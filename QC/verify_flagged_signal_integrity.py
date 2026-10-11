"""Test WHY the sampling-rate QC flagged SPN 3030, 5052, 2979 — are their Δt
anomalies physically explained (so the signals are honest but state-conditional),
or artefacts? Part of the signal-integrity thread
(`outputs/reports/signal_integrity_thread.md`).

Hypotheses tested (see thread for the full chain):
  H1 (T1): 3030 "TC Ratio" goes SILENT when the torque-converter lockup clutch is
           engaged — i.e. its ~49% dropout is lockup-conditional, not a fault.
           Reference = SPN 573 "TC Lockup Engaged" (100 Hz, verified healthy).
  H2 (T2): 5052 "Clutch/Converter Input Speed" — same mechanism vs 573.
  H3 (T3): 2979 "Vehicle Accel Rate Limit Status" is genuinely event-driven
           multi-rate (a share of Δt faster than the 50 Hz mode = bursts), not an
           artefact.

Method:
  T1/T2 — for every 573 state sample (its value rounded to an integer state), ask
          whether the target signal (3030 / 5052) has a sample within TOL seconds
          (merge_asof nearest). Group by 573 state -> presence fraction. If one
          state suppresses the target (presence ~0) and another keeps it
          (presence ~1), the dropout is state-conditional. Aggregated over all
          usable drivers (weighted by sample count).
  T3   — Δt of 2979: fraction of intervals below the 50 Hz mode period (bursts),
         plus Δt percentiles, averaged over drivers.

Pass criteria (thread T1/T2/T3):
  T1/T2: min-presence state < 0.30 AND max-presence state > 0.80.
  T3:    >= 30% of Δt below the mode period.

Writes outputs/reports/flagged_signal_integrity.md (flagged/verdict format).

Run from repo root:
    python -m QC.verify_flagged_signal_integrity
"""

import re

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, EXCLUDE_DRIVERS, OUT_REPORTS

LOCKUP_SPN   = 573          # reference state: TC Lockup Engaged (100 Hz, healthy)
STATE_TARGETS = {3030: "H1/T1", 5052: "H2/T2"}   # signals whose silence we test vs 573
BURST_SPN    = 2979         # multi-rate signal for the Δt-distribution test
TOL_S        = 0.05         # "present near t" window for merge_asof (~2.5× 50 Hz period)
MODE_DT_2979 = 0.02         # 50 Hz native period; Δt below this = a burst
PRES_LOW     = 0.30         # presence below this = state suppresses the signal
PRES_HIGH    = 0.80         # presence above this = state keeps the signal
BURST_FRAC   = 0.30         # T3: this share of Δt below mode => multimodal

_ID = re.compile(r"^G(\d+)_Subject(\d+)$")


def _driver_id(stem: str) -> str:
    m = _ID.match(stem)
    return f"G{m.group(1)}S{int(m.group(2)):02d}"


def _col(cols, spn: int) -> str | None:
    """The signal (value) column for an SPN, e.g. '3030 Transmission ...'."""
    pref = f"{spn} "
    return next((c for c in cols if c.startswith(pref)), None)


def presence_by_state(state_t, state_v, target_t) -> dict:
    """{573 state -> (presence_fraction, n_state_samples)} for one driver.

    presence = fraction of this state's samples that have a target-signal sample
    within TOL_S seconds.
    """
    s = pd.DataFrame({"t": np.asarray(state_t, float),
                      "v": np.asarray(state_v, float)}).dropna().sort_values("t")
    if s.empty:
        return {}
    s["v"] = s["v"].round().astype(int)
    tgt = pd.DataFrame({"t": np.sort(np.asarray(pd.Series(target_t).dropna(), float))})
    if tgt.empty:
        return {}
    tgt["present"] = 1.0
    m = pd.merge_asof(s, tgt, on="t", direction="nearest", tolerance=TOL_S)
    m["present"] = m["present"].fillna(0.0)
    return {int(v): (float(g["present"].mean()), int(len(g)))
            for v, g in m.groupby("v")}


def dt_burst_fraction(target_t) -> tuple:
    """(frac below mode period, p10, p50, p90) of 2979's Δt for one driver."""
    t = np.sort(np.asarray(pd.Series(target_t).dropna(), float))
    dt = np.diff(t)
    dt = dt[dt > 0]
    if dt.size < 3:
        return None
    return (float(np.mean(dt < MODE_DT_2979 * 0.9)),
            *[float(x) for x in np.percentile(dt, [10, 50, 90])])


