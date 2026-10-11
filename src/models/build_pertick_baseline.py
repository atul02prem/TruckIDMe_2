"""Per-tick driver-ID baseline: classify a driver from ONE 100 ms snapshot.

Feeds the mean-downsampled 10 Hz master-timeline channels directly to the
classifier with no Stage-2 aggregation. Each row = one 10 Hz tick; features =
the CAN channel values at that instant; label = driver.

SPLIT — per-driver chronological with a gap (prevents temporal-adjacency leak):
For each driver's time-ordered ticks,
    train = first 70%   (early route),
    gap   = next  5%    (DISCARDED buffer, rows 70-75%),
    test  = last  25%   (late route, rows 75-100%).
Because train and test cover different parts of the route, the model cannot
memorise "this driver was here at this second" — it must fingerprint behaviour.
This is a deliberate LOWER BOUND: no temporal context, no variability, no
jerkiness — just instantaneous values. Compare against the windowed result.

Run from project root:
    python -m src.models.build_pertick_baseline
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, top_k_accuracy_score

from src.features.build_feature_matrix import (
    check_channel_uniformity,
    filename_to_driver_id,
    get_can_signal_cols,
)
from src.config import DATA_INTERIM, EXCLUDE_DRIVERS, OUT_REPORTS

TRAIN_END    = 0.70     # train = first 70% of each drive
TEST_START   = 0.75     # test  = last 25%; gap = 70-75% (5%), discarded
TICK_STRIDE  = 1       # keep every Nth tick (speed/memory; does not affect the split)
SEED         = 42
N_ESTIMATORS = 400
TOP_KS       = (1, 2, 5)


def load_pertick_split():
    """Load per-driver chronological train/test tick tables.

    Returns:
        (X_tr, y_tr, X_te, y_te, channel_cols): stacked train/test feature
        arrays with driver labels, and the CAN channel column names.
    """
    xtr, ytr, xte, yte = [], [], [], []
    channel_cols = None

    for csv_file in sorted(DATA_INTERIM.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in EXCLUDE_DRIVERS:
            continue

        df = pd.read_csv(csv_file).sort_values("canloggerTime").reset_index(drop=True)
        cols = get_can_signal_cols(df.columns.tolist())
        channel_cols = check_channel_uniformity(driver_id, cols, channel_cols)

        n = len(df)
        train_end  = int(TRAIN_END * n)
        test_start = int(TEST_START * n)

        train = df.iloc[:train_end:TICK_STRIDE]
        test  = df.iloc[test_start::TICK_STRIDE]

        xtr.append(train[channel_cols]); ytr.append(np.full(len(train), driver_id))
        xte.append(test[channel_cols]);  yte.append(np.full(len(test),  driver_id))
        print(f"  {driver_id}: {n:,} ticks -> train {len(train):,}, "
              f"test {len(test):,} (gap {test_start - train_end:,})")

    X_tr = pd.concat(xtr, ignore_index=True).to_numpy(dtype=float)
    X_te = pd.concat(xte, ignore_index=True).to_numpy(dtype=float)
    return X_tr, np.concatenate(ytr), X_te, np.concatenate(yte), channel_cols


def main() -> None:
    print(f"Per-tick baseline: train first {TRAIN_END:.0%}, gap "
          f"{TEST_START - TRAIN_END:.0%}, test last {1 - TEST_START:.0%} "
          f"(stride {TICK_STRIDE})")
    X_tr, y_tr, X_te, y_te, channels = load_pertick_split()
    drivers = sorted(set(y_tr))
    print(f"\nChannels: {len(channels)}   Drivers: {len(drivers)}")
    print(f"Train rows: {len(X_tr):,}   Test rows: {len(X_te):,}")

    imp = SimpleImputer(strategy="median")
    X_tr = imp.fit_transform(X_tr)
    X_te = imp.transform(X_te)

    clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=SEED, n_jobs=-1)
    clf.fit(X_tr, y_tr)
    proba = clf.predict_proba(X_te)
    pred = clf.classes_[proba.argmax(axis=1)]

    top1 = accuracy_score(y_te, pred)
    topk = {k: top_k_accuracy_score(y_te, proba, k=k, labels=clf.classes_) for k in TOP_KS}

    print()
    for k in TOP_KS:
        print(f"top-{k}: {topk[k]:.4f}")

    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TruckIDMe — Per-Tick Driver-ID Baseline (no Stage-2 aggregation)",
        "",
        "Each row = ONE 100 ms tick. Features = instantaneous CAN channel values.",
        "No temporal context — a deliberate LOWER BOUND vs the windowed result.",
        "",
        f"**Channels (features):** {len(channels)} (mean-downsampled 10 Hz)",
        f"**Split:** per-driver chronological — train first {TRAIN_END:.0%} of each "
        f"drive, {TEST_START - TRAIN_END:.0%} gap discarded, test last "
        f"{1 - TEST_START:.0%}. Train and test cover different route positions "
        "(prevents temporal-adjacency leakage; model must fingerprint behaviour, "
        "not memorise position).",
        f"**Train rows:** {len(X_tr):,}   **Test rows:** {len(X_te):,}   "
        f"(every {TICK_STRIDE}th tick)",
        f"**Drivers:** {len(drivers)}   **Random baseline:** {100/len(drivers):.1f}%",
        "",
        "| Metric | Accuracy |",
        "|---|---:|",
        *[f"| top-{k} | {topk[k]*100:.1f}% |" for k in TOP_KS],
        "",
        "## Interpretation",
        "Compare against the windowed result (9 aggregates over 120 s windows). The",
        "gap quantifies the value of temporal aggregation: how much driver identity",
        "lives in *how signals evolve over time* vs their instantaneous values.",
    ]
    out = OUT_REPORTS / "pertick_baseline_results.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"\nReport written to {out}")


if __name__ == "__main__":
    main()
