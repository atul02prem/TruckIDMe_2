"""Build the per-(driver, sector) feature matrix for downstream ML.

For each driver's master timeline (data/interim_data/{driver}.csv), group
rows by sector_id and compute Stage-2 aggregates per CAN signal. Combines
all 46 usable drivers into one feature matrix.

Per-signal aggregates (Stage 2 — across the master ticks within each sector):
  - Distribution: mean, median, std_dev, min, max, p10, p90
  - Dynamics: dmean, dstd  (mean/std of |first difference| — "jerkiness")

GPS columns are deliberately excluded — they encode route geometry, not
driver behavior. Only CAN signals contribute features. See
feedback_downsample_strategy.md in auto-memory for the rationale.

Output: data/processed_data/feature_matrix.csv
Schema:
  - driver       (e.g. G1S01)
  - group        (G1 / G2 / G3)
  - sector_id    (int)
  - n_rows       (number of master-timeline ticks in this driver × sector)
  - 9 per CAN signal: mean_, median_, std_, min_, max_, p10_, p90_, dmean_, dstd_

Run from project root:
    python -m src.features.build_feature_matrix
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATA_INTERIM, DATA_PROCESSED, EXCLUDE_DRIVERS, EXCLUDE_SPNS


_DRIVER_ID_RE  = re.compile(r"^G(\d+)_Subject(\d+)$")
_CAN_SIGNAL_RE = re.compile(r"^(\d+)\s")

# Non-CAN columns to skip when selecting signals to aggregate.
GPS_AND_META_COLS = {
    "canloggerTime", "gpsTime", "timestampsLocation",
    "longitude", "latitude",
    "timestampHeading", "gpsSpeed", "headingDegree",
    "timestampSat", "numSats",
    "sector_id", "sector_dist_m",
}


def filename_to_driver_id(stem: str) -> str:
    """Convert 'G1_Subject4' to canonical 'G1S04'."""
    m = _DRIVER_ID_RE.match(stem)
    if not m:
        raise ValueError(f"Cannot parse driver ID from {stem!r}")
    return f"G{m.group(1)}S{int(m.group(2)):02d}"


def driver_id_to_group(driver_id: str) -> str:
    """Extract group label ('G1', 'G2', 'G3') from a canonical driver ID."""
    return driver_id[:2]


def get_can_signal_cols(columns: list[str]) -> list[str]:
    """Return CAN signal columns to aggregate (not GPS, not metadata, not excluded).

    Honours EXCLUDE_SPNS at the feature stage so the Stage-1 audit loop can drop
    a leaking signal by editing config alone — no master-timeline rebuild needed.
    The master timeline keeps the full signal set; excluded SPNs are simply not
    turned into features.

    Args:
        columns: full column list of a master-timeline DataFrame.

    Returns:
        List of CAN signal column names in original order, excluding EXCLUDE_SPNS.
    """
    cols = []
    for c in columns:
        if c in GPS_AND_META_COLS:
            continue
        m = _CAN_SIGNAL_RE.match(c)
        if m is None or int(m.group(1)) in EXCLUDE_SPNS:
            continue
        cols.append(c)
    return cols


def aggregate_signals(group: pd.DataFrame, signal_cols: list[str]) -> dict:
    """Compute the 9 Stage-2 aggregates per signal over one time-ordered group.

    The group rows must be time-ordered (master timeline is sorted by
    canloggerTime; pandas groupby is stable), so np.diff gives the true temporal
    first difference. dmean/dstd = mean/std of |Δ| ("jerkiness" — smoothness of
    control; most meaningful for fast signals, artifactual for slow ffilled ones).

    Args:
        group: rows of a master timeline belonging to one sector or window.
        signal_cols: CAN signal columns to aggregate.

    Returns:
        Dict of {aggregate}_{signal} -> float, for aggregates
        mean, median, std, min, max, p10, p90, dmean, dstd.
    """
    out: dict = {}
    for sig in signal_cols:
        vals = group[sig].dropna().to_numpy()
        if vals.size == 0:
            for agg in ("mean", "median", "std", "min", "max", "p10", "p90", "dmean", "dstd"):
                out[f"{agg}_{sig}"] = np.nan
            continue
        out[f"mean_{sig}"]   = float(vals.mean())
        out[f"median_{sig}"] = float(np.median(vals))
        out[f"std_{sig}"]    = float(vals.std(ddof=1)) if vals.size > 1 else 0.0
        out[f"min_{sig}"]    = float(vals.min())
        out[f"max_{sig}"]    = float(vals.max())
        out[f"p10_{sig}"]    = float(np.percentile(vals, 10))
        out[f"p90_{sig}"]    = float(np.percentile(vals, 90))
        if vals.size > 1:
            d = np.abs(np.diff(vals))
            out[f"dmean_{sig}"] = float(d.mean())
            out[f"dstd_{sig}"]  = float(d.std(ddof=1)) if d.size > 1 else 0.0
        else:
            out[f"dmean_{sig}"] = 0.0
            out[f"dstd_{sig}"]  = 0.0
    return out


def check_channel_uniformity(driver_id: str, cols: list[str],
                             reference: list[str] | None) -> list[str]:
    """Fail loudly if a driver's CAN channel columns differ from the reference.

    Guards every place that stacks drivers together: non-uniform schemas must be
    caught here rather than silently producing misaligned/NaN features.

    Args:
        driver_id: current driver (for the error message).
        cols: this driver's CAN signal columns.
        reference: the first driver's columns, or None to seed the reference.

    Returns:
        The reference list (cols itself on the first call).
    """
    if reference is None:
        return cols
    if cols != reference:
        missing = sorted(set(reference) - set(cols))
        extra   = sorted(set(cols) - set(reference))
        raise ValueError(
            f"Column schema mismatch for {driver_id}: missing={missing}, "
            f"extra={extra}. Master-timeline schema must be uniform across "
            "drivers — rebuild build_master_timeline."
        )
    return reference


def compute_sector_features_for_driver(
    master_df: pd.DataFrame,
    signal_cols: list[str],
) -> pd.DataFrame:
    """Aggregate one driver's master timeline into per-sector feature rows.

    Args:
        master_df: a driver's full master-timeline DataFrame (must contain
                   'sector_id' column).
        signal_cols: CAN signal columns to aggregate.

    Returns:
        DataFrame with one row per sector visited; columns are
        [sector_id, n_rows, median_<sig>, std_<sig>, min_<sig>, max_<sig>, ...].
    """
    rows = []
    for sector_id, group in master_df.groupby("sector_id", sort=True):
        row: dict = {"sector_id": int(sector_id), "n_rows": len(group)}
        row.update(aggregate_signals(group, signal_cols))
        rows.append(row)
    return pd.DataFrame(rows)


def build_feature_matrix(interim_dir: Path, exclude_drivers: set[str]) -> pd.DataFrame:
    """Build the full multi-driver feature matrix.

    Args:
        interim_dir:      directory of per-driver master timeline CSVs.
        exclude_drivers:  canonical driver IDs to skip.

    Returns:
        DataFrame with one row per (driver, sector_id) tuple.
    """
    all_rows = []
    ref_cols = None
    for csv_file in sorted(interim_dir.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in exclude_drivers:
            continue

        master_df = pd.read_csv(csv_file)
        signal_cols = get_can_signal_cols(master_df.columns.tolist())
        ref_cols = check_channel_uniformity(driver_id, signal_cols, ref_cols)

        sector_df = compute_sector_features_for_driver(master_df, signal_cols)
        sector_df.insert(0, "driver", driver_id)
        sector_df.insert(1, "group",  driver_id_to_group(driver_id))
        all_rows.append(sector_df)

        print(
            f"  {driver_id}: {len(sector_df):>2} sectors x "
            f"{sector_df.shape[1]:>4} cols  "
            f"(n_rows median={sector_df['n_rows'].median():.0f})"
        )

    return pd.concat(all_rows, ignore_index=True)


if __name__ == "__main__":
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    feature_matrix = build_feature_matrix(DATA_INTERIM, EXCLUDE_DRIVERS)

    out_path = DATA_PROCESSED / "feature_matrix.csv"
    feature_matrix.to_csv(out_path, index=False)

    print()
    print(f"Feature matrix written to {out_path}")
    print(f"Shape: {feature_matrix.shape}")
    print(f"Drivers: {feature_matrix['driver'].nunique()}")
    print(f"Rows per group:")
    print(feature_matrix.groupby('group').size().to_string())
    print(f"Sectors per driver (median): "
          f"{feature_matrix.groupby('driver').size().median():.0f}")
    print(f"Null fraction: "
          f"{feature_matrix.isna().sum().sum() / feature_matrix.size * 100:.2f}%")
