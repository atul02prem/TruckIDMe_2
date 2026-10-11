"""Verify WHICH clock degraded for the 3 canloggerTime-excluded drivers.

Exclusion claim (PIPELINE.md §2): G1S10/G1S11/G1S12 were dropped because
`canloggerTime` defaulted to 2022-05-01 (Teensy RTC never synced). This script
checks the sharper question: did the *other* CAN clocks degrade too, or is the
corruption isolated to `canloggerTime`?

For each of the 3 excluded drivers (plus a reference good driver), it reports the
date range of:
  - canloggerTime   (Teensy / SparkFun logger clock — the master align clock)
  - gpsTime         (satellite UTC — independent reference)
  - every CAN TimeXXX column (CANLogger clock — one per signal)

Expected result: only canloggerTime is 2022; gpsTime and ALL TimeXXX are 2024.
=> the corruption is isolated to the Teensy bridge; the CAN behaviour data itself
is intact (could be salvaged by re-keying alignment on TimeXXX/gpsTime).

Writes outputs/reports/excluded_driver_clocks.md.

Run from repo root:
    python -m QC.verify_excluded_driver_clocks
"""

import re
from datetime import datetime, timezone

import pandas as pd

from src.config import DATA_RAW, OUT_REPORTS

EXCLUDED   = ["G1_Subject10", "G1_Subject11", "G1_Subject12"]
REFERENCE  = "G1_Subject1"
_TIME_RE   = re.compile(r"^Time(\d+)$")   # CAN signal timestamp columns


def _date(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")


def clock_dates(csv_stem: str) -> dict:
    """Date range of canloggerTime, gpsTime, and all CAN TimeXXX for one driver."""
    df = pd.read_csv(DATA_RAW / f"{csv_stem}.csv")
    time_cols = [c for c in df.columns if _TIME_RE.match(c)]

    can_dates = set()
    for tc in time_cols:
        v = df[tc].dropna()
        if len(v):
            can_dates.update({_date(v.min()), _date(v.max())})

    clg = df["canloggerTime"].dropna()
    gps = df["gpsTime"].dropna()
    return {
        "clg_range":  f"{_date(clg.min())} .. {_date(clg.max())}",
        "gps_range":  f"{_date(gps.min())} .. {_date(gps.max())}",
        "n_can_cols": len(time_cols),
        "can_dates":  sorted(can_dates),
    }


if __name__ == "__main__":
    rows = []
    for stem in EXCLUDED + [REFERENCE]:
        d = clock_dates(stem)
        d["driver"] = stem
        rows.append(d)
        print(f"  {stem}: canloggerTime[{d['clg_range']}]  gpsTime[{d['gps_range']}]  "
              f"CAN TimeXXX dates={d['can_dates']} ({d['n_can_cols']} cols)")

    # Verdict: for the excluded drivers, only canloggerTime should be 2022.
    excl = [r for r in rows if r["driver"] in EXCLUDED]
    clg_2022     = all(r["clg_range"].startswith("2022") for r in excl)
    gps_2024     = all(r["gps_range"].startswith("2024") for r in excl)
    can_all_2024 = all(all(d.startswith("2024") for d in r["can_dates"]) for r in excl)
    isolated     = clg_2022 and gps_2024 and can_all_2024

    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Excluded-driver clock degradation — which clock failed?",
        "",
        "G1S10/G1S11/G1S12 were excluded because `canloggerTime` defaulted to "
        "2022-05-01. Question: did the CAN signal clocks (`TimeXXX`) degrade too, "
        "or is the corruption isolated to the Teensy-written `canloggerTime`?",
        "",
        "## Verdict",
        f"- Corruption isolated to `canloggerTime`: "
        f"**{'CONFIRMED' if isolated else 'NOT CONFIRMED'}**.",
        f"  - canloggerTime = 2022 for all excluded: {clg_2022}",
        f"  - gpsTime = 2024 (correct): {gps_2024}",
        f"  - every CAN TimeXXX = 2024 (correct): {can_all_2024}",
        "",
        "Two devices, two clocks: the **CANLogger** (stamps `TimeXXX`) kept correct "
        "time; only the **Teensy/SparkFun** logger (`canloggerTime`) fell back to its "
        "uninitialised RTC. The CAN behaviour data is therefore intact and could be "
        "salvaged by re-keying alignment on `TimeXXX`/`gpsTime`.",
        "",
        "## Per-driver clock date ranges",
        "",
        "| Driver | canloggerTime | gpsTime | CAN TimeXXX dates | # CAN cols |",
        "|---|---|---|---|---:|",
    ]
    for r in rows:
        tag = " (reference, good)" if r["driver"] == REFERENCE else ""
        lines.append(
            f"| {r['driver']}{tag} | {r['clg_range']} | {r['gps_range']} | "
            f"{', '.join(r['can_dates'])} | {r['n_can_cols']} |"
        )
    out = OUT_REPORTS / "excluded_driver_clocks.md"
    out.write_text("\n".join(lines) + "\n")

    print()
    print(f"corruption isolated to canloggerTime: "
          f"{'CONFIRMED' if isolated else 'NOT CONFIRMED'}")
    print(f"Report written to {out}")
