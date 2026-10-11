"""η² leakage audit over ALL 102 CAN signals (not just the excluded ones).

Purpose: document AND stress-test the EXCLUDE_SPNS decisions in one report. For
every CAN signal, η² = between-driver variance / total variance of the raw
native-rate values (does the signal separate drivers into distinct bands?).

This report does NOT auto-generate the exclude list. η² FLAGS; physics DECIDES
(a high-η² signal can still be genuine style — e.g. braking abruptness). The
initial list was physics-proposed (counters / levels / ambient) and η²-confirmed.
This report's job is:
  - JUSTIFY: excluded signals should cluster near η² ≈ 1.0.
  - AUDIT: a KEPT signal with η² ≈ 1.0 = a possible MISSED leak; an EXCLUDED
    signal with LOW η² = a cut that needs a non-η² reason (or reconsideration).

Not every exclusion is η²-driven: the bursty command PGNs (898/518/4191/3544)
and protocol constants (4206/4207) were cut for orthogonal reasons and may show
low η². They are labelled so they don't read as false inconsistencies.

Reuses `eta_squared` + `collect_excluded_signal_values` from the leakage audit.
Reads data/raw_data/ (all columns present), applies EXCLUDE_DRIVERS.
Writes outputs/reports/all_can_eta2.md.

Run from repo root:
    python -m QC.verify_all_can_eta2
"""

import re

import numpy as np
import pandas as pd

from src.qc.verification_of_excluded_spn import (
    collect_excluded_signal_values,
    eta_squared,
)
from src.config import DATA_RAW, EXCLUDE_DRIVERS, EXCLUDE_SPNS, OUT_REPORTS

REF_DRIVER = "G1_Subject1"
ETA_HIGH   = 0.90     # separates drivers cleanly — leak suspect
ETA_LOW    = 0.50     # drivers overlap — behavioural
# Exclusions cut for reasons ORTHOGONAL to η² (ffill-unreliable / protocol):
NON_ETA_EXCLUSIONS = {898, 518, 4191, 3544, 4206, 4207}


def discover_can_spns(csv_path) -> set[int]:
    """All CAN SPNs present as signal columns ('<spn> Name ...') in a raw CSV."""
    header = pd.read_csv(csv_path, nrows=0).columns
    return {int(m.group(1)) for c in header if (m := re.match(r"^(\d+)\s", c))}


# def flag(e: float) -> str:
#     if np.isnan(e):
#         return "⚪"
#     if e >= ETA_HIGH:
#         return "🔴"
#     if e <= ETA_LOW:
#         return "🟢"
#     return "🟡"


if __name__ == "__main__":
    all_spns = discover_can_spns(DATA_RAW / f"{REF_DRIVER}.csv")
    print(f"Discovered {len(all_spns)} CAN SPNs in {DATA_RAW / f'{REF_DRIVER}.csv'}")
    per_spn, names = collect_excluded_signal_values(DATA_RAW, EXCLUDE_DRIVERS, all_spns)

    rows = []
    for spn in all_spns:
        if not per_spn.get(spn):
            continue
        e = eta_squared(per_spn[spn])
        rows.append({
            "spn": spn, "signal": names.get(spn, "?")[:46], "eta2": e,
            "status": "EXCLUDED" if spn in EXCLUDE_SPNS else "KEPT",
            "flag": flag(e),
        })
    rows.sort(key=lambda r: (-(r["eta2"] if not np.isnan(r["eta2"]) else -1)))

    # Audit: the two inconsistency classes.
    missed_leak = [r for r in rows
                   if r["status"] == "KEPT" and not np.isnan(r["eta2"])
                   and r["eta2"] >= ETA_HIGH]
    weak_cut = [r for r in rows
                if r["status"] == "EXCLUDED" and not np.isnan(r["eta2"])
                and r["eta2"] < ETA_LOW and r["spn"] not in NON_ETA_EXCLUSIONS]

    n_excl = sum(r["status"] == "EXCLUDED" for r in rows)
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CAN leakage audit — η² over all signals",
        "",
        f"{len(rows)} CAN signals ({n_excl} EXCLUDED / {len(rows)-n_excl} KEPT), "
        f"46 drivers. η² = between-driver variance / total; 1.0 = each driver a "
        "distinct band (trip fingerprint), 0.0 = drivers overlap (behavioural). "
        "**η² flags; physics decides.**",
        "",
        f"- 🔴 η² ≥ {ETA_HIGH} (separates drivers cleanly — leak suspect)  ·  "
        f"🟡 {ETA_LOW}–{ETA_HIGH}  ·  🟢 ≤ {ETA_LOW} (behavioural)",
        "",
        "## ⚠️ Audit — inconsistencies to review first",
        "",
        f"**KEPT but η² ≥ {ETA_HIGH} (possible MISSED leak): {len(missed_leak)}**",
    ]
    if missed_leak:
        lines += ["", "| η² | SPN | Signal |", "|--:|--:|---|"]
        lines += [f"| {r['eta2']:.3f} | {r['spn']} | {r['signal']} |" for r in missed_leak]
    else:
        lines.append("_None — no kept signal separates drivers like a leak._")

    lines += ["",
              f"**EXCLUDED but η² < {ETA_LOW} and not a known non-η² cut "
              f"(questionable): {len(weak_cut)}**"]
    if weak_cut:
        lines += ["", "| η² | SPN | Signal |", "|--:|--:|---|"]
        lines += [f"| {r['eta2']:.3f} | {r['spn']} | {r['signal']} |" for r in weak_cut]
    else:
        lines.append("_None — every low-η² exclusion has a documented non-η² reason._")

    lines += [
        "",
        "## All CAN signals — ranked by η² (leak → behavioural)",
        "",
        "| η² | flag | status | SPN | Signal | note |",
        "|--:|:--:|:--|--:|---|---|",
    ]
    for r in rows:
        note = "non-η² exclusion (bursty/protocol)" if r["spn"] in NON_ETA_EXCLUSIONS else ""
        lines.append(f"| {r['eta2']:.3f} | {r['flag']} | {r['status']} | "
                     f"{r['spn']} | {r['signal']} | {note} |")

    out = OUT_REPORTS / "all_can_eta2.md"
    out.write_text("\n".join(lines) + "\n")

    print(f"{len(rows)} CAN signals ({n_excl} excluded).")
    print(f"AUDIT — kept-but-high-η²: {len(missed_leak)}  |  "
          f"excluded-but-low-η² (unexplained): {len(weak_cut)}")
    print(f"Report written to {out}")
