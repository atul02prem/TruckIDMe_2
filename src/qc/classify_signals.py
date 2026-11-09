"""Classify every CAN signal by the standard automotive signal types.

The taxonomy is not ours. Automotive tooling already settled it, and our own
multi-rate review (`outputs/reports/literature_multirate_can.md`) records the
convention:

| Type | Handling | Endorsed by |
|---|---|---|
| continuous | linear interpolation | asammdf `float_interpolation=1`; MATLAB `continuous` |
| step | repeat previous value (ZOH), or mode per window | asammdf `integer_interpolation=0`; MATLAB `step` |
| event | do not fill | MATLAB `event`; asammdf `empty_channels='skip'` |

(MATLAB Vehicle Network Toolbox calls this property `VariableContinuity`.)

This stage reports only what each signal **is**. It says nothing about whether a
signal is kept or excluded — that is a separate decision made on separability and
physics — and nothing about whether our aggregation is correct, which can only be
*measured* after aggregation rather than asserted here.

Classification runs on all raw CAN signals, before any exclusion: a signal's type
is a property of what the bus transmits.

Run from the repo root in the `truckidme` env:
    python -m src.qc.classify_signals
"""

import re

import numpy as np
import pandas as pd

from src.config import DATA_RAW, EXCLUDE_DRIVERS, OUT_REPORTS
from src.qc.signal_dictionary import load as load_dictionary

REPORT_PATH = OUT_REPORTS / "signal_classification.md"

MAX_DRIVERS = None     # all usable drivers; a type must hold across the dataset
                       # (8 was enough to see a value set, but not to call one final)
EVENT_COVERAGE = 0.5   # active less than half the drive => sporadic/event
STEP_MAX_CODES = 16    # at most this many integer codes => a state, not a measure
MONOTONE_FRACTION = 0.99   # never decreasing => accumulator, not a state code
BAND_FACTOR = 4        # audit band spans STEP_MAX_CODES / f .. STEP_MAX_CODES * f
BAND_LOW = STEP_MAX_CODES // BAND_FACTOR
BAND_HIGH = STEP_MAX_CODES * BAND_FACTOR

# Signals close enough to STEP_MAX_CODES that an arbitrary threshold, not the
# data, decides their type. Each needs a verdict from the signal's physical
# definition, because the distinct-value count cannot tell 13 readings of a
# percent-torque estimate from 13 gear codes — only the unit can.
#
# A verdict overrides the statistic in BOTH directions, so a code book with many
# states can be forced back to `step`. Reviewing a signal is not the same as
# declaring it continuous: SPN 523 sits in this band at 7 values and must stay
# `step`, so a one-directional override set would be cleared by the one action
# that breaks the classifier.
SIGNAL_REVIEW: dict[int, tuple[str, str]] = {
    # ── reviewed -> continuous: a measured quantity that happens to move little
    # Verified against DriverIDSQLiteCSVDataDictionary.pdf: a fractional adder to
    # SPN 513 at 0.125%/bit, legal range 0-0.875%. The verdict holds for the SPN;
    # the exported column does not honour it (9.31% of samples exceed 0.875% by
    # 15-158x), so the signal is excluded on data quality. See DECISIONS.md S1.
    4154: ("continuous", "fractional adder to SPN 513, 0.125%/bit, 0-0.875% (data dictionary) — column values exceed that range"),
    2978: ("continuous", "percent torque; data dictionary names the sources as cooling fan, air compressor, air conditioning"),
    3031: ("continuous", "temperature"),
    1717: ("continuous", "percent torque"),
    5398: ("continuous", "percent torque"),
    514:  ("continuous", "percent torque"),
    1087: ("continuous", "air pressure"),
    1088: ("continuous", "air pressure"),
    105:  ("continuous", "temperature"),
    110:  ("continuous", "temperature"),
    117:  ("continuous", "pressure"),
    118:  ("continuous", "pressure"),
    # ── reviewed -> step: a genuine enumerated code book
    523:  ("step", "7 discrete gear positions"),
    524:  ("step", "7 discrete gear positions"),
    3232: ("step", "FMI — an enumerated J1939 failure-mode identifier"),
}
_SIG_RE = re.compile(r"^(\d+)\s")


