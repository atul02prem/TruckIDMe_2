"""Separability of step signals — Cramér's V and mutual information.

η² is the wrong instrument for a step signal. It compares group means, so for a
gear it asks whether drivers occupy different *average gears* — and an average
gear of 4.3 is not a quantity. Every step signal in `all_can_eta2.md` therefore
carries a number that says nothing about it, which is why 12 of them were kept on
an η² near zero that is not evidence of anything.

The right question for a categorical signal is contingency: given the driver, how
predictable is the state? Two statistics answer it, both read off the same
driver × state table:

- **Cramér's V** — association strength, 0 (independent) to 1 (state determines
  driver). An effect size, not a significance test: CAN samples are heavily
  autocorrelated at 10–67 Hz, so a p-value here would be meaningless while an
  effect size stays honest.
- **Theil's U** — the fraction of the signal's own entropy explained by knowing
  the driver. Catches dependence that is not a simple association, and is
  directionally the question we care about.

As with η²: **the statistic flags, physics decides.** A high value means the
signal separates drivers; whether that is behaviour (this driver shifts
differently) or a trip artifact is not something either number can tell.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_step_separability
"""

import numpy as np
import pandas as pd

from src.config import DATA_RAW, EXCLUDE_DRIVERS, EXCLUDE_SPNS, OUT_REPORTS
from src.qc.classify_signals import (classify, driver_id, reviewed_type,
                                     time_coverage)

REPORT_PATH = OUT_REPORTS / "step_separability.md"

LEAK_V = 0.5      # association this strong on a state code is a leak suspect
WATCH_V = 0.3
_SIG_PREFIX = " "


def flag(value: float) -> str:
    """Severity marker for an association strength."""
    if value >= LEAK_V:
        return "🔴"
    if value >= WATCH_V:
        return "🟡"
    return "🟢"


def cramers_v(table: np.ndarray) -> float:
    """Cramér's V for a contingency table.

    Args:
        table: counts, rows = drivers, columns = states.

    Returns:
        Association strength in [0, 1], or NaN if the table is degenerate.
    """
    total = table.sum()
    if total == 0 or min(table.shape) < 2:
        return float("nan")
    expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / total
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum(np.where(expected > 0,
                                  (table - expected) ** 2 / expected, 0.0))
    return float(np.sqrt(chi2 / (total * (min(table.shape) - 1))))


def theils_u(table: np.ndarray) -> float:
    """Fraction of the signal's entropy explained by knowing the driver.

    Args:
        table: counts, rows = drivers, columns = states.

    Returns:
        Value in [0, 1], or NaN if the signal has no entropy to explain.
    """
    total = table.sum()
    if total == 0:
        return float("nan")
    joint = table / total
    p_state = joint.sum(axis=0)
    p_driver = joint.sum(axis=1)

    def entropy(p: np.ndarray) -> float:
        p = p[p > 0]
        return float(-(p * np.log(p)).sum())

    h_state = entropy(p_state)
    if h_state <= 0:
        return float("nan")
    mutual = h_state + entropy(p_driver) - entropy(joint.ravel())
    return float(min(max(mutual / h_state, 0.0), 1.0))


def collect_step_signals() -> tuple[dict[int, str], dict[int, dict[str, dict[float, int]]]]:
    """Find the step signals and count each driver's time in each state.

    Returns:
        (names, counts) where names maps SPN to its column name and counts maps
        SPN -> driver id -> {state value: sample count}.
    """
    files = [p for p in sorted(DATA_RAW.glob("G*_Subject*.csv"))
             if driver_id(p.stem) not in EXCLUDE_DRIVERS]
    header = pd.read_csv(files[0], nrows=0).columns.tolist()
    import re
    signals = {int(m.group(1)): c for c in header
               if (m := re.match(r"^(\d+)\s", c)) and f"Time{m.group(1)}" in header}

    # one cheap pass over a few drivers decides which signals are step at all
    probe = files[:8]
    pooled: dict[int, list[np.ndarray]] = {s: [] for s in signals}
    covers: dict[int, list[float]] = {s: [] for s in signals}
    cols = list(signals.values()) + [f"Time{s}" for s in signals]
    for path in probe:
        frame = pd.read_csv(path, usecols=cols)
        for spn, col in signals.items():
            pooled[spn].append(frame[col].dropna().to_numpy(float))
            cov = time_coverage(frame[f"Time{spn}"].dropna().to_numpy(float))
            if not np.isnan(cov):
                covers[spn].append(cov)

    steps = {}
    for spn, col in signals.items():
        values = np.concatenate(pooled[spn])
        distinct = np.unique(values)
        integral = bool(np.all(np.equal(np.mod(distinct, 1), 0)))
        cov = float(np.mean(covers[spn])) if covers[spn] else float("nan")
        final, _ = reviewed_type(spn, classify(cov, int(distinct.size), integral))
        if final == "step":
            steps[spn] = col
    print(f"step signals: {len(steps)} | counting states over {len(files)} drivers")

    counts: dict[int, dict[str, dict[float, int]]] = {s: {} for s in steps}
    for path in files:
        did = driver_id(path.stem)
        frame = pd.read_csv(path, usecols=list(steps.values()))
        for spn, col in steps.items():
            series = frame[col].dropna()
            counts[spn][did] = series.value_counts().to_dict()
    return steps, counts


