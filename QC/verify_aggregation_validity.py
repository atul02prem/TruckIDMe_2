"""Measure how many values linear interpolation fabricates for step signals.

`build_windows.resample_window` calls `np.interp` on every channel regardless of
type. For a continuous signal that is correct. For a step signal — a gear, a mode,
a status flag — it is not: interpolating gear 4 to gear 5 emits 4.37, a state the
transmission was never in and cannot be in.

This script quantifies that. For each step channel it resamples every window
exactly as the pipeline does, then counts the grid values that are **not in the
signal's observed value set**. The result is the "before" number for the typed
aggregation change, and it is measured rather than asserted.

It also computes what the *correct* step features would be (transition count,
dominant-state share), so the report shows what interpolation is destroying and
not merely that it is wrong.

Scope: this reports on the channels actually fed to the models
(`MVP_CHANNEL_SPNS`, read from `data/processed_data/`). It makes no exclusion
recommendation — whether a signal is kept is a separate decision.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_aggregation_validity
"""

import numpy as np
import pandas as pd

from src.config import (DATA_PROCESSED, EXCLUDE_DRIVERS,
                        MIN_SAMPLES_PER_WINDOW, MVP_CHANNEL_SPNS, OUT_REPORTS,
                        WINDOW_SECONDS)
from src.features.build_windows import resample_window, resolve_channels
from src.qc.classify_signals import (classify, driver_id, reviewed_type,
                                     time_coverage)

REPORT_PATH = OUT_REPORTS / "aggregation_validity.md"

MAX_DRIVERS = 8        # enough to establish the defect; the cause is per-channel
VALUE_TOL = 1e-6       # step values are integral, so exact matching is safe
WARN_ILLEGAL = 0.01    # >1% fabricated values is a real defect
FAIL_ILLEGAL = 0.10    # >10% means the channel is mostly fiction


def flag(illegal: float) -> str:
    """Severity marker for a channel's fabricated-value fraction."""
    if illegal >= FAIL_ILLEGAL:
        return "🔴"
    if illegal >= WARN_ILLEGAL:
        return "🟡"
    return "🟢"


def load_channels(csv_path: str) -> tuple[pd.DataFrame, dict[int, tuple[str, str]]]:
    """Read one driver's processed CSV, keeping only the audited channels.

    Args:
        csv_path: processed CSV for one driver.

    Returns:
        (frame, channels) where channels maps SPN -> (signal column, time column).
    """
    header = pd.read_csv(csv_path, nrows=0).columns.tolist()
    channels = resolve_channels(header, MVP_CHANNEL_SPNS)
    needed = ["canloggerTime"] + [c for pair in channels.values() for c in pair]
    frame = pd.read_csv(csv_path, usecols=sorted(set(needed)))
    return frame, channels