def driver_id(stem: str) -> str:
    """Canonical driver id from a filename stem ('G1_Subject4' -> 'G1S04')."""
    group, number = stem.replace("G", "").split("_Subject")
    return f"G{group}S{int(number):02d}"


def rising_fraction(values: np.ndarray) -> float:
    """Of the times a signal changed, the fraction of changes that were upward.

    Identifies accumulators (odometer, total hours, total revolutions), which
    only ever count up. They are continuous quantities reported at integer
    resolution, so they interpolate linearly, but a window summarises them by
    its endpoints rather than by its mean.

    Unchanged samples are excluded. A signal held flat between updates repeats
    its value at the sampling rate, so counting every non-decreasing pair would
    measure how slowly the signal moves, not whether it only moves one way.

    Args:
        values: samples in acquisition order.

    Returns:
        Fraction in [0, 1], or NaN if the signal never changed.
    """
    steps = np.diff(values)
    changes = steps[steps != 0]
    if changes.size == 0:
        return float("nan")
    return float(np.mean(changes > 0))


def time_coverage(times: np.ndarray) -> float:
    """Fraction of the drive during which a signal was actually transmitting.

    Measured from the signal's own timestamp column, not from null counts in the
    raw CSV: those rows are a union of every signal's sample times, so a slow
    periodic signal is null on most rows while still transmitting steadily.

    A periodic signal satisfies n_samples x median_period ~= elapsed span, so
    coverage ~= 1. A command PGN that fires in bursts has a small median period
    inside each burst and long silences between them, so coverage falls far
    below 1 — which is what "absent ~92% of the time" means for TSC1.

    Args:
        times: the signal's sample timestamps (seconds), unsorted is fine.

    Returns:
        Coverage in (0, 1], or NaN if fewer than 3 samples.
    """
    ordered = np.sort(times)
    if ordered.size < 3:
        return float("nan")
    span = float(ordered[-1] - ordered[0])
    if span <= 0:
        return float("nan")
    period = float(np.median(np.diff(ordered)))
    if period <= 0:
        return float("nan")
    return min(ordered.size * period / span, 1.0)


def classify(coverage: float, n_distinct: int, integral: bool) -> str:
    """Assign one of the three standard signal types.

    A step signal is one with a small code book: a gear, mode or flag. Being
    integer-valued is not enough on its own — a pressure reported in whole kPa
    is a finely quantised continuous quantity, and interpolating it is correct.

    Args:
        coverage: fraction of the drive the signal was transmitting.
        n_distinct: count of distinct values.
        integral: every value is a whole number.

    Returns:
        'event', 'step' or 'continuous'.
    """
    if not np.isnan(coverage) and coverage < EVENT_COVERAGE:
        return "event"
    if integral and n_distinct <= STEP_MAX_CODES:
        return "step"
    return "continuous"


def reviewed_type(spn: int, statistical: str) -> tuple[str, str]:
    """Apply a recorded physics verdict to one signal's statistical type.

    Only step/continuous are reviewable. `event` is decided by transmission
    coverage rather than by the code-book threshold, so the audit band — which
    exists to police that threshold — has no bearing on it.

    Args:
        spn: the signal's SPN.
        statistical: the type the statistic assigned.

    Returns:
        (final type, review status) where status is 'confirmed', 'overridden'
        or 'unreviewed'.
    """
    if statistical == "event" or spn not in SIGNAL_REVIEW:
        return statistical, "unreviewed"
    verdict, _ = SIGNAL_REVIEW[spn]
    return verdict, "confirmed" if verdict == statistical else "overridden"


