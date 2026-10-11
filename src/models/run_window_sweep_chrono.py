"""Windowed driver-ID sweep with a chronological window-split — directly
comparable to the per-tick baseline (same 62 channels, same 70/gap/25 idea).

Per driver: build NON-OVERLAPPING windows of each duration in DURATIONS_S,
ordered in time, then split BY WINDOW COUNT:
    train = first 70% of windows,
    gap   = next  5% of windows (DROPPED buffer),
    test  = last  25% of windows.
Each window is aggregated to the 9 Stage-2 stats per CAN channel. No overlap,
no stride. Train and test cover different route positions and never straddle
the gap. One split, one number per duration.

Outputs:
  - outputs/reports/window_sweep_chrono.md
  - outputs/figures/window_sweep_chrono_curve.png

Run from project root:
    python -m src.models.run_window_sweep_chrono
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, top_k_accuracy_score

from src.features.build_feature_matrix import (
    aggregate_signals,
    check_channel_uniformity,
    filename_to_driver_id,
    get_can_signal_cols,
)
from src.config import DATA_INTERIM, EXCLUDE_DRIVERS, OUT_FIGURES, OUT_REPORTS

MASTER_HZ    = 10.0
TRAIN_END    = 0.70    # first 70% of a driver's windows -> train
TEST_START   = 0.75    # last 25% -> test; the 70-75% window band is the dropped gap
MIN_COVERAGE = 0.9     # keep a window only if it has >= this fraction of expected ticks
DURATIONS_S  = [30, 60, 90, 120]
SEED         = 42
N_ESTIMATORS = 300
TOP_KS       = (1, 2, 5)


def ordered_windows(master_df: pd.DataFrame, signal_cols: list[str], window_s: float):
    """Return time-ordered list of per-window feature dicts (full windows only)."""
    t = master_df["canloggerTime"].to_numpy()
    win_id = np.floor((t - t[0]) / window_s).astype(int)
    md = master_df.assign(_w=win_id)
    expected = window_s * MASTER_HZ
    feats = []
    for _, g in md.groupby("_w", sort=True):
        if len(g) < MIN_COVERAGE * expected:
            continue  # partial window (usually the last one)
        feats.append(aggregate_signals(g, signal_cols))
    return feats


def build_split(window_s: float):
    """Stacked train/test feature tables across drivers, split by window count."""
    xtr, xte, ytr, yte = [], [], [], []
    ref_cols = None
    for csv_file in sorted(DATA_INTERIM.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in EXCLUDE_DRIVERS:
            continue
        df = pd.read_csv(csv_file).sort_values("canloggerTime").reset_index(drop=True)
        signal_cols = get_can_signal_cols(df.columns.tolist())
        ref_cols = check_channel_uniformity(driver_id, signal_cols, ref_cols)
        wins = ordered_windows(df, signal_cols, window_s)
        n = len(wins)
        train_end  = int(TRAIN_END * n)
        test_start = int(TEST_START * n)
        for w in wins[:train_end]:
            xtr.append(w); ytr.append(driver_id)
        for w in wins[test_start:]:
            xte.append(w); yte.append(driver_id)
    X_tr = pd.DataFrame(xtr)
    X_te = pd.DataFrame(xte)[X_tr.columns]
    return X_tr.to_numpy(float), np.array(ytr), X_te.to_numpy(float), np.array(yte)


def main() -> None:
    print(f"Windowed chronological sweep (train {TRAIN_END:.0%} / gap "
          f"{TEST_START-TRAIN_END:.0%} / test {1-TEST_START:.0%} of windows)")
    results = []
    for win_s in DURATIONS_S:
        X_tr, y_tr, X_te, y_te = build_split(win_s)
        imp = SimpleImputer(strategy="median")
        X_tr = imp.fit_transform(X_tr)
        X_te = imp.transform(X_te)
        clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=SEED, n_jobs=-1)
        clf.fit(X_tr, y_tr)
        proba = clf.predict_proba(X_te)
        pred = clf.classes_[proba.argmax(axis=1)]
        top1 = accuracy_score(y_te, pred)
        topk = {k: top_k_accuracy_score(y_te, proba, k=k, labels=clf.classes_) for k in TOP_KS}
        n_feat = X_tr.shape[1]
        results.append({"win": win_s, "n_tr": len(X_tr), "n_te": len(X_te),
                        "n_feat": n_feat, "top1": top1,
                        **{f"top{k}": topk[k] for k in TOP_KS}})
        print(f"  {win_s:>4}s: train={len(X_tr):,} test={len(X_te):,} feat={n_feat}  "
              f"top1={top1:.4f} top2={topk[2]:.4f} top5={topk[5]:.4f}")

    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TruckIDMe — Windowed Driver-ID (chronological window-split)",
        "",
        "Non-overlapping windows; per-driver split by window count "
        "(train first 70%, 5% gap dropped, test last 25%) — same protocol as the "
        "per-tick baseline, directly comparable. Random baseline = 2.2% (1/46).",
        "",
        "| Window (s) | Top-1 | Top-2 | Top-5 | Features | Train win | Test win |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(f"| {r['win']} | {r['top1']*100:.1f}% | {r['top2']*100:.1f}% | "
                     f"{r['top5']*100:.1f}% | {r['n_feat']} | {r['n_tr']} | {r['n_te']} |")
    lines += ["",
              "## Comparison to per-tick baseline (same split, same 62 channels)",
              "Per-tick (one 100ms snapshot): top-1 16.6% / top-2 26.5% / top-5 44.2%.",
              "The lift to windowed = value of temporal aggregation (the 9 per-window",
              "stats: mean/median/std/min/max/p10/p90/jerk-mean/jerk-std), measured",
              "under an identical chronological split."]
    (OUT_REPORTS / "window_sweep_chrono.md").write_text("\n".join(lines) + "\n")

    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    xs = [r["win"] for r in results]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(xs, [r["top1"]*100 for r in results], "o-", label="top-1")
    ax.plot(xs, [r["top2"]*100 for r in results], "s-", label="top-2")
    ax.plot(xs, [r["top5"]*100 for r in results], "^-", label="top-5")
    ax.axhline(16.6, color="gray", ls=":", label="per-tick top-1 (16.6%)")
    ax.axhline(1 / 46 * 100, color="k", ls="--", alpha=0.5, label="random")
    ax.set_xlabel("Window duration (s)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Windowed driver-ID vs duration (chronological split, 46 drivers)")
    ax.grid(True, alpha=0.3); ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIGURES / "window_sweep_chrono_curve.png", dpi=150)
    plt.close(fig)
    print(f"\nReport: {OUT_REPORTS / 'window_sweep_chrono.md'}")
    print(f"Curve:  {OUT_FIGURES / 'window_sweep_chrono_curve.png'}")


if __name__ == "__main__":
    main()
