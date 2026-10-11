"""Exploration of TruckIDMe raw CSVs.

Two jobs:
  1. Report median sampling rate (Hz) for every timestamp column in a driver CSV.
  2. Filter each raw CSV down to CAN + SparkFun columns (drop VBOX + Empatica)
     and write the result to data/processed_data/.

Raw CSV column layout (per ORNL DriverID dataset):
    [CAN cols ... 84 Wheel-Based Vehicle Speed]
    [id.1, VBOX cols ...]
    [id.2, SparkFun cols ...]
    [id.3, Empatica cols ...]
"""

import re
from pathlib import Path

import pandas as pd

from src.config import DATA_RAW, DATA_PROCESSED, EXCLUDE_SPNS, OUT_REPORTS


CAN_END_COL = "84 Wheel-Based Vehicle Speed"

# SparkFun GPS columns (per the dataset data dictionary). Their position
# inside the CSV varies per driver (e.g. G3_Subject6 has SparkFun before
# VBOX, while everyone else has VBOX before SparkFun), so we select by
# name, not by id-marker position.
SPARKFUN_DATA_COLS = {
    "canloggerTime",       # CAN-logger-clock snapshot at each GPS sample
    "gpsTime",             # UTC from the GPS chip
    "timestampsLocation",  # Teensy timestamp paired with latitude / longitude
    "longitude",
    "latitude",
    "timestampHeading",    # Teensy timestamp paired with gpsSpeed / headingDegree
    "gpsSpeed",
    "headingDegree",
    "timestampSat",        # Teensy timestamp paired with numSats
    "numSats",
}

# Columns to drop from every processed CSV regardless of which block they sit in.
#   "id"                     — SQLite primary key from the CAN table, not data.
#   "190 Engine Speed CAN0"  — duplicate of "190 Engine Speed" recorded by the
#   "Time190 CAN0"             CANLogger3 at 100 Hz alongside the TruckCape's
#                              50 Hz capture. Only present for 37/46 usable
#                              drivers; dropped to give every driver an
#                              identical 184-column schema (the 50 Hz column
#                              already exists for all drivers).
DROP_COLS = {
    "id",
    "190 Engine Speed CAN0",
    "Time190 CAN0",
}

_SPN_FROM_TIME   = re.compile(r"^Time(\d+)") # internal use only; _ means "private"
_SPN_FROM_SIGNAL = re.compile(r"^(\d+)\s")


def get_spn_from_column(col: str) -> int | None:
    """Extract the J1939 SPN number from a CAN column name.

    Matches both signal columns (e.g. '171 Ambient Air Temperature') and
    paired time columns (e.g. 'Time171').

    Args:
        col: column name from a raw/processed driver CSV.

    Returns:
        The SPN integer if the column is a CAN signal or its time partner,
        otherwise None.
    """
    m = _SPN_FROM_TIME.match(col)
    if m:
        return int(m.group(1))
    m = _SPN_FROM_SIGNAL.match(col)
    if m:
        return int(m.group(1))
    return None


# def get_sampling_rate_hz(time_series: pd.Series) -> float:
#     """Compute the median sampling rate (Hz) from a timestamp column in seconds.

#     Args:
#         time_series: epoch-second timestamps, possibly with NaNs.

#     Returns:
#         Median frequency in Hz, or NaN if fewer than 2 valid samples.
#     """
#     t = time_series.dropna().sort_values()
#     if len(t) < 2:
#         return float("nan")
#     dt = t.diff().dropna()
#     median_dt = dt.median()
#     return 1.0 / median_dt if median_dt > 0 else float("nan")


def report_column_sampling_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Report median sampling rate (Hz) for every column in a driver CSV.

    Each data column inherits the rate of its paired timestamp column:
      - CAN signal column (e.g. '190 Engine Speed') -> paired TimeXXX column
      - SparkFun data column (latitude, longitude, etc.) -> appropriate timestamp column
      - Timestamp column itself -> its own rate

    Args:
        df: raw or filtered driver DataFrame.

    Returns:
        DataFrame with columns [column, paired_time_column, hz, n_samples],
        in original column order.
    """
    can_time_by_spn: dict[int, str] = {}
    for col in df.columns:
        m = _SPN_FROM_TIME.match(col)
        if m:
            can_time_by_spn[int(m.group(1))] = col

    sparkfun_pairings = {
        "latitude":      "timestampsLocation",
        "longitude":     "timestampsLocation",
        "gpsSpeed":      "timestampHeading",
        "headingDegree": "timestampHeading",
        "numSats":       "timestampSat",
    }

    rows = []
    for col in df.columns:
        is_time_col = (
            _SPN_FROM_TIME.match(col) is not None
            or col.startswith("timestamp")
            or col in {"gpsTime", "canloggerTime"}
        )
        if is_time_col:
            time_col = col
        elif (m := _SPN_FROM_SIGNAL.match(col)) is not None:
            time_col = can_time_by_spn.get(int(m.group(1)))
        elif col in sparkfun_pairings:
            time_col = sparkfun_pairings[col]
        else:
            time_col = None

        hz = get_sampling_rate_hz(df[time_col]) if time_col else float("nan")
        rows.append({
            "column": col,
            "paired_time_column": "(self)" if time_col == col else (time_col or ""),
            "hz": hz,
            "n_samples": int(df[col].notna().sum()),
        })
    return pd.DataFrame(rows)


# def save_sampling_rate_artifact(
#     report: pd.DataFrame,
#     out_path: Path,
#     source_name: str,
# ) -> None:
#     """Write a sampling rate report as a markdown table.