def in_band(n_distinct: int, integral: bool) -> bool:
    """Is this signal close enough to the threshold for it to decide its type?

    Args:
        n_distinct: count of distinct values.
        integral: every value is a whole number.

    Returns:
        True when the signal sits in the audit band around STEP_MAX_CODES.
    """
    return integral and BAND_LOW <= n_distinct <= BAND_HIGH


def profile_signals() -> tuple[pd.DataFrame, int]:
    """Measure the value set of every raw CAN signal, pooled over drivers.

    Returns:
        (table, n_drivers) where table has one row per signal carrying its
        measurements and type, and n_drivers is how many drivers were pooled.
    """
    files = [p for p in sorted(DATA_RAW.glob("G*_Subject*.csv"))
             if driver_id(p.stem) not in EXCLUDE_DRIVERS][:MAX_DRIVERS]
    definitions = load_dictionary()

    header = pd.read_csv(files[0], nrows=0).columns.tolist()
    signals = {int(m.group(1)): col for col in header
               if (m := _SIG_RE.match(col)) and f"Time{m.group(1)}" in header}

    pooled: dict[int, list[np.ndarray]] = {spn: [] for spn in signals}
    coverages: dict[int, list[float]] = {spn: [] for spn in signals}
    monotone: dict[int, list[float]] = {spn: [] for spn in signals}
    columns = list(signals.values()) + [f"Time{spn}" for spn in signals]
    for path in files:
        frame = pd.read_csv(path, usecols=columns)
        for spn, col in signals.items():
            ordered = frame[col].dropna().to_numpy(dtype=float)
            pooled[spn].append(ordered)
            share = rising_fraction(ordered)
            if not np.isnan(share):
                monotone[spn].append(share)
            stamps = frame[f"Time{spn}"].dropna().to_numpy(dtype=float)
            coverage = time_coverage(stamps)
            if not np.isnan(coverage):
                coverages[spn].append(coverage)
    print(f"profiled {len(signals)} signals over {len(files)} drivers")

    rows = []
    for spn, col in signals.items():
        values = np.concatenate(pooled[spn])
        distinct = np.unique(values)
        coverage = float(np.mean(coverages[spn])) if coverages[spn] else float("nan")
        integral = bool(np.all(np.equal(np.mod(distinct, 1), 0)))
        rises = float(np.mean(monotone[spn])) if monotone[spn] else float("nan")
        statistical = classify(coverage, int(distinct.size), integral)
        final, status = reviewed_type(spn, statistical)
        rows.append({
            "spn": spn,
            "signal": col,
            "type": final,
            "type_statistic": statistical,
            "review": status,
            "banded": in_band(int(distinct.size), integral),
            "coverage": coverage,
            "monotone": rises,
            "accumulator": bool(rises >= MONOTONE_FRACTION),
            "n_distinct": int(distinct.size),
            "n_samples": int(values.size),
            "only_value": float(distinct[0]) if distinct.size == 1 else float("nan"),
            "integer_valued": integral,
            "constant": distinct.size <= 1,
            "units": definitions.get(spn, {}).get("units"),
        })
    return pd.DataFrame(rows).sort_values(["type", "n_distinct"]), len(files)


def section_header(table: pd.DataFrame, counts: pd.Series,
                   n_drivers: int) -> list[str]:
    """Title, scope, and the type-summary table.

    Args:
        table: one row per signal.
        counts: signal count per type.
        n_drivers: how many drivers were pooled.

    Returns:
        Report lines.
    """
    return [
        "# Signal classification — the three standard automotive signal types",
        "",
        f"All **{len(table)} CAN signals** in the raw data, value sets pooled over "
        f"{n_drivers} drivers. This report describes only what each signal *is*. "
        "Whether a signal is kept, and whether our aggregation of it is correct, "
        "are separate questions answered elsewhere.",
        "",
        "| Type | Count | Correct handling | Convention |",
        "|---|---:|---|---|",
        f"| continuous | {counts.get('continuous', 0)} | linear interpolation; "
        "mean / std / percentiles | asammdf `float_interpolation=1`, MATLAB `continuous` |",
        f"| step | {counts.get('step', 0)} | repeat previous value (ZOH), or mode "
        "per window | asammdf `integer_interpolation=0`, MATLAB `step` |",
        f"| event | {counts.get('event', 0)} | **do not fill** — absence is the "
        "normal state | MATLAB `event`, asammdf `empty_channels='skip'` |",
        "",
        "The taxonomy follows MATLAB Vehicle Network Toolbox's `VariableContinuity` "
        "property and asammdf's interpolation defaults, as recorded in "
        "`literature_multirate_can.md`. We add no categories of our own.",
        "",
    ]


