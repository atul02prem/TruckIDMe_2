"""Measure what linear interpolation fabricates in step signals — 50 channels, 4 windows.

Supersedes `verify_aggregation_validity.py` for the model input. That script ran
on the earlier 62-channel set, at 120 s only, on 8 drivers. The model now reads
the 50 channels of `src/features/build_tensors.py`, and the headline window is
30 s, so the 120 s number did not cover the configuration being reported.

This script keeps the earlier method unchanged — it imports every measuring
function rather than copying it — and changes only the scope:

| | earlier | here |
|---|---|---|
| channels | 62 (`MVP_CHANNEL_SPNS`) | 50 (`build_tensors.arm_b_channels`) |
| windows | 120 s | 30 / 51.2 / 90 / 120 s |
| drivers | 8 | all 46 usable |
| resampling | `np.interp` | `np.interp` (unchanged) |

Signal types and legal value sets are decided once, pooled over all 46 drivers,
so every window length is judged against the same definition of a legal state.

The earlier report is kept: it is the evidence for excluding SPN 2979, which is
not among the 50 channels and so cannot appear here.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_aggregation_validity_50ch
"""

import pandas as pd

from src.config import DATA_PROCESSED, EXCLUDE_DRIVERS, OUT_REPORTS
from src.features.build_tensors import WINDOW_LENGTHS, arm_b_channels
from src.qc.classify_signals import driver_id
from QC.verify_aggregation_validity import (WARN_ILLEGAL, audit_driver,
                                            channel_series, flag,
                                            load_channels, pool_signals,
                                            summarise, window_starts)

REPORT_PATH = OUT_REPORTS / "aggregation_validity_50ch.md"


def read_drivers(channel_spns: tuple[int, ...]) -> tuple[dict, dict, dict]:
    """Read every usable driver's channels once.

    Args:
        channel_spns: the SPNs to read.

    Returns:
        (series, frames, names): driver -> SPN -> (times, values); driver ->
        the frame used for window starts; SPN -> signal column name.
    """
    files = [p for p in sorted(DATA_PROCESSED.glob("G*_Subject*.csv"))
             if driver_id(p.stem) not in EXCLUDE_DRIVERS]
    series, frames, names = {}, {}, {}
    for path in files:
        frame, channels = load_channels(path, channel_spns=channel_spns)
        did = driver_id(path.stem)
        series[did] = channel_series(frame, channels)
        frames[did] = frame[["canloggerTime"]]
        names.update({spn: col for spn, (col, _) in channels.items()})
        print(f"  read {did}")
    return series, frames, names


def audit_window(series: dict, frames: dict, steps: list[int], legal: dict,
                 names: dict, window_seconds: float) -> pd.DataFrame:
    """Measure every step channel at one window length, over all drivers.

    Args:
        series: driver -> SPN -> (times, values).
        frames: driver -> frame carrying `canloggerTime`.
        steps: SPNs classified step, pooled over all drivers.
        legal: SPN -> every value the signal takes in the dataset.
        names: SPN -> signal column name.
        window_seconds: window length in seconds.

    Returns:
        One row per step channel, from `summarise`.
    """
    rows: list[dict] = []
    for did in series:
        starts = window_starts(frames[did], window_seconds)
        rows += audit_driver(series[did], starts, steps, legal, names,
                             window_seconds=window_seconds)
    return summarise(rows)


