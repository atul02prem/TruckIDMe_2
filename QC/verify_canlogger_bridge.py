"""Verify that canloggerTime serves as a stable time bridge between SparkFun GPS
and CAN signals for every driver (except those in EXCLUDE_DRIVERS).

Two checks per driver:
  1. (gpsTime - canloggerTime) should be approximately constant
     (std << 1 second across the drive).
  2. Every CAN TimeXXX column's [min, max] range should sit within
     canloggerTime's [min, max] range (with a small tolerance) —
     confirming both clocks share a reference frame.

Run from project root:
    python -m playground.verify_canlogger_bridge
"""

from itertools import count
import re
from pathlib import Path

import pandas as pd

from src.config import DATA_PROCESSED, EXCLUDE_DRIVERS, OUT_REPORTS


_DRIVER_ID_RE  = re.compile(r"^G(\d+)_Subject(\d+)$")
_CAN_TIME_RE   = re.compile(r"^Time(\d+)")
RANGE_TOL_S    = 8.0  # tolerance for CAN-range-within-canloggerTime check


def filename_to_driver_id(stem: str) -> str:
    """Convert a CSV filename stem like 'G1_Subject4' to canonical 'G1S04'.

    Args:
        stem: CSV filename without the .csv extension.

    Returns:
        Driver ID in 'G{group}S{nn}' format (zero-padded subject number).
    """
    m = _DRIVER_ID_RE.match(stem)
    if not m:
        raise ValueError(f"Cannot parse driver ID from {stem!r}")
    return f"G{m.group(1)}S{int(m.group(2)):02d}"


def check_offset_stability(df: pd.DataFrame) -> dict:
    """Summarize (gpsTime - canloggerTime) across a driver's GPS samples.

    Args:
        df: driver DataFrame (must contain 'gpsTime' and 'canloggerTime').

    Returns:
        Dict with n_gps_rows, mean_offset_s, std_offset_s, max_deviation_s.
    """
    pair = df[["gpsTime", "canloggerTime"]].dropna()
    #print(pair.shape) #same no of rows (gpsTime, canloggerTime) after dropping na
    offset = pair["gpsTime"] - pair["canloggerTime"]
    return {
        "n_gps_rows":      int(len(pair)),
        "mean_offset_s":   float(offset.mean()),
        "std_offset_s":    float(offset.std()),
        "max_deviation_s": float((offset - offset.mean()).abs().max()),
    }


def check_can_in_canlogger_range(df: pd.DataFrame, tol_s: float = RANGE_TOL_S) -> dict:
    """Verify every CAN TimeXXX column's range fits inside canloggerTime's range.

    Args:
        df: driver DataFrame (must contain 'canloggerTime' and CAN TimeXXX columns).
        tol_s: tolerance in seconds for the range comparison.

    Returns:
        Dict with n_can_time_cols, n_out_of_range, out_of_range_cols.
    """
    cl = df["canloggerTime"].dropna()
    cl_min, cl_max = cl.min(), cl.max()

    can_time_cols = [c for c in df.columns if _CAN_TIME_RE.match(c)]
    out_of_range = []
    for c in can_time_cols:
        s = df[c].dropna()
        if len(s) == 0:
            continue
        if s.min() < cl_min - tol_s or s.max() > cl_max + tol_s:
            out_of_range.append(c)
    return {
        "n_can_time_cols":   len(can_time_cols),
        "n_out_of_range":    len(out_of_range),
        "out_of_range_cols": out_of_range,
    }


def verify_all_drivers(data_dir: Path, exclude_drivers: set[str]) -> pd.DataFrame:
    """Run both checks for every driver CSV in data_dir, except excluded ones.

    Args:
        data_dir: directory of driver CSVs.
        exclude_drivers: set of canonical driver IDs to skip (e.g. {'G1S04'}).

    Returns:
        DataFrame indexed by driver ID with offset and range statistics per driver.
    """
    rows = []
    for csv_file in sorted(data_dir.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in exclude_drivers:
            print(f"  skipping {driver_id} (excluded)")
            continue
        df = pd.read_csv(csv_file, low_memory=False)
        offset_stats = check_offset_stability(df)
        range_stats = check_can_in_canlogger_range(df)
        rows.append({"driver": driver_id, **offset_stats, **range_stats})
        print(
            f"  {driver_id}: "
            f"offset_std={offset_stats['std_offset_s']:.4f}s, "
            f"can_cols_out_of_range={range_stats['n_out_of_range']}"
        )
    return pd.DataFrame(rows).set_index("driver")


if __name__ == "__main__":
    print(f"Verifying canloggerTime bridge across drivers in {DATA_PROCESSED}")
    print(f"Excluded drivers: {EXCLUDE_DRIVERS}")
    print()

    report = verify_all_drivers(DATA_PROCESSED, EXCLUDE_DRIVERS)
    print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(
        report[["n_gps_rows", "mean_offset_s", "std_offset_s",
                "max_deviation_s", "n_can_time_cols", "n_out_of_range"]]
        .to_string()
    )
    print()

    # Flag any driver where the offset isn't approximately constant.
    bad_offset = report[report["std_offset_s"] >= 1.0]
    print("Drivers with offset std >= 1.0s (canloggerTime drifts mid-drive):")
    if len(bad_offset) == 0:
        print("  None — canloggerTime is stable for all drivers.")
    else:
        print(bad_offset[["mean_offset_s", "std_offset_s", "max_deviation_s"]].to_string())
    print()

    # Flag any driver where any CAN Time column falls outside canloggerTime range.
    bad_range = report[report["n_out_of_range"] > 0]
    print(f"Drivers with CAN Time columns outside canloggerTime range (tol = {RANGE_TOL_S}s):")
    if len(bad_range) == 0:
        print("  None — all CAN time columns are within canloggerTime range.")
    else:
        for driver in bad_range.index:
            cols = bad_range.loc[driver, "out_of_range_cols"]
            print(f"  {driver}: {len(cols)} cols, first few: {cols[:3]}")

    report_file = Path(OUT_REPORTS)/"canlogger_bridge_report.md"
    with report_file.open("w") as f:
        f.write("# Canlogger Bridge Verification Report\n\n")
        f.write(f"Excluded drivers: {EXCLUDE_DRIVERS}\n\n")
        f.write(report.to_string())