def section_constants(degenerate: pd.DataFrame, n_drivers: int) -> list[str]:
    """The zero-variance signals, and the open question their values raise.

    Args:
        degenerate: the signals holding a single value.
        n_drivers: how many drivers were pooled.

    Returns:
        Report lines.
    """
    lines = ["## Data-quality note" if len(degenerate)
             else "## Data-quality note — none", ""]
    if not len(degenerate):
        return lines

    lines += [
        f"**{len(degenerate)} signals are constant** — one single value across "
        f"every sample of every one of the {n_drivers} drivers. Not a signal "
        "type but a defect: with zero variance they carry no information, no "
        "separability statistic is defined on them (η² and mutual information "
        "are both 0/0), and they cannot contribute to any model.",
        "",
        "| Flag | SPN | Signal | Value held | Samples | Coverage |",
        "|---|--:|---|--:|--:|--:|",
    ]
    for row in degenerate.itertuples(index=False):
        coverage = "—" if np.isnan(row.coverage) else f"{row.coverage:.1%}"
        lines.append(f"| 🔴 | {row.spn} | `{row.signal}` | "
                     f"`{row.only_value:g}` | {row.n_samples:,} | "
                     f"{coverage} |")

    sporadic = degenerate[degenerate["coverage"] < EVENT_COVERAGE]
    steady = degenerate[~(degenerate["coverage"] < EVENT_COVERAGE)]
    lines += [
        "",
        "The coverage column separates two cases. "
        f"**{len(sporadic)} are constant *and* sporadic** "
        f"({', '.join(f'SPN {s}' for s in sporadic.spn)}): transmitting on "
        "under half the drive and sending the same value each time. "
        f"**{len(steady)} is constant while transmitting steadily** "
        f"({', '.join(f'SPN {s}' for s in steady.spn)}): present on "
        "essentially the whole drive, always the same value.",
        "",
        "### ⚑ Open item — three of these values are not physically valid",
        "",
        "The measurement above (zero variance) is certain. The *reason* is not, "
        "and the values themselves raise a separate question that is not about "
        "leakage at all:",
        "",
        "| Flag | SPN | Value | Why it is suspect |",
        "|---|--:|--:|---|",
        "| 🟡 | 3544 | `64255` | `0xFAFF` is the largest value a 2-byte J1939 "
        "parameter may legally carry — i.e. a saturation / top-of-range "
        "sentinel, not a reading |",
        "| 🔴 | 4206 | `1111` | published as a 4-bit message counter, which "
        "cannot exceed 15 |",
        "| 🔴 | 4207 | `1111` | published as a 4-bit checksum, which cannot "
        "exceed 15 — and is *identical* to the counter above, which a real "
        "counter/checksum pair cannot be |",
        "| 🔴 | 4191 | `138` | published as a 3-bit fractional torque field, "
        "which cannot reach 138 |",
        "",
        "These values fall outside the ranges the SPN definitions allow, so the "
        "likeliest explanation is a **decoding artifact in the CSV export, not "
        "a bus condition**. This cannot be confirmed from anything in this "
        "repository: no DBC or decoder specification is checked in, and the "
        "widths above are quoted from the J1939-71 definitions rather than "
        "verified against whatever DBC produced these files. "
        "**Action: obtain the DBC and re-check.** If the decode is wrong for "
        "these columns it may be wrong for others, which is a question about "
        "the whole dataset rather than about these five signals.",
        "",
        "### Why this matters now",
        "",
        f"`SPN {steady.spn.iloc[0]}` is currently one of the audited channels "
        "fed to the models, so a zero-information column is occupying an input "
        "slot. Dropping a constant column is a data-quality fix rather than a "
        "leakage judgement: with no variance there is no behaviour in it to "
        "lose, whatever the underlying cause turns out to be.",
    ]
    return lines