def write_report(tables: dict[float, pd.DataFrame], type_counts: dict[str, int],
                 n_drivers: int, n_channels: int) -> None:
    """Write the 50-channel, four-window report.

    Args:
        tables: window length -> per-channel table.
        type_counts: signal type -> number of the model's channels of that type.
        n_drivers: drivers measured.
        n_channels: channels in the model input.
    """
    windows = list(tables)
    spns = tables[windows[0]][["spn", "signal"]].values.tolist()
    worst = {w: tables[w]["mean_illegal"].max() for w in windows}
    violating = [w for w in windows if worst[w] >= WARN_ILLEGAL]

    lines = [
        "# Aggregation validity — step signals in the 50-channel model input",
        "",
        "> Supersedes `aggregation_validity.md` for the model input. That report "
        "measured the earlier 62-channel set at 120 s on 8 drivers, and remains "
        "the evidence for excluding SPN 2979.",
        "",
        f"**{n_channels} channels** x **{len(windows)} window lengths**, all "
        f"**{n_drivers} drivers**, resampled with `np.interp` exactly as "
        "`build_windows.resample_window` does.",
        "",
        "Signal types among the model's channels, pooled over all drivers: "
        + ", ".join(f"**{k} {v}**" for k, v in type_counts.items()) + ". "
        "Only step channels can receive an illegal value; a continuous "
        "channel has no forbidden values between its samples.",
        "",
        "A resampled point is **illegal** when it matches no value the signal "
        "takes anywhere in the dataset — a state the vehicle was never in.",
        "",
        "Flags: 🔴 mean illegal ≥ 10% · 🟡 ≥ 1% · 🟢 below 1%.",
        "",
    ]

    if violating:
        lines += [f"## 🔴 Violations at {len(violating)} of {len(windows)} "
                  "window lengths", ""]
        for w in violating:
            bad = tables[w][tables[w]["mean_illegal"] >= WARN_ILLEGAL]
            for row in bad.itertuples(index=False):
                lines.append(f"- {flag(row.mean_illegal)} {w:g} s, SPN "
                             f"{row.spn}: {row.mean_illegal:.1%} illegal")
        lines.append("")
    else:
        lines += ["## 🟢 No violations", "",
                  f"No step channel exceeds {WARN_ILLEGAL:.0%} illegal values at "
                  "any window length.", ""]

    lines += [
        "## Mean illegal share, by window length",
        "",
        "| SPN | Signal | " + " | ".join(f"{w:g} s" for w in windows) + " |",
        "|--:|---|" + "--:|" * len(windows),
    ]
    for spn, signal in spns:
        cells = []
        for w in windows:
            value = tables[w].set_index("spn").loc[spn, "mean_illegal"]
            cells.append(f"{flag(value)} {value:.2%}")
        lines.append(f"| {spn} | `{signal}` | " + " | ".join(cells) + " |")

    for w in windows:
        lines += [
            "",
            f"## {w:g} s window",
            "",
            "| Flag | SPN | Signal | Legal values | Windows | Mean illegal | "
            "Worst window | Windows affected | Transitions/window | "
            "Time in modal state |",
            "|---|--:|---|--:|--:|--:|--:|--:|--:|--:|",
        ]
        for row in tables[w].itertuples(index=False):
            lines.append(
                f"| {flag(row.mean_illegal)} | {row.spn} | `{row.signal}` | "
                f"{row.n_legal} | {row.windows} | {row.mean_illegal:.2%} | "
                f"{row.max_illegal:.1%} | {row.windows_affected:.1%} | "
                f"{row.mean_transitions:.2f} | {row.mean_dominant:.1%} |")

    lines += [
        "",
        "## Limitations",
        "",
        "- Illegal share measures one failure only: values between two states. "
        "It does not measure the transition being smeared in time, which "
        "interpolation also does.",
        "- Window counts can differ slightly from the tensors: the pipeline "
        "drops a window when *any* channel is too sparse, while this script "
        "judges each step channel on its own. The per-window share is "
        "unaffected.",
        "- Continuous channels are measured separately, in "
        "`resampling_distortion.md`.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Measure interpolation damage on the model's step channels at every window."""
    channel_spns = arm_b_channels()
    series, frames, names = read_drivers(channel_spns)

    types, legal = pool_signals(series)
    steps = [spn for spn, kind in types.items() if kind == "step"]
    type_counts = {k: sum(1 for v in types.values() if v == k)
                   for k in ("continuous", "step", "event")}
    print(f"\n{len(channel_spns)} channels: {type_counts} | step SPNs {steps}")

    tables = {}
    for w in WINDOW_LENGTHS:
        tables[w] = audit_window(series, frames, steps, legal, names, w)
        print(f"  {w:g} s: worst SPN {tables[w].iloc[0].spn} at "
              f"{tables[w].iloc[0].mean_illegal:.2%} illegal")

    write_report(tables, type_counts, len(series), len(channel_spns))
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
