"""Value distribution and per-driver constancy for every CAN signal.

Two questions that no separability statistic answers, both of which have already
overturned a proposed verdict:

1. **What values does this signal actually hold, and in what proportion?**
   SPN 4154 was assumed constant once its null sentinels were removed. It is not:
   it varies for all 46 drivers across 4 values, none of which lie in the
   0-0.875% range its own data dictionary defines.

2. **Does it vary for every driver, or only for some?**
   SPN 515 holds one value for 99.22% of samples and never moves at all in 9 of
   the 46 drives. "Does this signal vary in this recording" is then a per-driver
   binary splitting the cohort 9 against 37 -- a partial driver label.

**Why this screens all 102 signals rather than a shortlist.** An earlier version
measured only the two signals above, chosen because their proposed verdicts
rested on unverified claims. That is selection by accident, not by criterion.
Per-driver constancy is a leak mechanism that every other instrument is blind to:
eta-squared, Cramer's V, Theil's U and mutual information all pool samples across
drivers, so a signal that is flat in some drives and active in others shows them
nothing. `classify_signals.py` reports signals constant across *every* driver;
nothing reported the *partial* case until this script did.

A near-constant signal is not a constant one, and a signal constant for *some*
drivers is a different problem from one constant for all.

Cited by `outputs/reports/signal_exclusion_decisions.md`.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_signal_value_distributions
"""
from __future__ import annotations

import re

import pandas as pd

from src.config import DATA_RAW, EXCLUDE_DRIVERS, OUT_REPORTS

TOP_VALUES = 10            # values listed individually before the tail is pooled
DOMINANT_SHARE = 0.95      # one value holding this much of a drive is near-constant
DETAIL_MAX_DISTINCT = 64   # above this a value table says nothing; summary only

REPORT_PATH = OUT_REPORTS / "signal_value_distributions.md"
_SIGNAL_RE = re.compile(r"^(\d+)\s")


def canonical_id(stem: str) -> str:
    """Canonical driver id from a CSV filename stem.

    Args:
        stem: file stem, e.g. 'G1_Subject4'.

    Returns:
        Canonical id, e.g. 'G1S04'.
    """
    group, number = stem.replace("G", "").split("_Subject")
    return f"G{group}S{int(number):02d}"


def usable_driver_files() -> list:
    """List the raw CSVs for drivers not excluded by config.

    Returns:
        Sorted list of Path, one per usable driver.
    """
    files = sorted(DATA_RAW.glob("G*_Subject*.csv"))
    return [f for f in files if canonical_id(f.stem) not in EXCLUDE_DRIVERS]


def signal_columns(path) -> dict[int, str]:
    """Find every CAN signal column that has a paired timestamp column.

    Args:
        path: any raw driver CSV.

    Returns:
        SPN to signal column name.
    """
    header = pd.read_csv(path, nrows=0).columns.tolist()
    return {int(m.group(1)): c for c in header
            if (m := _SIGNAL_RE.match(c)) and f"Time{m.group(1)}" in header}


def scan(*, files: list, columns: dict[int, str]) -> tuple[dict, dict]:
    """Measure value counts and per-driver constancy, one pass per driver.

    Pooled value counts are kept only while a signal stays below
    DETAIL_MAX_DISTINCT; past that the signal is marked high-cardinality and its
    counts dropped, so a 65k-value continuous channel cannot exhaust memory.

    Args:
        files: raw CSV paths, one per driver.
        columns: SPN to signal column name.

    Returns:
        (pooled, per_driver) where pooled maps SPN to {value: count} or None for
        a high-cardinality signal, and per_driver maps SPN to a list of
        (driver_id, n_distinct, dominant_share) one entry per driver.
    """
    pooled: dict[int, dict[float, int] | None] = {spn: {} for spn in columns}
    per_driver: dict[int, list[tuple[str, int, float]]] = {spn: [] for spn in columns}

    for path in files:
        did = canonical_id(path.stem)
        frame = pd.read_csv(path, usecols=list(columns.values()))
        for spn, column in columns.items():
            counts = frame[column].dropna().value_counts()
            if counts.empty:
                continue
            total = int(counts.sum())
            per_driver[spn].append(
                (did, int(counts.size), float(counts.iloc[0]) / total))
            bucket = pooled[spn]
            if bucket is None:
                continue
            for value, n in counts.items():
                bucket[value] = bucket.get(value, 0) + int(n)
            if len(bucket) > DETAIL_MAX_DISTINCT:
                pooled[spn] = None
        print(f"  {did}")

    return pooled, per_driver