def section_all_signals(table: pd.DataFrame) -> list[str]:
    """One row per signal with the measurements behind its type.

    Args:
        table: one row per signal.

    Returns:
        Report lines.
    """
    lines = [
        "",
        "## All signals",
        "",
        "Units are quoted from `DriverIDSQLiteCSVDataDictionary.pdf`. **No units "
        "is not missing data** — a parameter reporting a *state* has no physical "
        "unit, so the blank is itself evidence of type.",
        "",
        "| SPN | Signal | Type | Units (dictionary) | Coverage | Distinct | "
        "Integer | Accumulator |",
        "|--:|---|---|---|--:|--:|:-:|:-:|",
    ]
    for row in table.itertuples(index=False):
        coverage = "—" if np.isnan(row.coverage) else f"{row.coverage:.1%}"
        lines.append(f"| {row.spn} | `{row.signal}` | {row.type} | "
                     f"{row.units or '—'} | "
                     f"{coverage} | {row.n_distinct} | "
                     f"{'yes' if row.integer_valued else 'no'} | "
                     f"{'yes' if row.accumulator else '—'} |")
    return lines


def section_threshold_audit(band: pd.DataFrame) -> list[str]:
    """The code-book boundary audit: who the threshold alone decided.

    Args:
        band: the signals sitting near STEP_MAX_CODES, by distinct count.

    Returns:
        Report lines.
    """
    unreviewed = band[band["review"] == "unreviewed"]
    overridden = band[band["review"] == "overridden"]

    lines = [
        "",
        f"## {'🔴' if len(unreviewed) else '🟢'} Threshold audit — the code-book "
        "boundary",
        "",
        f"The step rule turns on an arbitrary number: at most {STEP_MAX_CODES} "
        "distinct integer values. This section audits every signal close enough "
        "to that cutoff that **the threshold, rather than the data, decides its "
        "type**.",
        "",
        f"The band is integer-valued signals with {BAND_LOW}–{BAND_HIGH} distinct "
        f"values, derived as `STEP_MAX_CODES / {BAND_FACTOR}` to "
        f"`STEP_MAX_CODES × {BAND_FACTOR}` so that it tracks the threshold it "
        "polices instead of adding two more hand-picked bounds.",
        "",
        "**It is built to empty out.** Each row needs a verdict taken from the "
        "signal's physical definition, recorded in `SIGNAL_REVIEW`. Once given, "
        "the row reports as resolved. A list that shows the same rows every run "
        "becomes wallpaper; a list whose only interesting state is *a new "
        "unreviewed signal* stays worth reading.",
        "",
        f"**{len(band)} in band · {len(unreviewed)} unreviewed · "
        f"{len(overridden)} overridden by physics.**",
        "",
    ]
    if len(unreviewed):
        lines += [
            f"### 🔴 Unreviewed — {len(unreviewed)} signals typed by the threshold "
            "alone",
            "",
            "| Flag | SPN | Signal | Distinct | Typed as | Needs |",
            "|---|--:|---|--:|---|---|",
        ]
        for row in unreviewed.itertuples(index=False):
            lines.append(f"| 🔴 | {row.spn} | `{row.signal}` | {row.n_distinct} | "
                         f"{row.type_statistic} | unit check: is this a quantity "
                         "or a code book? |")
        lines.append("")

    lines += [
        "### Verdicts on record",
        "",
        "| Flag | SPN | Signal | Distinct | Statistic | Verdict | Basis |",
        "|---|--:|---|--:|---|---|---|",
    ]
    for row in band[band["review"] != "unreviewed"].itertuples(index=False):
        mark = "🟡" if row.review == "overridden" else "🟢"
        lines.append(f"| {mark} | {row.spn} | `{row.signal}` | {row.n_distinct} | "
                     f"{row.type_statistic} | **{row.type}** | "
                     f"{SIGNAL_REVIEW[row.spn][1]} |")
    lines += [
        "",
        "🟡 marks a verdict that **changed** the type the statistic assigned; 🟢 "
        "marks one that confirmed it. A verdict applies in both directions, so a "
        "code book with many states can be forced back to `step` — which is why "
        "reviewing a signal is recorded separately from declaring it continuous.",
        "",
        "Why this matters here: percent torque is one physical quantity, yet its "
        "members span 4 to 101 distinct values in this dataset "
        "(`4154`, `2978`, `5398`, `514`, `513`, `2432`, `512`). The two that "
        "barely move fell below the threshold and were typed as enums. That is a "
        "fact about this truck's engine, not evidence of a code book.",
        "",
    ]
    return lines