#     Args:
#         report: DataFrame returned by report_column_sampling_rates.
#         out_path: destination .md file path.
#         source_name: name of the source CSV (used in the report header).
#     """
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     lines = [
#         "# TruckIDMe — Column Sampling Rates",
#         "",
#         f"**Source file:** `{source_name}`",
#         f"**Total columns:** {len(report)}",
#         "",
#         "Each data column inherits its sampling rate from its paired timestamp",
#         "column. CAN signal columns pair with their `TimeXXX` partner; SparkFun",
#         "GPS data columns pair with the appropriate `timestamp*` column.",
#         "",
#         "| # | Column | Paired Time Column | Hz | Non-null samples |",
#         "|---|---|---|---:|---:|",
#     ]
#     for i, row in enumerate(report.itertuples(index=False), 1):
#         hz_str = f"{row.hz:.4f}" if pd.notna(row.hz) else "—"
#         lines.append(
#             f"| {i} | `{row.column}` | `{row.paired_time_column}` | {hz_str} | {row.n_samples:,} |"
#         )
#     out_path.write_text("\n".join(lines) + "\n")


def select_can_and_sparkfun_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Slice CAN signal columns and SparkFun GPS columns out of a raw driver CSV.

    Selection logic:
      - CAN block: every column from index 0 to CAN_END_COL (inclusive), minus
        the SQLite 'id' key and minus any signal whose SPN is in EXCLUDE_SPNS.
      - SparkFun block: the columns named in SPARKFUN_DATA_COLS, wherever they
        appear in the CSV. VBOX and Empatica columns are dropped by virtue of
        not being in this set.

    Args:
        df: raw merged DataFrame as loaded from data/raw_data/.

    Returns:
        DataFrame containing only CAN and SparkFun columns in their original
        CSV order within each block.
    """
    cols = list(df.columns)

    if CAN_END_COL not in cols:
        raise ValueError(f"CAN end marker {CAN_END_COL!r} not found in CSV")
    missing_sf = SPARKFUN_DATA_COLS - set(cols)
    if missing_sf:
        raise ValueError(f"SparkFun columns missing from CSV: {sorted(missing_sf)}")

    can_end_idx = cols.index(CAN_END_COL)
    can_cols = [
        c for c in cols[: can_end_idx + 1]
        if c not in DROP_COLS
        and get_spn_from_column(c) not in EXCLUDE_SPNS
    ]
    print(f"select_can_and_sparkfun_columns: {len(can_cols)} CAN columns selected")
    sparkfun_cols = [c for c in cols if c in SPARKFUN_DATA_COLS]
    print(f"select_can_and_sparkfun_columns: {len(sparkfun_cols)} SparkFun columns selected")
    return df[can_cols + sparkfun_cols].copy()


# def write_filtered_csvs(raw_dir: Path, out_dir: Path) -> None:
#     """Filter every raw CSV in raw_dir and write the CAN+SparkFun subset to out_dir.

#     Args:
#         raw_dir: directory containing one raw CSV per driver.
#         out_dir: directory to write filtered CSVs into; created if missing.
#     """
#     out_dir.mkdir(parents=True, exist_ok=True)
#     for csv_file in sorted(raw_dir.glob("*.csv")):
#         df = pd.read_csv(csv_file)
#         filtered = select_can_and_sparkfun_columns(df)
#         out_path = out_dir / csv_file.name
#         filtered.to_csv(out_path, index=False)
#         print(f"{csv_file.name}: raw {df.shape} -> filtered {filtered.shape}")


if __name__ == "__main__":
    # 1. Generate column-level sampling rate artifact for documentation.
    sample_file = DATA_RAW / "G1_Subject1.csv"
    sample_df = pd.read_csv(sample_file)
    filtered = select_can_and_sparkfun_columns(sample_df)
    report = report_column_sampling_rates(filtered)
#     save_sampling_rate_artifact(
#         report,
#         OUT_REPORTS / "column_sampling_rates.md",
#         sample_file.name,
#     )
#     print(f"Sampling rate artifact written to "
#           f"{OUT_REPORTS / 'column_sampling_rates.md'}")
#     print(f"({len(report)} columns from {sample_file.name})")

#     # 2. (Re)filter all raw CSVs and write to processed_data/.
#     write_filtered_csvs(DATA_RAW, DATA_PROCESSED)
