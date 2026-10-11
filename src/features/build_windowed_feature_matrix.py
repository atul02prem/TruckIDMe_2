"""Build a per-driver feature matrix over fixed-duration time windows.

Unlike build_feature_matrix (which aggregates per route sector), this slices
each driver's master timeline into non-overlapping fixed-length windows of
WINDOW_SECONDS and computes the same 9 aggregates per window. This is the unit
for the "identify a driver from N seconds of driving" feasibility study.

Only windows with at least MIN_COVERAGE of the expected ticks are kept, so every
example is genuinely ~WINDOW_SECONDS long (drops the partial final window).

Reuses the aggregate helper and signal selection from build_feature_matrix, so
EXCLUDE_SPNS and the 9-aggregate definition stay in one place.

Run from project root (default 120 s):
    python -m src.features.build_windowed_feature_matrix
"""

import numpy as np
import pandas as pd

from src.features.build_feature_matrix import (
    aggregate_signals,
    driver_id_to_group,
    filename_to_driver_id,
    get_can_signal_cols,
)
from src.config import DATA_INTERIM, DATA_PROCESSED, EXCLUDE_DRIVERS


MASTER_HZ         = 10.0   # master timeline tick rate
WINDOW_SECONDS    = 120    # default window length
MIN_COVERAGE      = 0.9    # keep a window only if it has ≥ this fraction of expected ticks


def compute_window_features_for_driver(
    master_df: pd.DataFrame,
    signal_cols: list[str],
    window_seconds: float,
) -> pd.DataFrame:
    """Aggregate one driver's master timeline into fixed-window feature rows.

    Args:
        master_df: a driver's master-timeline DataFrame (must contain
                   'canloggerTime'), time-ordered.
        signal_cols: CAN signal columns to aggregate.
        window_seconds: window length in seconds.

    Returns:
        DataFrame with one row per kept window:
            [window_id, n_rows, <9 aggregates per signal>].
    """
    t = master_df["canloggerTime"].to_numpy()
    t0 = t[0]
    window_id = np.floor((t - t0) / window_seconds).astype(int)
    master_df = master_df.assign(_window_id=window_id)

    expected_ticks = window_seconds * MASTER_HZ
    rows = []
    for wid, group in master_df.groupby("_window_id", sort=True):
        if len(group) < MIN_COVERAGE * expected_ticks:
            continue  # drop partial (usually final) window
        row: dict = {"window_id": int(wid), "n_rows": len(group)}
        row.update(aggregate_signals(group, signal_cols))
        rows.append(row)
    return pd.DataFrame(rows)


def build_windowed_feature_matrix(
    interim_dir,
    exclude_drivers: set[str],
    window_seconds: float,
) -> pd.DataFrame:
    """Build the multi-driver windowed feature matrix at one window length.

    Args:
        interim_dir: directory of per-driver master timeline CSVs.
        exclude_drivers: canonical driver IDs to skip.
        window_seconds: window length in seconds.

    Returns:
        DataFrame with one row per (driver, window) at this window length.
    """
    all_rows = []
    for csv_file in sorted(interim_dir.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in exclude_drivers:
            continue
        master_df = pd.read_csv(csv_file)
        signal_cols = get_can_signal_cols(master_df.columns.tolist())
        win_df = compute_window_features_for_driver(master_df, signal_cols, window_seconds)
        win_df.insert(0, "driver", driver_id)
        win_df.insert(1, "group",  driver_id_to_group(driver_id))
        all_rows.append(win_df)
    return pd.concat(all_rows, ignore_index=True)


if __name__ == "__main__":
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    matrix = build_windowed_feature_matrix(DATA_INTERIM, EXCLUDE_DRIVERS, WINDOW_SECONDS)

    out_path = DATA_PROCESSED / f"windowed_feature_matrix_{WINDOW_SECONDS}s.csv"
    matrix.to_csv(out_path, index=False)

    print(f"Window length: {WINDOW_SECONDS} s")
    print(f"Shape: {matrix.shape}")
    print(f"Total windows: {len(matrix)}")
    print(f"Windows per driver: "
          f"min={matrix.groupby('driver').size().min()}, "
          f"median={matrix.groupby('driver').size().median():.0f}, "
          f"max={matrix.groupby('driver').size().max()}")
    print(f"Rows per group: {matrix.groupby('group').size().to_dict()}")
    print(f"Written to {out_path}")
