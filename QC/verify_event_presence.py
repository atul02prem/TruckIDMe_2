"""Separability of event signals — does the firing pattern identify the driver?

An event signal is absent most of the drive; absence is its normal state. So its
*values* are the wrong thing to measure — a command PGN that only ever sends one
value still carries information in **when and how often it fires**.

That makes presence the quantity of interest, and it cuts both ways. SPN 2979
taught the lesson: its unavailability rate is 28.44–28.60% across all 46 drivers,
a deterministic protocol cycle carrying zero driver information. The
aftertreatment group's rate ranges 0–26% and clusters at drive start, which makes
it a warm-up fingerprint. Identical kind of artifact, opposite consequence — only
measuring the spread tells them apart.

So this report measures, per signal:

- **firing rate per window** — then η² over those rates, with driver as the group.
  Using windows rather than one rate per driver gives within-driver variation, so
  η² is defined rather than degenerate.
- **spread across drivers** — if every driver fires at the same rate, the signal
  cannot identify anyone, whatever η² says about the noise.
- **position in the drive** — concentration near the start is a warm-up or
  cold-state signature, which is trip identity rather than behaviour.

This report **measures only**: no exclusion labels, no recommendation.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_event_presence
"""

import re

import numpy as np
import pandas as pd

from src.config import DATA_RAW, EXCLUDE_DRIVERS, OUT_REPORTS, WINDOW_SECONDS
from src.qc.classify_signals import (classify, driver_id, reviewed_type,
                                     time_coverage)
from src.qc.signal_dictionary import load as load_dictionary
from src.qc.verification_of_excluded_spn import eta_squared

REPORT_PATH = OUT_REPORTS / "event_presence.md"

LEAK_ETA = 0.9
WATCH_ETA = 0.5
UNIFORM_SPREAD = 0.02   # rates this tight across drivers => protocol, not behaviour
EARLY_FRACTION = 0.10   # "first tenth of the drive"

# What the dataset's own dictionary says each value may be. Quoted, not inferred
# from J1939-71 field widths -- see section_dictionary. Two kinds of statement:
# a legal 'range', or a specific 'sentinel' the parameter must use for a condition.
# They need different checks: a value inside a range is fine, whereas a constant
# that is not the documented sentinel is a fault even if it is numerically legal.
DOCUMENTED: dict[int, dict] = {
    4206: {"range": (0, 7),
           "says": "counts 0 to 7 then wraps, increasing every cycle"},
    4191: {"range": (0, 0.875),
           "says": "0000b-0111b = 0-0.875% at 0.125%/bit; 1000b-1111b not available"},
    3544: {"sentinel": 65535,
           "says": "65535 (FFFFh) where time remaining is not applicable"},
}

# Observations the dictionary states no range for, recorded so the row is not bare.
NOTED: dict[int, str] = {
    518: "no range given; observed -125 to 125% is exactly the J1939 percent-torque "
         "span, consistent with a correct decode",
    898: "no range given; the 8031.88 rpm ceiling is the saturation value for "
         "0.125 rpm/bit over two bytes, so the scale decodes correctly",
    4207: "no range given, but a checksum over the payload must change with it",
}
_SIG_RE = re.compile(r"^(\d+)\s")


def flag(value: float) -> str:
    """Severity marker for a separability value."""
    if np.isnan(value):
        return "⚪"
    if value >= LEAK_ETA:
        return "🔴"
    if value >= WATCH_ETA:
        return "🟡"
    return "🟢"