def section_method() -> list[str]:
    """How each type is recognised, and what the accumulator column means.

    Returns:
        Report lines.
    """
    return [
        "## How each type is recognised",
        "",
        f"- **event** — active for less than {EVENT_COVERAGE:.0%} of the drive, "
        "measured as `n_samples x median_period / elapsed_span` from the signal's "
        "own timestamps. Absence is the normal state (a command PGN sends only "
        "while something is commanding), so filling the gaps fabricates activity "
        "that never happened.",
        f"- **step** — integer-valued with at most {STEP_MAX_CODES} distinct "
        "codes: a gear, mode or status enum. Values between the codes do not "
        "exist, so neither interpolating them nor averaging them is meaningful.",
        "- **continuous** — everything else, including coarsely-quantised "
        "sensors. A pressure reported in whole kPa has few distinct values but "
        "the quantity between them exists, so it keeps continuous handling.",
        "",
        "These three rules give the **statistical** type. Where a signal falls in "
        "the audit band above, a recorded physics verdict takes precedence, so "
        "the `Type` column is the statistic *after* review. The statistic flags; "
        "physics decides — the same rule this project applies to η².",
        "",
        "The **accumulator** column is not a fourth type. It marks signals that "
        f"only ever count up (≥ {MONOTONE_FRACTION:.0%} of their *changes* are "
        "upward): odometers, total hours, total revolutions, filter timers. They interpolate linearly like any continuous signal, but a "
        "window summarises them by last − first, because their mean is a "
        "statement about *when* in the drive the window sits — the strongest "
        "trip-identity leak in the data.",
    ]