def run() -> dict:
    """Accumulate T1/T2/T3 evidence across all usable drivers."""
    time_re = re.compile(r"^Time(\d+)$")
    want_time = {LOCKUP_SPN, BURST_SPN, *STATE_TARGETS}

    pres = {spn: {} for spn in STATE_TARGETS}     # spn -> state -> [pres_weighted_sum, count]
    burst = []                                     # per-driver (frac_burst, p10, p50, p90)
    n_drivers = 0

    for f in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
        if _driver_id(f.stem) in EXCLUDE_DRIVERS:
            continue
        cols = pd.read_csv(f, nrows=0).columns
        state_col = _col(cols, LOCKUP_SPN)
        keep = [c for c in cols
                if (m := time_re.match(c)) and int(m.group(1)) in want_time]
        if state_col:
            keep.append(state_col)
        df = pd.read_csv(f, usecols=keep)
        n_drivers += 1

        # T1 / T2: target silence vs 573 lockup state
        if state_col and f"Time{LOCKUP_SPN}" in df:
            for spn in STATE_TARGETS:
                tcol = f"Time{spn}"
                if tcol not in df:
                    continue
                by_state = presence_by_state(df[f"Time{LOCKUP_SPN}"], df[state_col], df[tcol])
                for st, (frac, n) in by_state.items():
                    acc = pres[spn].setdefault(st, [0.0, 0])
                    acc[0] += frac * n
                    acc[1] += n

        # T3: 2979 burst fraction
        if f"Time{BURST_SPN}" in df:
            d = dt_burst_fraction(df[f"Time{BURST_SPN}"])
            if d:
                burst.append(d)

    return {"n_drivers": n_drivers, "pres": pres, "burst": burst}


if __name__ == "__main__":
    res = run()
    n = res["n_drivers"]

    lines = [
        "# Flagged-signal integrity — T1/T2/T3",
        "",
        f"{n} usable drivers. Tests why the sampling QC flagged SPN 3030, 5052 "
        "(dropout) and 2979 (multi-rate). See `signal_integrity_thread.md`.",
        "",
        "## ⚠️ Verdicts — read these first",
        "",
        "| test | signal | verdict | evidence |",
        "|:--:|--:|:--:|---|",
    ]

    verdicts = []
    # T1 / T2
    for spn, label in STATE_TARGETS.items():
        states = {st: (w / c if c else float("nan"), c)
                  for st, (w, c) in res["pres"][spn].items()}
        if states:
            lo = min(states.values(), key=lambda x: x[0])[0]
            hi = max(states.values(), key=lambda x: x[0])[0]
            ok = lo < PRES_LOW and hi > PRES_HIGH
            flag = "🟢 confirmed" if ok else "🔴 refuted"
            ev = "; ".join(f"state {st}: present {p*100:.0f}% (n={c:,})"
                           for st, (p, c) in sorted(states.items()))
        else:
            flag, ev = "⚪ no data", "573 or target column missing"
        verdicts.append((label, spn, flag, ev))

    # T3
    if res["burst"]:
        b = np.array(res["burst"])
        frac_burst = b[:, 0].mean()
        p10, p50, p90 = b[:, 1].mean(), b[:, 2].mean(), b[:, 3].mean()
        ok = frac_burst >= BURST_FRAC
        flag = "🔴 confirmed multi-rate" if ok else "🟢 single-rate"
        ev = (f"{frac_burst*100:.0f}% of Δt below the {1/MODE_DT_2979:.0f} Hz mode "
              f"period; Δt p10/p50/p90 = {p10*1000:.1f}/{p50*1000:.1f}/{p90*1000:.1f} ms")
    else:
        flag, ev = "⚪ no data", "Time2979 missing"
    verdicts.append(("H3/T3", BURST_SPN, flag, ev))

    for label, spn, flag, ev in verdicts:
        lines.append(f"| {label} | {spn} | {flag} | {ev} |")

    # Detail: presence-by-state tables
    lines += ["", "## T1/T2 detail — target presence by 573 lockup state", ""]
    for spn, label in STATE_TARGETS.items():
        lines += [f"### {label}: SPN {spn} presence vs SPN {LOCKUP_SPN} state", "",
                  "| 573 state | target present % | state samples |",
                  "|--:|--:|--:|"]
        states = res["pres"][spn]
        for st in sorted(states):
            w, c = states[st]
            lines.append(f"| {st} | {(w/c*100 if c else 0):.1f}% | {c:,} |")
        lines.append("")

    out = OUT_REPORTS / "flagged_signal_integrity.md"
    out.write_text("\n".join(lines) + "\n")

    print(f"{n} drivers.")
    for label, spn, flag, ev in verdicts:
        print(f"  {label:>6} SPN {spn}: {flag}  — {ev}")
    print(f"Report written to {out}")