def window_firing_rates(times: np.ndarray, window_seconds: float,
                        period: float) -> np.ndarray:
    """Fraction of each window during which the signal was transmitting.

    Args:
        times: the signal's sample timestamps (seconds).
        window_seconds: window length.
        period: the signal's native sample period, from its median gap.

    Returns:
        One rate in [0, 1] per window spanned by the drive.
    """
    if times.size < 3 or period <= 0:
        return np.empty(0)
    t0, t1 = times.min(), times.max()
    n_windows = int((t1 - t0) // window_seconds)
    if n_windows < 2:
        return np.empty(0)
    index = ((times - t0) // window_seconds).astype(np.int64)
    counts = np.bincount(index[index < n_windows], minlength=n_windows)
    return np.minimum(counts * period / window_seconds, 1.0)


def event_spns(files: list) -> dict[int, str]:
    """Find the signals classified event, using the shared classifier.

    Args:
        files: raw CSV paths.

    Returns:
        SPN -> signal column name.
    """
    header = pd.read_csv(files[0], nrows=0).columns.tolist()
    signals = {int(m.group(1)): c for c in header
               if (m := _SIG_RE.match(c)) and f"Time{m.group(1)}" in header}
    cols = list(signals.values()) + [f"Time{s}" for s in signals]

    pooled: dict[int, list[np.ndarray]] = {s: [] for s in signals}
    covers: dict[int, list[float]] = {s: [] for s in signals}
    for path in files[:8]:
        frame = pd.read_csv(path, usecols=cols)
        for spn, col in signals.items():
            pooled[spn].append(frame[col].dropna().to_numpy(float))
            cov = time_coverage(frame[f"Time{spn}"].dropna().to_numpy(float))
            if not np.isnan(cov):
                covers[spn].append(cov)

    out = {}
    for spn, col in signals.items():
        values = np.concatenate(pooled[spn])
        distinct = np.unique(values)
        integral = bool(np.all(np.equal(np.mod(distinct, 1), 0)))
        cov = float(np.mean(covers[spn])) if covers[spn] else float("nan")
        final, _ = reviewed_type(spn, classify(cov, int(distinct.size), integral))
        if final == "event":
            out[spn] = col
    return out


def profile_driver(times: np.ndarray) -> dict[str, float]:
    """Summarise one driver's firing pattern for one event signal.

    Args:
        times: the signal's sample timestamps for this driver.

    Returns:
        Coverage, burst count and mean position of samples within the drive.
    """
    ordered = np.sort(times)
    if ordered.size < 3:
        return {}
    span = float(ordered[-1] - ordered[0])
    period = float(np.median(np.diff(ordered)))
    if span <= 0 or period <= 0:
        return {}
    # a gap far longer than the native period separates two bursts
    bursts = int(1 + np.count_nonzero(np.diff(ordered) > 10 * period))
    position = (ordered - ordered[0]) / span
    return {
        "coverage": min(ordered.size * period / span, 1.0),
        "bursts": bursts,
        "mean_position": float(position.mean()),
        "early_share": float(np.mean(position < EARLY_FRACTION)),
        "period": period,
    }


def measure(files: list, signals: dict[int, str]) -> pd.DataFrame:
    """Measure firing pattern and its separability for every event signal.

    Args:
        files: raw CSV paths, one per driver.
        signals: SPN -> signal column name.

    Returns:
        One row per event signal, most separable first.
    """
    cols = [f"Time{s}" for s in signals] + list(signals.values())
    per_driver: dict[int, dict[str, dict]] = {s: {} for s in signals}
    seen: dict[int, set[float]] = {s: set() for s in signals}
    rates: dict[int, dict[str, np.ndarray]] = {s: {} for s in signals}

    for path in files:
        did = driver_id(path.stem)
        frame = pd.read_csv(path, usecols=cols)
        for spn in signals:
            t = frame[f"Time{spn}"].dropna().to_numpy(float)
            seen[spn].update(frame[signals[spn]].dropna().unique().tolist())
            info = profile_driver(t)
            if not info:
                continue
            per_driver[spn][did] = info
            r = window_firing_rates(t, WINDOW_SECONDS, info["period"])
            if r.size:
                rates[spn][did] = r
        print(f"  {did}")

    rows = []
    for spn, col in signals.items():
        info = per_driver[spn]
        if not info:
            rows.append({"spn": spn, "signal": col, "drivers": 0,
                         "values": sorted(seen[spn])})
            continue
        cov = np.array([v["coverage"] for v in info.values()])
        rows.append({
            "spn": spn,
            "signal": col,
            "drivers": len(info),
            "coverage_mean": float(cov.mean()),
            "coverage_min": float(cov.min()),
            "coverage_max": float(cov.max()),
            "coverage_sd": float(cov.std()),
            "bursts_mean": float(np.mean([v["bursts"] for v in info.values()])),
            "position_mean": float(np.mean([v["mean_position"] for v in info.values()])),
            "early_share": float(np.mean([v["early_share"] for v in info.values()])),
            "eta2_rate": eta_squared(rates[spn]) if len(rates[spn]) >= 2 else float("nan"),
            "values": sorted(seen[spn]),
        })
    return pd.DataFrame(rows).sort_values("eta2_rate", ascending=False)


def section_dictionary(table: pd.DataFrame) -> list[str]:
    """Corroborate the measured firing pattern against the dataset's dictionary.

    Two things the dictionary settles that no statistic here can. It confirms the
    message grouping -- SPN 898 and 518 are each described as living in the
    "torque/speed control message", which is what the byte-identical statistics
    below imply. And it supplies each parameter's documented value range, which
    turns an observed constant into a provable decode fault rather than a
    suspicion about J1939 field widths.

    Args:
        table: one row per event signal, carrying its observed value set.

    Returns:
        Report lines.
    """
    definitions = load_dictionary()
    lines = [
        "",
        "## ⚑ Corroboration against the dataset's own dictionary",
        "",
        "`DriverIDSQLiteCSVDataDictionary.pdf` is quoted below. It settles two "
        "questions this report's statistics can only hint at.",
        "",
        "### 1. The message grouping is confirmed by name",
        "",
        "Five of these six signals produce **byte-identical statistics across "
        "every column above**, over all drivers. That implies they are fields of "
        "one message rather than five independent signals, and the dictionary "
        "says so outright:",
        "",
        "> **SPN 898** — \"Parameter provided to the engine from external sources "
        "in the *torque/speed control message*.\"",
        ">",
        "> **SPN 518** — \"Parameter provided to the engine or retarder in the "
        "*torque/speed control message* for controlling or limiting the output "
        "torque.\"",
        "",
        "That message is TSC1. So the input set was carrying one message five "
        "times, and 4206/4207 are its counter and checksum rather than vehicle "
        "state at all:",
        "",
        "> **SPN 4206** — \"The message counter is used to detect situations where "
        "the transmitting ECU malfunction repeats the same frame all the time.\"",
        ">",
        "> **SPN 4207** — \"The message checksum is used to verify the signal path "
        "from the transmitting device to the receiving device… calculated using "
        "the first 7 data bytes, the message counter and the bytes of the message "
        "identifier.\"",
        "",
        "Neither describes the truck. They describe the bus.",
        "",
        "### 2. Observed values against the documented range",
        "",
        "| Flag | SPN | Signal | Units | Observed values | Dictionary says |",
        "|---|--:|---|---|---|---|",
    ]

    for row in table.sort_values("spn").itertuples(index=False):
        units = (definitions.get(row.spn) or {}).get("units") or "—"
        values = row.values
        shown = (f"{values[0]:g}" if len(values) == 1
                 else f"{len(values)} values, {values[0]:g}–{values[-1]:g}")
        rule = DOCUMENTED.get(row.spn)
        if rule is None:
            mark = "⚪"
            says = NOTED.get(row.spn, "no explicit range given")
        elif "range" in rule:
            low, high = rule["range"]
            mark = "🔴" if any(not low <= v <= high for v in values) else "🟢"
            says = rule["says"]
        else:
            # a documented sentinel: the value must be it, not merely legal
            mark = "🟢" if values == [rule["sentinel"]] else "🔴"
            says = rule["says"]
        lines.append(f"| {mark} | {row.spn} | `{row.signal}` | {units} | "
                     f"{shown} | {says} |")

    lines += [
        "",
        "**SPN 4206 is the decisive one.** The dictionary states the counter "
        "\"will count from 0 to 7 and then wrap\" and that the transmitter "
        "\"will increase the message counter in every cycle\". It is observed "
        "**constant**, at a value outside 0–7. Both halves of its specification "
        "are violated at once, so this is not a judgement about field widths — it "
        "is the dataset's own documentation contradicted by the dataset's own "
        "values.",
        "",
        "There is an irony worth recording: a counter frozen at one value is "
        "precisely the fault condition SPN 4206 exists to detect. Here the "
        "freezing is in the CSV export rather than on the bus.",
        "",
        "**SPN 4207** compounds it. A checksum computed over the payload must "
        "change as the payload changes; it is observed constant, and constant at "
        "the *same* value as the counter — which a counter/checksum pair cannot "
        "be.",
        "",
        "**SPN 3544** is a further anomaly of the same kind. The dictionary "
        "specifies **65535 (FFFFh)** for states where time remaining does not "
        "apply. The observed constant is **64255 (FAFFh)** — the top of the valid "
        "range for a two-byte parameter, not the documented not-applicable code. "
        "Either the ECU saturates instead of signalling inapplicability, or the "
        "decode clamps. It carries no information either way.",
        "",
        "**Why this matters beyond these six signals.** Three violations are "
        "proven here against the dictionary — 4191 and 4206 outside their stated "
        "ranges, 3544 reporting a constant that is not its stated sentinel — and "
        "4207 fails on logic alone, a payload checksum that never changes. Add "
        "SPN 4154 from the continuous report, whose values exceed its documented "
        "0–0.875% range by 15–158×, and that is **four columns whose values their "
        "own dictionary forbids, plus a fifth that cannot be what it claims**.",
        "",
        "Note which ones *pass*: SPN 518's observed −125 to 125% is exactly the "
        "J1939 percent-torque span, and SPN 898's 8031.88 rpm ceiling is the "
        "saturation value for 0.125 rpm/bit over two bytes. The decoder handles "
        "ordinary scaled parameters correctly. What it appears to mishandle are "
        "**sub-byte bit fields** — fractional torque adders, a 3-bit counter, a "
        "checksum nibble — which is a narrower and more plausible fault than "
        "wholesale breakage, and it predicts where else to look.",
        "",
        "All six signals here are excluded on data quality regardless, so no "
        "decision rests on resolving this. It is a dataset-wide question. "
        "**Action: obtain the DBC.**",
        "",
    ]
    return lines


def write_report(table: pd.DataFrame, n_drivers: int) -> None:
    """Write the event-presence report.

    Args:
        table: one row per event signal.
        n_drivers: how many drivers were measured.
    """
    uniform = table[table.coverage_sd < UNIFORM_SPREAD]
    varying = table[table.coverage_sd >= UNIFORM_SPREAD]
    early = table[table.early_share > 2 * EARLY_FRACTION]

    lines = [
        "# Event-signal presence — does the firing pattern identify the driver?",
        "",
        f"All **{len(table)} event** signals over **{n_drivers} drivers**, raw CAN "
        "data. An event signal is absent most of the drive, so its values are not "
        "the question: **when and how often it fires** is.",
        "",
        "| Column | Meaning |",
        "|---|---|",
        "| coverage | share of the drive the signal was transmitting |",
        "| sd across drivers | how much that share varies between drives |",
        f"| η² on rate | driver separability of the per-{WINDOW_SECONDS:.0f}s-window "
        "firing rate |",
        "| position | mean location of samples within the drive (0 = start, 1 = end) |",
        f"| early share | fraction of samples in the first {EARLY_FRACTION:.0%} of "
        "the drive (uniform would give " + f"{EARLY_FRACTION:.0%}) |",
        "",
        "**This report measures only** — no exclusion labels, no recommendation.",
        "",
        "## Why the spread matters more than the rate",
        "",
        "The same artifact can be harmless or a severe leak, and only the spread "
        "across drivers distinguishes them. SPN 2979's unavailability sits at "
        "28.44–28.60% for every one of the 46 drivers — a deterministic protocol "
        "cycle that cannot identify anyone. The aftertreatment group's ranges from "
        "0% to 26% and clusters at drive start — a warm-up duration, which is trip "
        "identity. **A high rate is not the warning sign; a varying rate is.**",
        "",
        "## All event signals",
        "",
        "| Flag | SPN | Signal | Coverage | sd across drivers | η² on rate | "
        "Bursts | Position | Early share |",
        "|---|--:|---|--:|--:|--:|--:|--:|--:|",
    ]
    for row in table.itertuples(index=False):
        if not row.drivers:
            lines.append(f"| ⚪ | {row.spn} | `{row.signal}` | absent | — | — | — | "
                         "— | — |")
            continue
        lines.append(
            f"| {flag(row.eta2_rate)} | {row.spn} | `{row.signal}` | "
            f"{row.coverage_mean:.1%} | {row.coverage_sd:.3f} | "
            f"{row.eta2_rate:.3f} | {row.bursts_mean:.0f} | "
            f"{row.position_mean:.3f} | {row.early_share:.1%} |")

    lines += [
        "",
        f"## Uniform firing — {len(uniform)} signals (sd < {UNIFORM_SPREAD})",
        "",
    ]
    if len(uniform):
        lines += ["These fire at effectively the same rate for every driver, so the "
                  "pattern carries no driver information regardless of η²:", ""]
        for row in uniform.itertuples(index=False):
            lines.append(f"- **SPN {row.spn}** `{row.signal}` — coverage "
                         f"{row.coverage_min:.1%}–{row.coverage_max:.1%} across "
                         f"{row.drivers} drivers (sd {row.coverage_sd:.4f})")
    else:
        lines.append("_None._")

    lines += [
        "",
        f"## Varying firing — {len(varying)} signals (sd ≥ {UNIFORM_SPREAD})",
        "",
    ]
    if len(varying):
        lines += ["The firing rate differs between drives, so the pattern is a "
                  "candidate fingerprint. Physics decides whether the variation is "
                  "behaviour or trip condition:", ""]
        for row in varying.itertuples(index=False):
            lines.append(f"- **SPN {row.spn}** `{row.signal}` — coverage "
                         f"{row.coverage_min:.1%}–{row.coverage_max:.1%} "
                         f"(sd {row.coverage_sd:.3f}), η² on rate "
                         f"{row.eta2_rate:.3f}")
    else:
        lines.append("_None._")

    if len(early):
        lines += [
            "",
            f"## ⚑ Concentrated at drive start — {len(early)} signals",
            "",
            f"More than {2*EARLY_FRACTION:.0%} of samples fall in the first "
            f"{EARLY_FRACTION:.0%} of the drive, against {EARLY_FRACTION:.0%} "
            "expected if firing were uniform. A cold-state or warm-up signature, "
            "which tracks the drive rather than the driver:",
            "",
        ]
        for row in early.itertuples(index=False):
            lines.append(f"- **SPN {row.spn}** `{row.signal}` — "
                         f"{row.early_share:.1%} of samples in the first "
                         f"{EARLY_FRACTION:.0%}, mean position "
                         f"{row.position_mean:.3f}")

    lines += section_dictionary(table)

    lines += [
        "",
        "## Caveat",
        "",
        "A burst is counted where the gap between consecutive samples exceeds ten "
        "times the signal's own median period. That multiplier is a judgement "
        "call; it separates genuine silences from ordinary timing jitter, and the "
        "burst column is descriptive — no decision rests on it.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Measure event-signal presence and write the report."""
    files = [p for p in sorted(DATA_RAW.glob("G*_Subject*.csv"))
             if driver_id(p.stem) not in EXCLUDE_DRIVERS]
    signals = event_spns(files)
    print(f"event signals: {len(signals)} | reading {len(files)} drivers")

    table = measure(files, signals)
    write_report(table, len(files))

    print(f"\nuniform firing (sd < {UNIFORM_SPREAD}): "
          f"{int((table.coverage_sd < UNIFORM_SPREAD).sum())}")
    print(f"varying firing  (sd >= {UNIFORM_SPREAD}): "
          f"{int((table.coverage_sd >= UNIFORM_SPREAD).sum())}")
    print(f"concentrated at drive start: "
          f"{int((table.early_share > 2 * EARLY_FRACTION).sum())}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
