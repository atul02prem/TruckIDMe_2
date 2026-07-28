"""Verify the clock semantics of the dataset.

Claim (PIPELINE.md §1):
  - gpsTime is satellite **UTC**.
  - canloggerTime is CAN-logger **local** time (Mountain, MDT = UTC-6 in the
    Apr-Sep 2024 drive window).
  - CAN signal TimeXXX columns share the canloggerTime (local) reference.
  => use gpsTime only to VALIDATE the clock (independent), canloggerTime to ALIGN.

Evidence produced per driver:
  1. gpsTime - canloggerTime ~ 6.00 h (21,600 s): a whole-hour TIMEZONE offset
     (not random drift) -> the two clocks are in different references.
  2. canloggerTime decoded naively -> Colorado daytime wall clock (local);
     gpsTime decoded naively -> ~6 h later (UTC).
  3. |canloggerTime - Time91| ~ 0 s: CAN timestamps align with canloggerTime,
     not gpsTime -> CAN times are local.

Writes outputs/reports/clock_semantics.md.

Run from repo root:
    python -m scripts.verify_clock_semantics
"""

import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, EXCLUDE_DRIVERS, OUT_REPORTS

_DRIVER_ID_RE = re.compile(r"^G(\d+)_Subject(\d+)$")
# MDT_OFFSET_S  = 6 * 3600   # UTC - MDT (all drives are Apr-Sep 2024 = MDT)


def filename_to_driver_id(stem: str) -> str:
    m = _DRIVER_ID_RE.match(stem)
    if not m:
        raise ValueError(f"Cannot parse driver ID from {stem!r}")
    return f"G{m.group(1)}S{int(m.group(2)):02d}"


def _wall(epoch: float) -> str:
    """Naive-UTC decode of an epoch value -> 'YYYY-MM-DD HH:MM' wall clock."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def analyse_driver(csv_path) -> dict:
    """Compute the three clock-semantics checks for one driver."""
    df = pd.read_csv(csv_path, usecols=lambda c: c in
                     {"canloggerTime", "gpsTime", "Time91", "Time84"})
    pair = df[["canloggerTime", "gpsTime"]].dropna()
    offset = pair["gpsTime"] - pair["canloggerTime"]

    clg_min = pair["canloggerTime"].min()
    gps_min = pair["gpsTime"].min()
    # CAN alignment: how close does a CAN Time column start to canloggerTime?
    can_col = "Time91" if "Time91" in df.columns else "Time84"
    can_align_s = abs(clg_min - df[can_col].dropna().min())

    return {
        "offset_h":      offset.mean() / 3600.0,
        "offset_std_s":  offset.std(),
        "can_align_s":   can_align_s,
        "can_col":       can_col,
        "clg_wall":      _wall(clg_min),          # local wall clock (if claim holds)
        "gps_wall":      _wall(gps_min),          # UTC wall clock
    }


if __name__ == "__main__":
    rows = []
    for csv_file in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        # if driver_id in EXCLUDE_DRIVERS:
        #     continue
        r = analyse_driver(csv_file)
        r["driver"] = driver_id
        rows.append(r)
        print(f"  {driver_id}: offset={r['offset_h']:.4f} h  "
              f"|clg-{r['can_col']}|={r['can_align_s']:.2f} s  "
              f"local={r['clg_wall']}  utc={r['gps_wall']}")

    offs = np.array([r["offset_h"] for r in rows])
    aligns = np.array([r["can_align_s"] for r in rows])
    # local wall-clock hour (should be daytime, ~7-19)
    hours = np.array([int(r["clg_wall"][-5:-3]) for r in rows])

    near_6h   = np.all(np.abs(offs - 6.0) < 0.05)          # within 3 min of 6h
    can_local = np.all(aligns < 10.0)                       # CAN starts within 10 s of canloggerTime
    daytime   = np.all((hours >= 6) & (hours <= 20))        # local decode is daytime

    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Clock semantics verification",
        "",
        "Claim: `gpsTime` = satellite **UTC**; `canloggerTime` = CAN-logger "
        "**local** (MDT, UTC-6); CAN `TimeXXX` share the local reference. "
        "Use `gpsTime` to validate, `canloggerTime` to align.",
        "",
        "## Verdict",
        f"- gpsTime - canloggerTime = 6.00 h for all drivers: "
        f"**{'PASS' if near_6h else 'FAIL'}** "
        f"(mean {offs.mean():.4f} h, range {offs.min():.4f}-{offs.max():.4f}). "
        "A whole-hour timezone offset -> the clocks are in different frames.",
        f"- canloggerTime decodes to daytime (local): "
        f"**{'PASS' if daytime else 'FAIL'}** (hours {hours.min()}-{hours.max()}). "
        "-> canloggerTime is the local wall clock; gpsTime (6 h later) is UTC.",
        f"- CAN TimeXXX aligns with canloggerTime, not gpsTime: "
        f"**{'PASS' if can_local else 'FAIL'}** (max |offset| {aligns.max():.2f} s). "
        "-> CAN timestamps are local; align on canloggerTime.",
        "",
        "## Per-driver",
        "",
        "| Driver | gps−clg (h) | offset std (s) | \\|clg−CANtime\\| (s) | "
        "canloggerTime (local) | gpsTime (UTC) |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['driver']} | {r['offset_h']:.4f} | {r['offset_std_s']:.3f} | "
            f"{r['can_align_s']:.2f} | {r['clg_wall']} | {r['gps_wall']} |"
        )
    out = OUT_REPORTS / "clock_semantics.md"
    out.write_text("\n".join(lines) + "\n")

    print()
    print(f"near-6h offset: {'PASS' if near_6h else 'FAIL'}   "
          f"CAN-local: {'PASS' if can_local else 'FAIL'}   "
          f"daytime-local: {'PASS' if daytime else 'FAIL'}")
    print(f"Report written to {out}")
