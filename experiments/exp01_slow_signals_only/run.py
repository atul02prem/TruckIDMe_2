"""exp01 — Driver ID from natively-slow signals only (native rate, NO resampling).

Built from scratch from data/processed_data/ (native-rate CAN + TimeXXX). Uses
only the CAN signals whose native rate <= SLOW_MAX_HZ (5 Hz) — mostly brake /
boost / fuel-rail / oil pressures + turbo speed. These need no downsampling, so
the multi-rate / anti-aliasing question does not arise.

NATIVE windowing (Option B): windows are defined on canloggerTime; feach signal's
raw samples are bucketed into windows by that signal's own TimeXXX (same CAN-logger
clock family). No ffill, no 10 Hz grid — so all 9 aggregates, jerk included, are
computed on the genuine native samples.

Split: per-driver chronological — train first 70% of windows, 5% gap dropped,
test last 25%. RandomForest, top-1/2/5.

Run from repo root:
    python -m experiments.exp01_slow_signals_only.run
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, top_k_accuracy_score

from src.features.build_feature_matrix import (
    check_channel_uniformity,
    filename_to_driver_id,
)
from src.qc.dataqc import null_report
from src.config import DATA_PROCESSED, EXCLUDE_DRIVERS

QC_DIR = Path(__file__).resolve().parent / "qc"

SLOW_MAX_HZ  = 5.0
TRAIN_END    = 0.70
TEST_START   = 0.75
DURATIONS_S  = [30, 60, 90, 120]
MIN_SAMPLES  = 3            # a window needs >= this many native samples of a signal
SEED         = 42
N_ESTIMATORS = 300
TOP_KS       = (1, 2, 5)
RESULTS_PATH = Path(__file__).resolve().parent / "results.md"

_SIG_RE = re.compile(r"^(\d+)\s")
_AGGS   = ("mean", "median", "std", "min", "max", "p10", "p90", "dmean", "dstd")


def slow_signal_pairs(processed_csv) -> dict[str, str]:
    """{signal_col: time_col} for CAN signals with native rate <= SLOW_MAX_HZ."""
    df = pd.read_csv(processed_csv, nrows=300000)
    pairs = {}
    for c in df.columns:
        m = _SIG_RE.match(c)
        if not m:
            continue
        tcol = f"Time{m.group(1)}"
        if tcol not in df.columns:
            continue
        t = df[tcol].dropna().sort_values().to_numpy()
        if len(t) < 2:
            continue
        if 1.0 / np.median(np.diff(t)) <= SLOW_MAX_HZ:
            pairs[c] = tcol
    return pairs


def agg9(vals: np.ndarray) -> list[float]:
    """The 9 aggregates for one signal's native samples in one window (time-ordered)."""
    if vals.size == 0:
        return [np.nan] * len(_AGGS)
    out = [
        float(vals.mean()), float(np.median(vals)),
        float(vals.std(ddof=1)) if vals.size > 1 else 0.0,
        float(vals.min()), float(vals.max()),
        float(np.percentile(vals, 10)), float(np.percentile(vals, 90)),
    ]
    if vals.size > 1:
        d = np.abs(np.diff(vals))
        out += [float(d.mean()), float(d.std(ddof=1)) if d.size > 1 else 0.0]
    else:
        out += [0.0, 0.0]
    return out


def native_windows(processed_csv, pairs: dict[str, str], window_s: float):
    """Ordered list of per-window feature dicts, built from native samples."""
    cols = ["canloggerTime"] + [c for p in pairs.items() for c in p]
    df = pd.read_csv(processed_csv, usecols=list(dict.fromkeys(cols)))
    ct = df["canloggerTime"].dropna()
    t0 = ct.min()
    n_full = int((ct.max() - t0) // window_s)   # drop the trailing partial window

    # Per signal: window index per native sample, then group-aggregate.
    per_sig_bins = {}
    for sig, tcol in pairs.items():
        s = df[[tcol, sig]].dropna()
        s = s.sort_values(tcol)
        widx = np.floor((s[tcol].to_numpy() - t0) / window_s).astype(int)
        per_sig_bins[sig] = (widx, s[sig].to_numpy())

    rows = []
    for w in range(n_full):
        row = {}
        for sig, (widx, vals) in per_sig_bins.items():
            wv = vals[widx == w]
            wv = wv if wv.size >= MIN_SAMPLES else np.empty(0)
            for name, val in zip(_AGGS, agg9(wv)):
                row[f"{name}_{sig}"] = val
        rows.append(row)
    return rows


def build_split(pairs, window_s):
    xtr, xte, ytr, yte = [], [], [], []
    ref = None
    for csv_file in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in EXCLUDE_DRIVERS:
            continue
        ref = check_channel_uniformity(driver_id, sorted(pairs), ref)
        wins = native_windows(csv_file, pairs, window_s)
        n = len(wins)
        for r in wins[:int(TRAIN_END * n)]:
            xtr.append(r); ytr.append(driver_id)
        for r in wins[int(TEST_START * n):]:
            xte.append(r); yte.append(driver_id)
    X_tr = pd.DataFrame(xtr)
    X_te = pd.DataFrame(xte)[X_tr.columns]
    # Data-QC: null % per feature at this stage (windowed native features).
    null_report(X_tr, f"features_{int(window_s)}s_train", QC_DIR)
    return X_tr.to_numpy(float), np.array(ytr), X_te.to_numpy(float), np.array(yte)


def main() -> None:
    pairs = slow_signal_pairs(DATA_PROCESSED / "G1_Subject1.csv")
    print(f"Slow signals (<= {SLOW_MAX_HZ} Hz), built from native samples: {len(pairs)}")
    for c in pairs:
        print(f"    {c}")
    print()

    results = []
    for win_s in DURATIONS_S:
        X_tr, y_tr, X_te, y_te = build_split(pairs, win_s)
        imp = SimpleImputer(strategy="median")
        X_tr = imp.fit_transform(X_tr); X_te = imp.transform(X_te)
        clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=SEED, n_jobs=-1)
        clf.fit(X_tr, y_tr)
        proba = clf.predict_proba(X_te)
        pred = clf.classes_[proba.argmax(axis=1)]
        top1 = accuracy_score(y_te, pred)
        topk = {k: top_k_accuracy_score(y_te, proba, k=k, labels=clf.classes_) for k in TOP_KS}
        results.append({"win": win_s, "n_tr": len(X_tr), "n_te": len(X_te),
                        "n_feat": X_tr.shape[1], "top1": top1,
                        **{f"top{k}": topk[k] for k in TOP_KS}})
        print(f"  {win_s:>4}s: train={len(X_tr):,} test={len(X_te):,} feat={X_tr.shape[1]}  "
              f"top1={top1:.4f} top2={topk[2]:.4f} top5={topk[5]:.4f}")

    lines = [
        "# exp01 results — driver ID from native slow signals (<= 5 Hz, no resampling)",
        "",
        f"{len(pairs)} signals, native samples, {', '.join(_AGGS)} per signal per window.",
        "Per-driver chronological split (train 70% / gap 5% / test 25%). "
        "Random baseline = 2.2% (1/46).",
        "",
        "| Window (s) | Top-1 | Top-2 | Top-5 | Features | Train win | Test win |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(f"| {r['win']} | {r['top1']*100:.1f}% | {r['top2']*100:.1f}% | "
                     f"{r['top5']*100:.1f}% | {r['n_feat']} | {r['n_tr']} | {r['n_te']} |")
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nResults: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