def channel_series(frame: pd.DataFrame,
                   channels: dict[int, tuple[str, str]]
                   ) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Extract each channel's (times, values), dropped and time-sorted.

    Mirrors `build_driver_windows` so the windows measured here are the windows
    the pipeline builds.

    Args:
        frame: one driver's processed data.
        channels: SPN -> (signal column, time column).

    Returns:
        SPN -> (times, values).
    """
    series = {}
    for spn, (signal_col, time_col) in channels.items():
        pair = frame[[time_col, signal_col]].dropna().sort_values(time_col)
        series[spn] = (pair[time_col].to_numpy(dtype=float),
                       pair[signal_col].to_numpy(dtype=float))
    return series


def window_starts(frame: pd.DataFrame, window_seconds: float) -> np.ndarray:
    """Window start times for one driver, dropping the trailing partial window.

    Args:
        frame: one driver's processed data, carrying `canloggerTime`.
        window_seconds: window length in seconds.

    Returns:
        Start time of every full window.
    """
    clock = frame["canloggerTime"].dropna()
    t0, t1 = float(clock.min()), float(clock.max())
    count = int((t1 - t0) // window_seconds)
    return t0 + np.arange(count) * window_seconds


def illegal_share(interpolated: np.ndarray, legal: np.ndarray) -> float:
    """Fraction of resampled values that are not in the signal's value set.

    Args:
        interpolated: the resampled grid the encoder receives.
        legal: values this signal was ever observed to take.

    Returns:
        Fraction in [0, 1] of grid points holding a state that cannot exist.
    """
    gaps = np.abs(interpolated[:, None] - legal[None, :])
    return float(np.mean(gaps.min(axis=1) > VALUE_TOL))


def transition_count(values: np.ndarray) -> int:
    """Number of times a step signal actually changed state.

    This is the information linear interpolation destroys and a mean erases: how
    often the driver shifted, engaged lockup, or triggered a mode change.

    Args:
        values: samples inside one window, in time order.

    Returns:
        Count of value changes.
    """
    return int(np.count_nonzero(np.diff(values)))


def dominant_share(values: np.ndarray) -> float:
    """Fraction of a window spent in its single most common state.

    Args:
        values: samples inside one window.

    Returns:
        Share in (0, 1] held by the modal value.
    """
    _, counts = np.unique(values, return_counts=True)
    return float(counts.max() / values.size)


def pool_signals(cached: dict[str, dict[int, tuple[np.ndarray, np.ndarray]]]
                 ) -> tuple[dict[int, str], dict[int, np.ndarray]]:
    """Decide each channel's type and legal value set ONCE, pooled over drivers.

    The pipeline builds one tensor with one type per channel, so the type must be
    a property of the channel rather than of a driver. Deriving it per driver let
    SPN 515 — constant for some drivers, 800 distinct values pooled — appear as a
    step channel, which the pipeline would never treat as one.

    Args:
        cached: driver id -> SPN -> (times, values).

    Returns:
        (types, legal) where types maps SPN to its signal type and legal maps
        SPN to every value the signal was observed to take, across all drivers.
    """
    spns = sorted({spn for per_driver in cached.values() for spn in per_driver})
    types, legal = {}, {}
    for spn in spns:
        values = np.concatenate([cached[d][spn][1] for d in cached
                                 if spn in cached[d]])
        coverages = [time_coverage(cached[d][spn][0]) for d in cached
                     if spn in cached[d]]
        coverages = [c for c in coverages if not np.isnan(c)]
        distinct = np.unique(values)
        integral = bool(np.all(np.equal(np.mod(distinct, 1), 0)))
        coverage = float(np.mean(coverages)) if coverages else float("nan")
        statistical = classify(coverage, int(distinct.size), integral)
        types[spn], _ = reviewed_type(spn, statistical)
        legal[spn] = distinct
    return types, legal


def audit_driver(series: dict[int, tuple[np.ndarray, np.ndarray]],
                 starts: np.ndarray,
                 steps: list[int],
                 legal: dict[int, np.ndarray],
                 names: dict[int, str]) -> list[dict]:
    """Measure interpolation damage for every step channel of one driver.

    Args:
        series: SPN -> (times, values) for this driver.
        starts: window start times for this driver.
        steps: the SPNs classified step, decided pooled over all drivers.
        legal: SPN -> values the signal takes anywhere in the dataset.
        names: SPN -> signal column name.

    Returns:
        One row per (channel, window) that the pipeline would have built.
    """
    rows = []
    for start in starts:
        end = start + WINDOW_SECONDS
        for spn in steps:
            times, values = series[spn]
            inside = (times >= start) & (times < end)
            if inside.sum() < MIN_SAMPLES_PER_WINDOW:
                continue
            grid = resample_window(times[inside], values[inside], start, end)
            rows.append({
                "spn": spn,
                "signal": names[spn],
                "illegal": illegal_share(grid, legal[spn]),
                "transitions": transition_count(values[inside]),
                "dominant": dominant_share(values[inside]),
                "n_legal": int(legal[spn].size),
            })
    return rows


def summarise(rows: list[dict]) -> pd.DataFrame:
    """Aggregate per-window measurements to one row per channel.

    Args:
        rows: per (channel, window) measurements.

    Returns:
        One row per channel, worst channels first.
    """
    frame = pd.DataFrame(rows)
    grouped = frame.groupby(["spn", "signal"], as_index=False).agg(
        windows=("illegal", "size"),
        mean_illegal=("illegal", "mean"),
        max_illegal=("illegal", "max"),
        windows_affected=("illegal", lambda s: float((s > 0).mean())),
        mean_transitions=("transitions", "mean"),
        mean_dominant=("dominant", "mean"),
        n_legal=("n_legal", "first"),
    )
    return grouped.sort_values("mean_illegal", ascending=False)


def write_report(table: pd.DataFrame, n_drivers: int) -> None:
    """Write the aggregation-validity report.

    Args:
        table: one row per step channel.
        n_drivers: how many drivers were measured.
    """
    violations = table[table["mean_illegal"] >= WARN_ILLEGAL]
    moving = table[table["mean_transitions"] > 0]

    lines = [
        "# Aggregation validity — what linear interpolation does to step signals",
        "",
        f"Measured over **{n_drivers} drivers**, {WINDOW_SECONDS}s windows, on the "
        f"**{len(table)} step channels** among the {len(MVP_CHANNEL_SPNS)} audited "
        "channels fed to the models. Windows are built exactly as "
        "`build_windows.build_driver_windows` builds them, and the resampling is "
        "`build_windows.resample_window` itself, imported — this measures the "
        "shipping code, not a reimplementation.",
        "",
        "**Legal values** are the values each signal was observed to take "
        "anywhere in this dataset. A resampled point is counted illegal when it "
        "matches none of them: a state the vehicle was never in.",
        "",
        "Signal types and legal value sets are decided **once, pooled over all "
        "drivers measured** — not per driver. The pipeline builds one tensor with "
        "one type per channel, so a type must be a property of the channel. "
        "Deriving it per driver let SPN 515 (constant for some drivers, 800 "
        "distinct values pooled) appear as a step channel.",
        "",
    ]

    if len(violations):
        lines += [
            f"## 🔴 Violations — {len(violations)} of {len(table)} step channels "
            "receive fabricated states",
            "",
            "| Flag | SPN | Signal | Legal values | Mean illegal | Worst window | "
            "Windows affected |",
            "|---|--:|---|--:|--:|--:|--:|",
        ]
        for row in violations.itertuples(index=False):
            lines.append(
                f"| {flag(row.mean_illegal)} | {row.spn} | `{row.signal}` | "
                f"{row.n_legal} | {row.mean_illegal:.1%} | {row.max_illegal:.1%} | "
                f"{row.windows_affected:.1%} |")
        lines += [
            "",
            "Every percentage above is a share of the 512 numbers per window that "
            "the encoder reads as a vehicle state which never existed.",
            "",
        ]
    else:
        lines += ["## 🟢 No violations", "",
                  "No step channel received a fabricated value above the "
                  f"{WARN_ILLEGAL:.0%} threshold.", ""]

    lines += [
        "## All step channels",
        "",
        "| Flag | SPN | Signal | Legal values | Windows | Mean illegal | "
        "Transitions/window | Time in modal state |",
        "|---|--:|---|--:|--:|--:|--:|--:|",
    ]
    for row in table.itertuples(index=False):
        lines.append(
            f"| {flag(row.mean_illegal)} | {row.spn} | `{row.signal}` | "
            f"{row.n_legal} | {row.windows} | {row.mean_illegal:.1%} | "
            f"{row.mean_transitions:.2f} | {row.mean_dominant:.1%} |")

    lines += [
        "",
        "## What the correct features would be",
        "",
        "The last two columns are the information interpolation and averaging "
        "destroy. A step signal's behaviour is *when and how often it changed*, "
        "not its level:",
        "",
        f"- **{len(moving)} of {len(table)} step channels actually change state** "
        "within a window. For those, `transitions/window` is a direct behavioural "
        "measure — how often this driver shifted, or engaged torque-converter "
        "lockup — and it survives no averaging.",
        "- `time in modal state` is the complementary measure: a driver who holds "
        "one gear differs from one who hunts between two, even with the same mean.",
        "",
        "Correct handling per the taxonomy in `signal_classification.md`: repeat "
        "the previous value (ZOH) rather than interpolate, and summarise a window "
        "by transition count, time-in-state fractions and mode — never a mean.",
        "",
        "## Caveat",
        "",
        "Window counts here may differ slightly from the full pipeline build. "
        "`build_driver_windows` drops a window when *any* of the "
        f"{len(MVP_CHANNEL_SPNS)} channels has fewer than "
        f"{MIN_SAMPLES_PER_WINDOW} native samples in it, whereas this script "
        "evaluates each step channel independently. That affects how many windows "
        "are counted, not the per-window illegal fraction being measured.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Measure interpolation damage across drivers and write the report."""
    files = [p for p in sorted(DATA_PROCESSED.glob("G*_Subject*.csv"))
             if driver_id(p.stem) not in EXCLUDE_DRIVERS][:MAX_DRIVERS]

    cached, starts, names = {}, {}, {}
    for path in files:
        frame, channels = load_channels(path)
        did = driver_id(path.stem)
        cached[did] = channel_series(frame, channels)
        starts[did] = window_starts(frame, WINDOW_SECONDS)
        names.update({spn: col for spn, (col, _) in channels.items()})
        print(f"  read {did}: {len(starts[did])} windows")

    types, legal = pool_signals(cached)
    steps = [spn for spn, kind in types.items() if kind == "step"]
    print(f"\npooled types: " + ", ".join(
        f"{k}={sum(1 for v in types.values() if v == k)}"
        for k in ("continuous", "step", "event")))

    rows: list[dict] = []
    for did in cached:
        rows += audit_driver(cached[did], starts[did], steps, legal, names)

    table = summarise(rows)
    write_report(table, len(files))

    worst = table.iloc[0]
    print(f"step channels measured: {len(table)}")
    print(f"channels with fabricated values: "
          f"{int((table['mean_illegal'] >= WARN_ILLEGAL).sum())}")
    print(f"worst: SPN {worst.spn} at {worst.mean_illegal:.1%} illegal")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