def contingency(per_driver: dict[str, dict[float, int]]) -> np.ndarray:
    """Build a driver × state count table.

    Args:
        per_driver: driver id -> {state value: sample count}.

    Returns:
        Counts with rows in driver order and columns in sorted state order.
    """
    states = sorted({v for d in per_driver.values() for v in d})
    return np.array([[per_driver[d].get(s, 0) for s in states]
                     for d in sorted(per_driver)], dtype=float)


def measure(names: dict[int, str],
            counts: dict[int, dict[str, dict[float, int]]]) -> pd.DataFrame:
    """Compute both statistics for every step signal.

    Args:
        names: SPN -> column name.
        counts: SPN -> driver -> {state: count}.

    Returns:
        One row per signal, strongest association first.
    """
    rows = []
    for spn, col in names.items():
        table = contingency(counts[spn])
        rows.append({
            "spn": spn,
            "signal": col,
            "states": table.shape[1],
            "cramers_v": cramers_v(table),
            "theils_u": theils_u(table),
            "excluded": spn in EXCLUDE_SPNS,
        })
    return pd.DataFrame(rows).sort_values("cramers_v", ascending=False)


def write_report(table: pd.DataFrame, n_drivers: int) -> None:
    """Write the step-separability report.

    Args:
        table: one row per step signal.
        n_drivers: how many drivers were counted.
    """
    kept = table[~table["excluded"]]
    leaks = kept[kept["cramers_v"] >= LEAK_V]

    lines = [
        "# Step-signal separability — Cramér's V and mutual information",
        "",
        f"Every **step** signal, counted over **{n_drivers} drivers**. These are "
        "the signals for which η² is the wrong instrument: it compares group "
        "means, so on a gear it asks whether drivers occupy different *average "
        "gears*, and an average gear of 4.3 is not a quantity.",
        "",
        "- **Cramér's V** — association between driver identity and signal state, "
        "0 (independent) to 1 (state determines driver).",
        "- **Theil's U** — share of the signal's own entropy explained by knowing "
        "the driver; catches dependence that is not simple association.",
        "",
        f"Flags: 🔴 V ≥ {LEAK_V} · 🟡 {WATCH_V}–{LEAK_V} · 🟢 < {WATCH_V}. Both are "
        "**effect sizes, not significance tests** — CAN samples are autocorrelated "
        "at 10–67 Hz, so a p-value would be meaningless here while an effect size "
        "stays honest.",
        "",
        "**The statistic flags; physics decides.** A high value says the signal "
        "separates drivers. Whether that is behaviour (this driver shifts "
        "differently) or a trip artifact is not something either number can tell.",
        "",
    ]
    if len(leaks):
        lines += [
            f"## 🔴 Kept signals with strong association — {len(leaks)}",
            "",
            "| Flag | SPN | Signal | States | Cramér's V | Theil's U |",
            "|---|--:|---|--:|--:|--:|",
        ]
        for row in leaks.itertuples(index=False):
            lines.append(f"| {flag(row.cramers_v)} | {row.spn} | `{row.signal}` | "
                         f"{row.states} | {row.cramers_v:.3f} | "
                         f"{row.theils_u:.3f} |")
        lines.append("")
    else:
        lines += [f"## 🟢 No kept step signal reaches V ≥ {LEAK_V}", ""]

    lines += [
        "## All step signals",
        "",
        "| Flag | SPN | Signal | States | Cramér's V | Theil's U | Status |",
        "|---|--:|---|--:|--:|--:|---|",
    ]
    for row in table.itertuples(index=False):
        lines.append(f"| {flag(row.cramers_v)} | {row.spn} | `{row.signal}` | "
                     f"{row.states} | {row.cramers_v:.3f} | {row.theils_u:.3f} | "
                     f"{'EXCLUDED' if row.excluded else 'KEPT'} |")

    lines += [
        "",
        "## Why this report exists",
        "",
        "`all_can_eta2.md` scored every one of the 102 signals with η², including "
        "these. For a step signal that number is not merely imprecise, it is "
        "answering a different question — so the 12 step signals kept on an η² "
        "near zero were not actually cleared by any evidence. This report supplies "
        "the evidence that applies to them.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Measure step-signal separability and write the report."""
    names, counts = collect_step_signals()
    n_drivers = len(next(iter(counts.values())))
    table = measure(names, counts)
    write_report(table, n_drivers)

    worst = table.iloc[0]
    print(f"\nstrongest association: SPN {worst.spn} "
          f"V={worst.cramers_v:.3f} U={worst.theils_u:.3f}")
    print(f"kept signals with V >= {LEAK_V}: "
          f"{int(((~table['excluded']) & (table['cramers_v'] >= LEAK_V)).sum())}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
