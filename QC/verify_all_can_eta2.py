"""SUPERSEDED — η² leakage audit over ALL 102 CAN signals.

⚠️ Retained for provenance; kept runnable; no longer the basis for any decision.

This script applies **one statistic, η², to all 102 signals regardless of type**.
η² compares group means, which is the wrong question for a step signal (an average
gear of 4.3 is not a quantity) and no question at all for an event signal absent
92% of the drive. The 15 step and 6 event signals it scores were therefore never
cleared by any evidence that applied to them.

Superseded by three type-matched scripts covering the same 102 signals:

  - verify_continuous_separability.py  (81) η² raw, η² per-window-mean, MI share
  - verify_step_separability.py        (15) Cramér's V, Theil's U
  - verify_event_presence.py            (6) firing rate, spread, position in drive

This script also emits EXCLUDED/KEPT columns, which the three replacements
deliberately do not: a measurement that already knows the answer cannot audit it.
Decisions now live in outputs/reports/signal_exclusion_decisions.md.

The η² values it computes are correct — verified to 0.0000 against an independent
implementation over 79 signals. It is the single-statistic *design* that was wrong,
plus one interpretation now corrected in the report's banner: the thermal family
was described as scoring 0.08-0.38 when it actually spans 0.078 to 0.986.

Original docstring follows.

η² leakage audit over ALL 102 CAN signals (not just the excluded ones).

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
# Exclusions justified by something other than raw-sample eta^2, with the reason.
# Raw-sample eta^2 systematically UNDERSTATES leakage for slowly-drifting signals:
# a temperature that ramps from cold start to operating heat has huge *within*-driver
# variance (the ramp itself), which pushes eta^2 down — while its per-window mean
# still differs between drivers because each drove on a different day. Those signals
# are therefore cut on physics and on feature-level eta^2, not on this statistic.
# Evidence: removing the thermal/ambient/electrical family moved the Random Forest
# from 74% to 29% (outputs/reports/research_plan.md), so they carried trip identity
# despite scoring 0.08-0.38 here.
NON_ETA_REASONS = {
    **{spn: "bursty command PGN (TSC1): absent ~92% of the time; ffill fabricates "
            "a phantom override" for spn in (898, 518, 4191)},
    3544: "state-conditional countdown (EOI), meaningless outside certain states",
    **{spn: "protocol constant, no behavioural content" for spn in (4206, 4207)},
    **{spn: "thermal state: proxies trip timing (each driver drove a distinct day), "
            "not a driver action"
       for spn in (105, 110, 177, 412, 1136, 3241, 3242, 3246, 4360, 4363, 4765, 5862)},
    **{spn: "ambient condition: weather and time of day, not behaviour"
       for spn in (108, 171)},
    168: "electrical state (battery potential), not a driver action",
    **{spn: "thermal-management actuator: responds to engine heat, not to the driver"
       for spn in (975, 986)},
    **{spn: "aftertreatment/DPF state: regeneration cycle timing, not behaviour"
       for spn in (3721, 5466, 3031, 1172)},
}
NON_ETA_EXCLUSIONS = set(NON_ETA_REASONS)


def discover_can_spns(csv_path) -> set[int]:
    """All CAN SPNs present as signal columns ('<spn> Name ...') in a raw CSV."""
    header = pd.read_csv(csv_path, nrows=0).columns
    return {int(m.group(1)) for c in header if (m := re.match(r"^(\d+)\s", c))}


def flag(e: float) -> str:
    if np.isnan(e):
        return "⚪"
    if e >= ETA_HIGH:
        return "🔴"
    if e <= ETA_LOW:
        return "🟢"
    return "🟡"


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
    non_eta_rows = [r for r in rows if r["spn"] in NON_ETA_EXCLUSIONS]
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
        "## What this statistic can and cannot see",
        "",
        "η² over **raw samples** answers: does each driver occupy a distinct value "
        "band? It is the right instrument for a signal that jitters around a level "
        "(pedal, torque, load) and the **wrong** one for a signal that ramps.",
        "",
        "A temperature climbing from cold start to operating heat has large "
        "*within*-driver variance — the ramp itself — which pushes η² down, while "
        "its per-window **mean** still separates drivers because each drove on a "
        "different day. Such signals are cut on physics and on feature-level η² "
        "instead; see the reasoned list below. The empirical proof that they leak: "
        "removing the thermal/ambient/electrical family moved the Random Forest "
        "from **74% to 29%** despite those signals scoring 0.08–0.38 here.",
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

    lines += [
        "",
        f"## Exclusions justified on grounds other than raw-sample η² ({len(non_eta_rows)})",
        "",
        "Each of these is excluded for a stated reason, so a low η² here is expected "
        "rather than contradictory.",
        "",
        "| η² | SPN | Signal | Why excluded |",
        "|--:|--:|---|---|",
    ]
    for r in sorted(non_eta_rows, key=lambda r: -(r["eta2"] if not np.isnan(r["eta2"]) else -1)):
        eta_text = "—" if np.isnan(r["eta2"]) else f"{r['eta2']:.3f}"
        lines.append(f"| {eta_text} | {r['spn']} | {r['signal']} | "
                     f"{NON_ETA_REASONS[r['spn']]} |")

    out = OUT_REPORTS / "all_can_eta2.md"
    out.write_text("\n".join(lines) + "\n")

    print(f"{len(rows)} CAN signals ({n_excl} excluded).")
    print(f"AUDIT — kept-but-high-η²: {len(missed_leak)}  |  "
          f"excluded-but-low-η² (unexplained): {len(weak_cut)}")
    print(f"Report written to {out}")
