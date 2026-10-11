"""Build the 10 Hz master timeline for every usable driver.

For each driver:
  1. Load GPS + sector_id from data/interim_data/{driver}.csv
     (the output of assign_sectors.py).
  2. Load CAN signals from data/processed_data/{driver}.csv.
  3. For each CAN signal, mean-aggregate raw samples per 100 ms window
     centered on each canloggerTime tick. Forward-fill any tick that
     had no raw sample in its window (i.e. slow signals).
  4. Concatenate: existing interim columns + aligned CAN columns.
  5. Overwrite data/interim_data/{driver}.csv with the merged result.

The output is a dense per-driver DataFrame indexed implicitly by
canloggerTime with:
    - 10 SparkFun GPS columns (canloggerTime, gpsTime, lat, lon, gpsSpeed, ...)
    - 2 sectorization columns (sector_id, sector_dist_m)
    - ~XX CAN signal columns aligned to canloggerTime

Run from project root:
    python -m src.data.build_master_timeline
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATA_INTERIM, DATA_PROCESSED, EXCLUDE_DRIVERS


_DRIVER_ID_RE   = re.compile(r"^G(\d+)_Subject(\d+)$")
_CAN_SIGNAL_RE  = re.compile(r"^(\d+)\s")
WINDOW_HALF_S   = 0.05  # 100 ms full window centered on each canloggerTime tick

# ── EXPERIMENT: extra within-100ms aggregates (Stage-1) ───────────────────────
# Set to () for the baseline (mean only). Anything listed here is computed
# *inside* each 100 ms window and added as an extra 10 Hz channel named
# "<signal>__w<agg>" (digit-prefixed so downstream signal-detection still works).
#
# Only applied to signals with at least MIN_SAMPLES_PER_WINDOW raw samples per
# window — for slower signals std would be 0 and min/max/median would duplicate
# the mean, flooding the model with degenerate features and confounding the test.
WITHIN_WINDOW_AGGS      = ("median", "std", "min", "max")
MIN_SAMPLES_PER_WINDOW  = 3


def filename_to_driver_id(stem: str) -> str:
    """Convert a CSV stem like 'G1_Subject4' to canonical 'G1S04'."""
    m = _DRIVER_ID_RE.match(stem)
    if not m:
        raise ValueError(f"Cannot parse driver ID from {stem!r}")
    return f"G{m.group(1)}S{int(m.group(2)):02d}"


def find_can_signal_pairs(columns: list[str]) -> dict[str, str]:
    """Map each CAN signal column to its TimeXXX partner.

    Args:
        columns: full column list of a processed driver CSV.

    Returns:
        Dict mapping signal column name (e.g. '190 Engine Speed') to its
        time column name (e.g. 'Time190'). Signals with no matching time
        column are skipped.
    """
    cols_set = set(columns)
    pairs: dict[str, str] = {}
    for col in columns:
        m = _CAN_SIGNAL_RE.match(col)
        if m:
            time_col = f"Time{m.group(1)}"
            if time_col in cols_set:
                pairs[col] = time_col
    return pairs


def align_signal_to_master(
    raw_times: np.ndarray,
    raw_values: np.ndarray,
    master_times: np.ndarray,
    window_half_s: float = WINDOW_HALF_S,
) -> np.ndarray:
    """Mean-aggregate raw signal samples per 100 ms window centered on each master tick.

    Args:
        raw_times:    TimeXXX column for a single signal (epoch seconds);
                      may contain NaN.
        raw_values:   the signal's value column, aligned with raw_times;
                      may contain NaN.
        master_times: canloggerTime values defining the master grid,
                      sorted ascending.
        window_half_s: half-width of each averaging window in seconds.

    Returns:
        Array of length len(master_times). Each entry is the mean of
        raw_values whose raw_times fall in
            [master_times[i] - window_half_s, master_times[i] + window_half_s].
        Entries with no raw sample in the window are NaN (caller forward-fills).
    """
    valid = ~(np.isnan(raw_times) | np.isnan(raw_values))
    rt = raw_times[valid]
    rv = raw_values[valid].astype(float)

    if len(rt) == 0:
        return np.full(len(master_times), np.nan)

    order = np.argsort(rt)
    rt = rt[order]
    rv = rv[order]

    left  = np.searchsorted(rt, master_times - window_half_s, side="left")
    right = np.searchsorted(rt, master_times + window_half_s, side="right")

    cumsum = np.concatenate([[0.0], np.cumsum(rv)])
    counts = right - left
    sums   = cumsum[right] - cumsum[left]

    return np.where(counts > 0, sums / np.maximum(counts, 1), np.nan)


def align_signal_multi_agg(
    raw_times: np.ndarray,
    raw_values: np.ndarray,
    master_times: np.ndarray,
    aggs: tuple[str, ...],
    window_half_s: float = WINDOW_HALF_S,
) -> tuple[dict[str, np.ndarray], float]:
    """Compute several within-window aggregates per master tick in one pass.

    Assigns every raw sample to the 100 ms window it falls in, then groups.
    Windows with no sample yield NaN (caller forward-fills), matching the
    mean-only path.

    Args:
        raw_times:    TimeXXX column for one signal (epoch seconds), may be NaN.
        raw_values:   the signal's values, aligned with raw_times, may be NaN.
        master_times: canloggerTime grid, sorted ascending.
        aggs:         extra aggregates beyond 'mean' (e.g. median/std/min/max).
        window_half_s: half-width of each window.

    Returns:
        (results, samples_per_window) where results maps aggregate name ->
        array of len(master_times), and samples_per_window is the median number
        of raw samples landing in a non-empty window (used to decide whether the
        extra aggregates are meaningful for this signal).
    """
    names = ("mean",) + tuple(aggs)
    n = len(master_times)
    out = {a: np.full(n, np.nan) for a in names}

    valid = ~(np.isnan(raw_times) | np.isnan(raw_values))
    rt, rv = raw_times[valid], raw_values[valid].astype(float)
    if rt.size == 0:
        return out, 0.0

    order = np.argsort(rt)
    rt, rv = rt[order], rv[order]

    edges = np.concatenate([master_times - window_half_s,
                            [master_times[-1] + window_half_s]])
    idx = np.searchsorted(edges, rt, side="right") - 1
    keep = (idx >= 0) & (idx < n)
    idx, rvk = idx[keep], rv[keep]
    if idx.size == 0:
        return out, 0.0

    grouped = pd.Series(rvk).groupby(idx)
    # ddof=0 so a single-sample window gives std 0 rather than NaN.
    computed = {
        "mean":   grouped.mean(),
        "median": grouped.median(),
        "std":    grouped.std(ddof=0),
        "min":    grouped.min(),
        "max":    grouped.max(),
    }
    for a in names:
        vals = computed[a]
        out[a][vals.index.to_numpy()] = vals.to_numpy()

    samples_per_window = float(np.median(np.bincount(idx)[np.bincount(idx) > 0]))
    return out, samples_per_window


def determine_fast_signals(interim_csv: Path, processed_csv: Path) -> set[str]:
    """Signals with >= MIN_SAMPLES_PER_WINDOW raw samples per 100 ms window.

    Computed ONCE from a reference driver and reused for all drivers, so the set
    of within-window aggregate channels (and hence the column schema) is uniform
    across every output file. Deciding this per-driver lets borderline ~30 Hz
    signals flip in/out and produces mismatched schemas.

    Args:
        interim_csv:   reference driver's GPS+sector file (for the master grid).
        processed_csv: reference driver's processed CSV (CAN signals).

    Returns:
        Set of signal column names deemed "fast" on the reference driver.
    """
    master_times = pd.read_csv(interim_csv, usecols=["canloggerTime"])["canloggerTime"].values
    processed_df = pd.read_csv(processed_csv)
    fast = set()
    for signal_col, time_col in find_can_signal_pairs(processed_df.columns.tolist()).items():
        _, spw = align_signal_multi_agg(
            processed_df[time_col].values, processed_df[signal_col].values,
            master_times, WITHIN_WINDOW_AGGS,
        )
        if spw >= MIN_SAMPLES_PER_WINDOW:
            fast.add(signal_col)
    return fast


def build_master_timeline_for_driver(
    interim_csv: Path,
    processed_csv: Path,
    fast_signals: set[str],
) -> pd.DataFrame:
    """Combine GPS + sector + temporally aligned CAN signals into one DataFrame.

    Args:
        interim_csv:   path to the GPS+sector file from assign_sectors.py.
        processed_csv: path to the full processed CSV with CAN signals.
        fast_signals:  signal columns that get the within-window aggregate
                       channels — a fixed set (from determine_fast_signals) so
                       the schema is identical for every driver.

    Returns:
        DataFrame with the existing interim columns followed by every
        aligned CAN signal column, one row per canloggerTime tick.
    """
    interim_df   = pd.read_csv(interim_csv)
    processed_df = pd.read_csv(processed_csv)

    # Make this step idempotent: if interim_csv was already a master timeline
    # (i.e. has CAN signal columns from a previous run), drop them before
    # re-appending. Otherwise repeated runs duplicate columns.
    stale_can_cols = [c for c in interim_df.columns if _CAN_SIGNAL_RE.match(c)]
    if stale_can_cols:
        interim_df = interim_df.drop(columns=stale_can_cols)

    master_times = interim_df["canloggerTime"].values
    pairs = find_can_signal_pairs(processed_df.columns.tolist())

    aligned_cols: dict[str, np.ndarray] = {}
    for signal_col, time_col in pairs.items():
        # Mean channel always via the original path, so it is byte-identical to
        # the mean-only baseline and the A/B comparison stays clean.
        aligned = align_signal_to_master(
            processed_df[time_col].values,
            processed_df[signal_col].values,
            master_times,
        )
        aligned_cols[signal_col] = pd.Series(aligned).ffill().values

        if not WITHIN_WINDOW_AGGS or signal_col not in fast_signals:
            continue

        # Extra within-window channels for the fixed fast-signal set (uniform
        # schema across drivers).
        res, _ = align_signal_multi_agg(
            processed_df[time_col].values,
            processed_df[signal_col].values,
            master_times,
            WITHIN_WINDOW_AGGS,
        )
        for a in WITHIN_WINDOW_AGGS:
            aligned_cols[f"{signal_col}__w{a}"] = pd.Series(res[a]).ffill().values

    can_df = pd.DataFrame(aligned_cols)
    return pd.concat(
        [interim_df.reset_index(drop=True), can_df.reset_index(drop=True)],
        axis=1,
    )


if __name__ == "__main__":
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)

    # Decide the fast-signal set ONCE from the reference driver so every output
    # file has an identical column schema.
    REFERENCE = "G1_Subject1.csv"
    fast_signals = (
        determine_fast_signals(DATA_INTERIM / REFERENCE, DATA_PROCESSED / REFERENCE)
        if WITHIN_WINDOW_AGGS else set()
    )
    print(f"Fast signals (from {REFERENCE}, applied to all): {len(fast_signals)}")
    for s in sorted(fast_signals):
        print(f"    {s}")
    print()

    for csv_file in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in EXCLUDE_DRIVERS:
            print(f"  skipping {driver_id} (excluded)")
            continue

        interim_path = DATA_INTERIM / csv_file.name
        if not interim_path.exists():
            print(f"  {driver_id}: no interim file — run assign_sectors.py first")
            continue

        master_df = build_master_timeline_for_driver(interim_path, csv_file, fast_signals)
        master_df.to_csv(interim_path, index=False)

        n_can = sum(1 for c in master_df.columns if _CAN_SIGNAL_RE.match(c))
        n_extra_cols = sum(1 for c in master_df.columns if "__w" in c)
        n_fast = n_extra_cols // len(WITHIN_WINDOW_AGGS) if WITHIN_WINDOW_AGGS else 0
        n_rows, n_cols = master_df.shape
        null_pct = master_df.isna().sum().sum() / (n_rows * n_cols) * 100
        print(
            f"  {driver_id}: {n_rows:>6,} rows x {n_cols:>3} cols  "
            f"({n_can} CAN channels; {n_fast} fast signals got "
            f"{len(WITHIN_WINDOW_AGGS)} extra within-window aggs)  "
            f"null={null_pct:5.2f}%"
        )