def summarise(spn: int, column: str,
              rows: list[tuple[str, int, float]]) -> dict:
    """Reduce one signal's per-driver measurements to a single summary row.

    Args:
        spn: the signal's SPN.
        column: signal column name.
        rows: (driver_id, n_distinct, dominant_share) per driver.

    Returns:
        Summary fields including the drivers for which the signal never changed.
    """
    constant = sorted(did for did, distinct, _ in rows if distinct == 1)
    distincts = [d for _, d, _ in rows]
    dominants = [s for _, _, s in rows]
    return {
        "spn": spn,
        "signal": column,
        "drivers": len(rows),
        "n_constant": len(constant),
        "constant_in": constant,
        "min_distinct": min(distincts) if distincts else 0,
        "max_distinct": max(distincts) if distincts else 0,
        "mean_dominant": sum(dominants) / len(dominants) if dominants else float("nan"),
    }


def flag_for(row: dict) -> str:
    """Severity marker for one signal's distribution.

    Args:
        row: a summary row from `summarise`.

    Returns:
        '🔴' constant for every driver · '🟡' constant for only some, or
        near-constant everywhere · '🟢' varies normally.
    """
    if row["drivers"] and row["n_constant"] == row["drivers"]:
        return "🔴"
    if row["n_constant"] > 0 or row["mean_dominant"] >= DOMINANT_SHARE:
        return "🟡"
    return "🟢"


def section_header(n_signals: int, n_drivers: int) -> list[str]:
    """Title, scope, and what this report is for.

    Args:
        n_signals: signals screened.
        n_drivers: drivers measured.

    Returns:
        Report lines.
    """
    return [
        "# Value distributions and per-driver constancy — all CAN signals",
        "",
        f"**All {n_signals} CAN signals over {n_drivers} drivers**, raw data.",
        "",
        "Flags: 🔴 constant for every driver · 🟡 constant for **only some** "
        f"drivers, or one value holding ≥ {DOMINANT_SHARE:.0%} of a typical "
        "drive · 🟢 varies normally.",
        "",
        "**This report measures only** — no exclusion labels, no recommendation. "
        "The decisions that cite it live in `signal_exclusion_decisions.md`.",
        "",
        "## Why no other instrument can answer this",
        "",
        "η², Cramér's V, Theil's U and mutual information all pool samples "
        "across drivers to ask whether drivers differ. None of them can ask "
        "whether a signal *moved at all* in a given drive. A signal that is flat "
        "in some recordings and active in others carries a driver split in its "
        "mere variability — SPN 515 splits this cohort **9 against 37** — and "
        "that split is invisible to every pooled effect size, including the "
        "within-window spread column added to the continuous report.",
        "",
        "`classify_signals.py` reports the signals constant across *every* "
        "driver. The **partial** case is reported only here.",
        "",
    ]


def section_partial(table: pd.DataFrame) -> list[str]:
    """Violations first: the signals constant for only some drivers.

    Args:
        table: all summary rows.

    Returns:
        Report lines.
    """
    partial = table[(table.n_constant > 0) & (table.n_constant < table.drivers)]
    partial = partial.sort_values("n_constant", ascending=False)
    if not len(partial):
        return ["## 🟢 No signal is constant for only some drivers",
                "",
                "Every signal either varies in every drive or in none. The "
                "mechanism this report exists to detect is absent — recorded as "
                "a negative result.",
                ""]

    lines = [
        f"## 🟡 Constant for only some drivers — {len(partial)} signals",
        "",
        "For each of these, *whether the signal varies* is itself a per-driver "
        "label. This is the mechanism no pooled statistic can see.",
        "",
        "| Flag | SPN | Signal | Constant in | Split | Distinct (min–max) |",
        "|---|--:|---|--:|---|--:|",
    ]
    for row in partial.itertuples(index=False):
        lines.append(
            f"| 🟡 | {row.spn} | `{row.signal}` | {row.n_constant}/{row.drivers} | "
            f"{row.n_constant} vs {row.drivers - row.n_constant} | "
            f"{row.min_distinct}–{row.max_distinct} |")
    lines.append("")
    for row in partial.itertuples(index=False):
        lines.append(f"- **SPN {row.spn}** constant in: "
                     f"{', '.join(row.constant_in)}")
    lines.append("")
    return lines


def section_near_constant(table: pd.DataFrame) -> list[str]:
    """The signals one value dominates without being formally constant.

    Args:
        table: all summary rows.

    Returns:
        Report lines.
    """
    near = table[(table.mean_dominant >= DOMINANT_SHARE)
                 & (table.n_constant < table.drivers)]
    near = near.sort_values("mean_dominant", ascending=False)
    if not len(near):
        return []
    lines = [
        f"## 🟡 Near-constant — {len(near)} signals hold one value "
        f"≥ {DOMINANT_SHARE:.0%} of a typical drive",
        "",
        "Not zero-variance, so every separability statistic is defined on them, "
        "but the information they carry is concentrated in a small fraction of "
        "samples.",
        "",
        "| Flag | SPN | Signal | Mean dominant share | Constant in | "
        "Distinct (min–max) |",
        "|---|--:|---|--:|--:|--:|",
    ]
    for row in near.itertuples(index=False):
        lines.append(
            f"| 🟡 | {row.spn} | `{row.signal}` | {100 * row.mean_dominant:.2f}% | "
            f"{row.n_constant}/{row.drivers} | "
            f"{row.min_distinct}–{row.max_distinct} |")
    lines.append("")
    return lines


