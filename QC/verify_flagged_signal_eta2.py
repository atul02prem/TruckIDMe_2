"""T4 of the signal-integrity thread: does the *value* of each flagged signal
(3030, 5052, 2979) separate drivers — i.e. leak trip identity — or overlap
(behavioural)? This is the decider for keep-vs-exclude, since T1-T3 already
showed the Δt anomalies are not informative on/off patterns.

Metric: η² = between-driver variance / total variance of the raw native-rate
values (reuses `eta_squared` from the leakage audit). η²→1 = each driver a
distinct band = trip fingerprint = exclude; η²→0 = drivers overlap = behavioural.

WHY anchors, not a fixed threshold: raw-value η² lives on a different scale than
the audit's feature-η² (max kept feature was 0.468). So we compute η² for the 3
suspects ALONGSIDE calibrators and judge by proximity:
  - behavioural anchors (KEPT, should be low):  91 pedal, 84 speed, 190 RPM
  - leak anchor (EXCLUDED cumulative counter, ~1.0):  245
A suspect near the behavioural anchors -> keep; near the leak anchor -> exclude.

Reads data/raw_data/ (all columns present), applies EXCLUDE_DRIVERS.
Writes outputs/reports/flagged_signal_eta2.md.

Run from repo root:
    python -m QC.verify_flagged_signal_eta2
"""

import numpy as np

from src.qc.verification_of_excluded_spn import (
    collect_excluded_signal_values,
    eta_squared,
)
from src.config import DATA_RAW, EXCLUDE_DRIVERS, OUT_REPORTS

TARGETS         = {3030, 5052, 2979}   # the flagged signals under investigation
REF_BEHAVIOURAL = {91, 84, 190}        # KEPT anchors — expected low η²
REF_LEAK        = {245}                # EXCLUDED cumulative-counter anchor — expected η²≈1

ETA_LEAK = 0.90    # >= this => trip fingerprint => exclude
ETA_OK   = 0.50    # <= this => behavioural => keep


def verdict(e: float, lo: float, hi: float) -> str:
    """Keep/exclude call for a suspect, anchor-calibrated (lo=behav, hi=leak)."""
    if np.isnan(e):
        return "⚪ no data"
    if e >= ETA_LEAK or e >= hi - 0.05:
        return "🔴 leak → exclude"
    if e <= ETA_OK or e <= lo + 0.10:
        return "🟢 behavioural → keep"
    return "🟡 borderline → judgment"


if __name__ == "__main__":
    all_spns = TARGETS | REF_BEHAVIOURAL | REF_LEAK
    per_spn, names = collect_excluded_signal_values(DATA_RAW, EXCLUDE_DRIVERS, all_spns)

    eta = {spn: eta_squared(per_spn[spn]) for spn in all_spns if per_spn.get(spn)}
    behav = [eta[s] for s in REF_BEHAVIOURAL if s in eta and not np.isnan(eta[s])]
    leak  = [eta[s] for s in REF_LEAK if s in eta and not np.isnan(eta[s])]
    lo = float(np.mean(behav)) if behav else 0.0
    hi = float(np.mean(leak)) if leak else 1.0

    role = ({s: "🎯 suspect" for s in TARGETS}
            | {s: "behavioural anchor" for s in REF_BEHAVIOURAL}
            | {s: "leak anchor" for s in REF_LEAK})

    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# T4 — η² of the flagged signals (value separability)",
        "",
        f"Do 3030 / 5052 / 2979 leak driver identity through their *values*? "
        f"η² = between-driver variance / total. Calibrated by anchors: behavioural "
        f"mean η² ≈ **{lo:.3f}** (91/84/190), leak anchor η² ≈ **{hi:.3f}** (245).",
        "",
        "## ⚠️ Verdicts — read these first",
        "",
        "| suspect | Signal | η² | verdict |",
        "|--:|---|--:|:--|",
    ]
    for spn in TARGETS:
        e = eta.get(spn, float("nan"))
        nm = names.get(spn, "?")[:44]
        lines.append(f"| {spn} | {nm} | {e:.3f} | {verdict(e, lo, hi)} |")

    lines += [
        "",
        "## Context — all η² ranked (suspects + anchors)",
        "",
        "| η² | role | SPN | Signal |",
        "|--:|:--|--:|---|",
    ]
    for spn, e in sorted(eta.items(), key=lambda kv: (-kv[1] if not np.isnan(kv[1]) else 0)):
        lines.append(f"| {e:.3f} | {role.get(spn,'')} | {spn} | {names.get(spn,'?')[:44]} |")

    lines += [
        "",
        f"Thresholds: η² ≥ {ETA_LEAK} (or ≈ leak anchor) → exclude; "
        f"η² ≤ {ETA_OK} (or ≈ behavioural anchor) → keep; else judgment.",
    ]

    out = OUT_REPORTS / "flagged_signal_eta2.md"
    out.write_text("\n".join(lines) + "\n")

    print(f"behavioural anchor η²≈{lo:.3f}   leak anchor η²≈{hi:.3f}")
    for spn in TARGETS:
        e = eta.get(spn, float("nan"))
        print(f"  🎯 SPN {spn}: η²={e:.3f}  {verdict(e, lo, hi)}")
    print(f"Report written to {out}")