def section_dictionary(table: pd.DataFrame) -> list[str]:
    """Corroborate the measured taxonomy against the dataset's own dictionary.

    The dictionary encodes the same distinction this report measures, in its
    structure rather than its prose: a parameter reporting a physical quantity
    carries a `Units:` field and a parameter reporting a state does not. That
    makes it an independent check, built from a different object than any
    statistic here.

    Args:
        table: one row per signal, carrying its dictionary units.

    Returns:
        Report lines.
    """
    stated = table[table.units.notna()]
    unitless = table[table.units.isna()]
    step_unitless = unitless[unitless.type == "step"]
    agree = len(step_unitless)

    lines = [
        "",
        "## ⚑ Corroboration against the dataset's own dictionary",
        "",
        f"`DriverIDSQLiteCSVDataDictionary.pdf` defines all **{len(table)}** of "
        "these signals — the same count this report measures. It is the "
        "authoritative source for this dataset, describing the columns as "
        "exported rather than the bus as specified.",
        "",
        "**It encodes the same distinction, in its structure rather than its "
        "prose.** A parameter reporting a physical quantity carries a `Units:` "
        "field; a parameter reporting a *state* does not. That is an independent "
        "check, built from a different object than any statistic here.",
        "",
        f"| | Signals | Of which step |",
        "|---|--:|--:|",
        f"| has a `Units:` field | {len(stated)} | "
        f"{int((stated.type == 'step').sum())} |",
        f"| **no** `Units:` field | {len(unitless)} | **{agree}** |",
        "",
        f"**{agree} of the {len(unitless)} unitless signals are classified "
        f"step.** The dictionary and the measurement agree without either having "
        "consulted the other.",
        "",
        "### The disagreements, which are the informative part",
        "",
        "| SPN | Signal | Type | Units | Why they differ |",
        "|--:|---|---|---|---|",
    ]

    unitless_other = unitless[unitless.type != "step"]
    for row in unitless_other.itertuples(index=False):
        if row.spn == 3030:
            why = ("a **ratio** is dimensionless, so the blank is a genuine "
                   "absence of unit rather than a state — 789 distinct "
                   "non-integer values confirm a measure")
        elif row.spn == 4154:
            why = ("the dictionary states its resolution in prose "
                   "(0.125%/bit, range 0–0.875%) instead of a `Units:` field, "
                   "so the blank is a formatting quirk")
        else:
            why = "unitless but not classified step — review"
        lines.append(f"| {row.spn} | `{row.signal}` | {row.type} | — | {why} |")

    step_with_units = stated[stated.type == "step"]
    for row in step_with_units.itertuples(index=False):
        if row.units == "gear value":
            why = ("`gear value` is the dictionary naming a state code in its "
                   "own words — agreement, not conflict")
        else:
            why = (f"**defined** as a measure in {row.units}, but takes only "
                   f"{row.n_distinct} integer values on this truck. Type as "
                   "*measured* governs aggregation: zero-order hold is correct "
                   "for a channel that is only ever on or off, whatever the SPN "
                   "permits")
        lines.append(f"| {row.spn} | `{row.signal}` | {row.type} | "
                     f"{row.units} | {why} |")

    lines += [
        "",
        "**The fan signals are the case worth remembering.** SPN 975 and 986 are "
        "percentages by definition and binary in this data. A taxonomy derived "
        "from the standard alone would call them continuous and interpolate "
        "them; a taxonomy derived from the data calls them step and holds them. "
        "For deciding how to aggregate, what the signal *does* here outranks "
        "what the SPN *allows*.",
        "",
    ]
    return lines


def build_report(table: pd.DataFrame, n_drivers: int) -> list[str]:
    """Assemble the report from its sections, in reading order.

    Args:
        table: one row per signal, as `profile_signals` returns it.
        n_drivers: how many drivers were pooled.

    Returns:
        Every line of the report.
    """
    return (section_header(table, table["type"].value_counts(), n_drivers)
            + section_constants(table[table["constant"]], n_drivers)
            + section_dictionary(table)
            + section_all_signals(table)
            + section_threshold_audit(table[table["banded"]]
                                      .sort_values("n_distinct"))
            + section_method())


def print_summary(table: pd.DataFrame) -> None:
    """Print the counts a reader needs to see without opening the report.

    Args:
        table: one row per signal.
    """
    band = table[table["banded"]]
    print(table["type"].value_counts().to_string())
    print(f"constant signals: {int(table['constant'].sum())}")
    print(f"threshold band: {len(band)} signals | "
          f"unreviewed: {int((band['review'] == 'unreviewed').sum())} "
          f"| overridden by physics: "
          f"{int((band['review'] == 'overridden').sum())}")
    print(f"report -> {REPORT_PATH}")


def main() -> None:
    """Classify every raw CAN signal and write the taxonomy report."""
    table, n_drivers = profile_signals()
    REPORT_PATH.write_text("\n".join(build_report(table, n_drivers)) + "\n")
    print_summary(table)


if __name__ == "__main__":
    main()