def section_screen(table: pd.DataFrame) -> list[str]:
    """The full screen: every signal, one row each.

    Args:
        table: all summary rows.

    Returns:
        Report lines.
    """
    ordered = table.sort_values(["n_constant", "mean_dominant"], ascending=False)
    lines = [
        "## All signals",
        "",
        "| Flag | SPN | Signal | Drivers | Constant in | Distinct (min–max) | "
        "Mean dominant |",
        "|---|--:|---|--:|--:|--:|--:|",
    ]
    for row in ordered.itertuples(index=False):
        lines.append(
            f"| {flag_for(row._asdict())} | {row.spn} | `{row.signal}` | "
            f"{row.drivers} | {row.n_constant} | "
            f"{row.min_distinct}–{row.max_distinct} | "
            f"{100 * row.mean_dominant:.2f}% |")
    lines.append("")
    return lines


def section_detail(table: pd.DataFrame,
                   pooled: dict[int, dict[float, int] | None]) -> list[str]:
    """Full value tables for the flagged, low-cardinality signals.

    Args:
        table: all summary rows.
        pooled: SPN to pooled value counts, or None if high-cardinality.

    Returns:
        Report lines.
    """
    flagged = table[table.apply(lambda r: flag_for(r.to_dict()) != "🟢", axis=1)]
    lines = ["## Value tables — flagged signals", "",
             "Only signals with at most "
             f"{DETAIL_MAX_DISTINCT} distinct values appear here; above that a "
             "value table carries no information.", ""]
    shown = 0
    for row in flagged.sort_values("spn").itertuples(index=False):
        counts = pooled.get(row.spn)
        if not counts:
            continue
        shown += 1
        total = sum(counts.values())
        ranked = sorted(counts.items(), key=lambda kv: -kv[1])
        lines += [f"### SPN {row.spn} — `{row.signal}`", "",
                  f"{len(counts)} distinct values · {total:,} samples",
                  "", "| Value | Samples | Share |", "|--:|--:|--:|"]
        for value, n in ranked[:TOP_VALUES]:
            lines.append(f"| `{value}` | {n:,} | {100 * n / total:.4f}% |")
        if len(ranked) > TOP_VALUES:
            tail = sum(n for _, n in ranked[TOP_VALUES:])
            lines.append(f"| _{len(ranked) - TOP_VALUES} further values_ | "
                         f"{tail:,} | {100 * tail / total:.4f}% |")
        lines.append("")
    if not shown:
        lines.append("_No flagged signal is low-cardinality enough to tabulate._")
        lines.append("")
    return lines


def build_report(table: pd.DataFrame,
                 pooled: dict[int, dict[float, int] | None],
                 n_drivers: int) -> str:
    """Assemble the report from its sections, in reading order.

    Args:
        table: all summary rows.
        pooled: SPN to pooled value counts, or None if high-cardinality.
        n_drivers: drivers measured.

    Returns:
        The report as markdown.
    """
    return "\n".join(
        section_header(len(table), n_drivers)
        + section_partial(table)
        + section_near_constant(table)
        + section_screen(table)
        + section_detail(table, pooled)) + "\n"


def main() -> None:
    """Screen every CAN signal for value distribution and per-driver constancy."""
    files = usable_driver_files()
    columns = signal_columns(files[0])
    print(f"signals: {len(columns)} | scanning {len(files)} drivers")

    pooled, per_driver = scan(files=files, columns=columns)
    table = pd.DataFrame([summarise(spn, col, per_driver[spn])
                          for spn, col in columns.items()])

    REPORT_PATH.write_text(build_report(table, pooled, len(files)))

    partial = table[(table.n_constant > 0) & (table.n_constant < table.drivers)]
    print(f"\nconstant for ALL drivers:          "
          f"{int((table.n_constant == table.drivers).sum())}")
    print(f"constant for SOME drivers (🟡):     {len(partial)}")
    for row in partial.sort_values("n_constant", ascending=False).itertuples(index=False):
        print(f"    SPN {row.spn}: constant in {row.n_constant}/{row.drivers} "
              f"({row.signal[:46]})")
    print(f"near-constant (≥{DOMINANT_SHARE:.0%} one value): "
          f"{int(((table.mean_dominant >= DOMINANT_SHARE) & (table.n_constant < table.drivers)).sum())}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
