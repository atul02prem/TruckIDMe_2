"""How much does resampling to 512 points distort each channel?

`build_windows.resample_window` puts every channel on the same RESIZE_STEPS grid
regardless of its native rate. At a 120 s window that grid is 4.27 Hz, so a 50 Hz
pedal channel is decimated 11.7x with no anti-alias filter, while a 0.93 Hz brake
pressure is interpolated *up* 4.6x. One line of code is reducing one channel and
fabricating another, and nothing had measured either.

**No metric here estimates a sampling rate, deliberately.** An earlier version
reported a native frequency and used it to find spectral energy above the grid's
Nyquist. That was abandoned because the estimate is not well defined:

- the **mean** (count / duration) averages in a channel's silent stretches, reading
  25 Hz for SPN 3030 against a true 50 Hz;
- the **mode** depends on bin width -- SPN 2979's modal gap is 20.0 ms binned to
  0.1 ms and 0.576 ms binned to 1 us, giving 50 Hz or 1736 Hz from one dataset;
- the **median** is sound for a unimodal channel but describes only one of two
  cadences for a channel like SPN 5052, which sends 50 Hz bursts separated by
  100 ms pauses.

The pipeline itself never estimates a rate -- `resample_window` is `np.interp` over
the raw timestamps, whatever their spacing -- so a diagnostic that depends on one
was measuring an artefact of its own estimator. Actual rates live in
`sampling_rate_all_drivers.md`, which computes them once, properly, per driver.

Four metrics, each computed directly from the samples:

- **sample ratio** -- raw samples in the window / RESIZE_STEPS. Above 1 the channel
  is decimated; below 1 it is upsampled and the extra points are invented. This is
  also the rate information, in the units that matter.
- **variance retained** -- std(resampled) / std(raw). Decimation smooths, which
  drops variance. Information lost.
- **anti-alias delta** -- how much the input would move if the grid were low-passed
  before decimating, in units of the raw standard deviation. Measures the decision
  rather than inferring it from a spectrum.
- **round-trip error** -- resample to 512, interpolate back onto the original
  timestamps, RMSE / std(raw). Overall fidelity. Note it compares only at observed
  timestamps, so it cannot see error *inside* a gap, where there is no ground truth.

Round-trip error alone would mislead: for an upsampled channel it is near zero,
because interpolating up and back is almost the identity. Upsampling does not lose
information, it invents it, and only the sample ratio shows that.

**Scope.** Nine drivers, three from each awareness group, over the 53 channels that
survived the exclusion decision. Distortion is a property of a channel's sampling
against the grid rather than of who was driving, so the spread across drivers is
reported as a check on that assumption rather than needing all 46. This report is
the evidence behind DECISIONS.md S3, which then dropped SPN 51 and SPN 3030, taking
the model input to 51 channels.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_resampling_distortion
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import (DATA_PROCESSED, EXCLUDE_DRIVERS, MIN_SAMPLES_PER_WINDOW,
                        OUT_REPORTS, RESIZE_STEPS)
from src.features.build_windows import (audited_channel_spns,
                                        filename_to_driver_id, resample_window,
                                        resolve_channels)
from src.qc.signal_dictionary import load as load_dictionary

REPORT_PATH = OUT_REPORTS / "resampling_distortion.md"
TABLE_PATH = OUT_REPORTS / "resampling_distortion.csv"

WINDOW_LENGTHS: tuple[float, ...] = (30.0, 51.2, 90.0, 120.0)
DRIVERS_PER_GROUP = 3
MAX_WINDOWS = 12          # per driver per window length; distortion is stable across them
OVERSAMPLE = 8            # finer grid used as the anti-aliased reference

# S1's nine exclusions plus S3's three data-quality drops, so this measures the
# channels the model actually receives. The evidence that condemned 51, 3030 and
# 2979 is recorded in S3 with the figures from the run that included them.
EXCLUDED_SPNS: tuple[int, ...] = (51, 515, 2978, 2979, 3030, 3229, 3230, 3231,
                                  3232, 3239, 4154, 5015)

SEVERE_VARIANCE = 0.70    # retaining less than this much variance is severe loss
SEVERE_ANTIALIAS = 0.20   # filtering would move the input this much of a std


def flag(variance_retained: float, antialias: float, ratio: float) -> str:
    """Severity marker for one channel's distortion.

    Args:
        variance_retained: std(resampled) / std(raw).
        antialias: how much filtering would move the input, in units of std.
        ratio: raw samples per resampled point.

    Returns:
        '🔴' severe variance loss, or filtering would change the input materially ·
        '🟡' upsampled, so points are invented · '🟢' faithful.
    """
    if variance_retained < SEVERE_VARIANCE or antialias > SEVERE_ANTIALIAS:
        return "🔴"
    if ratio < 1.0:
        return "🟡"
    return "🟢"


def antialias_delta(times: np.ndarray, values: np.ndarray, start: float,
                    end: float) -> float:
    """How much anti-alias filtering would change what the model sees.

    The pipeline point-samples onto RESIZE_STEPS with `np.interp`. The anti-aliased
    alternative resamples OVERSAMPLE times finer and block-averages each group back
    down to RESIZE_STEPS, which is a low-pass before decimation. The difference
    between the two is precisely what adding a filter would buy.

    Needs no sampling-rate estimate: no Nyquist, no FFT, no bin width.

    Args:
        times: raw sample timestamps within one window.
        values: raw sample values.
        start: window start time.
        end: window end time.

    Returns:
        RMSE between the point-sampled and block-averaged grids, divided by the raw
        standard deviation, or NaN for a window in which the channel never moves.
    """
    raw_std = float(values.std())
    if raw_std <= 0 or np.unique(values).size < 2:
        return float("nan")
    naive = resample_window(times, values, start, end)
    fine = resample_window(times, values, start, end,
                           steps=RESIZE_STEPS * OVERSAMPLE)
    averaged = fine.reshape(RESIZE_STEPS, OVERSAMPLE).mean(axis=1)
    return float(np.sqrt(np.mean((naive - averaged) ** 2)) / raw_std)


def measure_window(times: np.ndarray, values: np.ndarray, start: float,
                   end: float) -> dict[str, float]:
    """All four distortion metrics for one channel in one window.

    Args:
        times: raw timestamps inside the window.
        values: raw values inside the window.
        start: window start time.
        end: window end time.

    Returns:
        The four metrics. Variance, anti-alias delta and round-trip are NaN for a
        window in which the channel never moves, since each divides by the raw
        standard deviation.
    """
    resampled = resample_window(times, values, start, end)
    raw_std = float(values.std())
    back = np.interp(times, np.linspace(start, end, RESIZE_STEPS), resampled)
    # A window where the channel never moves has no variance to retain, and
    # dividing by its near-zero std produces values in the millions. Such a
    # window is undefined for these ratios, not distorted.
    flat = np.unique(values).size < 2 or raw_std <= 0
    return {
        "sample_ratio": times.size / RESIZE_STEPS,
        "variance_retained": float("nan") if flat else float(resampled.std()) / raw_std,
        "antialias_delta": antialias_delta(times, values, start, end),
        "roundtrip_error": float("nan") if flat
        else float(np.sqrt(np.mean((back - values) ** 2)) / raw_std),
    }


def arm_b_drivers() -> list:
    """Three usable drivers from each awareness group.

    Returns:
        Paths to processed CSVs, three per group, chosen deterministically as the
        first three by canonical id so the selection is reproducible.
    """
    files = sorted(DATA_PROCESSED.glob("G*_Subject*.csv"))
    usable = [f for f in files if filename_to_driver_id(f.stem) not in EXCLUDE_DRIVERS]
    chosen = []
    for group in ("G1", "G2", "G3"):
        members = sorted((f for f in usable
                          if filename_to_driver_id(f.stem).startswith(group)),
                         key=lambda f: filename_to_driver_id(f.stem))
        chosen.extend(members[:DRIVERS_PER_GROUP])
    return chosen


def measure_driver(path, channels: dict[int, tuple[str, str]],
                   window_seconds: float) -> list[dict]:
    """Distortion for every channel of one driver at one window length.

    Args:
        path: processed CSV for one driver.
        channels: {spn: (signal column, time column)}.
        window_seconds: window length.

    Returns:
        One record per (channel, window) measured.
    """
    needed = ["canloggerTime"] + [c for pair in channels.values() for c in pair]
    frame = pd.read_csv(path, usecols=sorted(set(needed)))
    clock = frame["canloggerTime"].dropna()
    t0, t1 = float(clock.min()), float(clock.max())
    n_windows = int((t1 - t0) // window_seconds)
    if n_windows < 1:
        return []
    picks = np.linspace(0, n_windows - 1, min(MAX_WINDOWS, n_windows)).astype(int)

    records = []
    for spn, (signal_col, time_col) in channels.items():
        pair = frame[[time_col, signal_col]].dropna().sort_values(time_col)
        all_times = pair[time_col].to_numpy(float)
        all_values = pair[signal_col].to_numpy(float)
        for index in picks:
            start = t0 + index * window_seconds
            inside = (all_times >= start) & (all_times < start + window_seconds)
            if inside.sum() < MIN_SAMPLES_PER_WINDOW:
                continue
            metrics = measure_window(all_times[inside], all_values[inside],
                                     start, start + window_seconds)
            metrics.update({"spn": spn, "driver": filename_to_driver_id(path.stem),
                            "window_seconds": window_seconds})
            records.append(metrics)
    return records


def summarise(records: pd.DataFrame) -> pd.DataFrame:
    """Average each channel's metrics over windows and drivers.

    Args:
        records: one row per (driver, window, channel) measurement.

    Returns:
        One row per (window_seconds, spn) with means and the across-driver spread.
    """
    per_driver = records.groupby(["window_seconds", "spn", "driver"]).mean(
        numeric_only=True).reset_index()
    grouped = per_driver.groupby(["window_seconds", "spn"])
    table = grouped.mean(numeric_only=True).reset_index()
    table["variance_sd_across_drivers"] = grouped["variance_retained"].std().values
    return table


def build_report(table: pd.DataFrame, drivers: list[str],
                 names: dict[int, str]) -> str:
    """Render the distortion measurement as markdown.

    Args:
        table: summarised metrics per (window, channel).
        drivers: canonical ids measured.
        names: SPN to signal description.

    Returns:
        The report as markdown.
    """
    lines = [
        "# Resampling distortion — what the 512-point grid does to each channel",
        "",
        f"**{table.spn.nunique()} channels** × **{len(WINDOW_LENGTHS)} window "
        f"lengths**, measured on **{len(drivers)} drivers** — three from each "
        f"awareness group: {', '.join(drivers)}.",
        "",
        "`RESIZE_STEPS = 512` is fixed, so the window length sets the grid rate and "
        "therefore how violently each channel is resampled.",
        "",
        "| Metric | Meaning |",
        "|---|---|",
        "| sample ratio | raw samples per resampled point. **Below 1 means the "
        "channel is upsampled and the extra points are invented.** Also the rate "
        "information, in the units that matter. |",
        "| variance retained | `std(resampled) / std(raw)` — information lost to "
        "smoothing |",
        "| anti-alias delta | how much the input would move if low-passed before "
        "decimating, in units of the raw std. **Measures the decision directly** |",
        "| round-trip error | resample to 512, interpolate back to the raw "
        "timestamps, RMSE / std(raw) |",
        "",
        f"Flags: 🔴 variance retained < {SEVERE_VARIANCE} or anti-alias delta > "
        f"{SEVERE_ANTIALIAS} · 🟡 upsampled (ratio < 1) · 🟢 faithful.",
        "",
        "## ⚑ No sampling rate is estimated here",
        "",
        "An earlier version reported a native frequency and used it to locate "
        "spectral energy above the grid's Nyquist. That was removed because the "
        "estimate is not well defined: the **mean** averages in silent stretches "
        "(25 Hz for SPN 3030 against a true 50 Hz), the **mode** depends on bin "
        "width (SPN 2979 reads 50 Hz or 1736 Hz from the same data depending on "
        "whether gaps are binned to 0.1 ms or 1 µs), and the **median**, while "
        "sound for a unimodal channel, describes only one of two cadences for a "
        "channel like SPN 5052 that sends 50 Hz bursts separated by 100 ms pauses.",
        "",
        "The pipeline never estimates a rate — `resample_window` is `np.interp` "
        "over the raw timestamps — so a diagnostic depending on one was measuring "
        "its own estimator. Rates are computed properly, per driver, in "
        "`sampling_rate_all_drivers.md`.",
        "",
    ]

    for window in WINDOW_LENGTHS:
        block = table[table.window_seconds == window].copy()
        if not len(block):
            continue
        severe = sum(1 for r in block.itertuples(index=False)
                     if flag(r.variance_retained, r.antialias_delta,
                             r.sample_ratio) == "🔴")
        upsampled = int((block.sample_ratio < 1).sum())
        lines += [
            f"## {window:g} s window — {RESIZE_STEPS / window:.2f} Hz grid",
            "",
            f"**{severe} channels severely distorted · {upsampled} upsampled · "
            f"median variance retained {block.variance_retained.median():.3f} · "
            f"median anti-alias delta {block.antialias_delta.median():.4f}**",
            "",
            "| Flag | SPN | Signal | Ratio | Var retained | Anti-alias Δ | "
            "Round-trip |",
            "|---|--:|---|--:|--:|--:|--:|",
        ]
        for row in block.sort_values("variance_retained").itertuples(index=False):
            lines.append(
                f"| {flag(row.variance_retained, row.antialias_delta, row.sample_ratio)} "
                f"| {row.spn} | `{names.get(row.spn, '')[:40]}` "
                f"| {row.sample_ratio:.2f} | {row.variance_retained:.3f} "
                f"| {row.antialias_delta:.4f} | {row.roundtrip_error:.3f} |")
        lines.append("")

    lines += [
        "## Spread across drivers",
        "",
        "Distortion should be a property of a channel's sampling against the grid, "
        "not of who was driving. The largest across-driver standard deviation in "
        "variance retained is "
        f"**{table.variance_sd_across_drivers.max():.4f}** "
        f"(median {table.variance_sd_across_drivers.median():.4f}). A large value "
        "would mean the measurement depends on the driver and needs all 46.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Measure resampling distortion and write the report."""
    files = arm_b_drivers()
    header = pd.read_csv(files[0], nrows=0).columns.tolist()
    channels_spns = tuple(s for s in audited_channel_spns(header)
                          if s not in EXCLUDED_SPNS)
    channels = resolve_channels(header, channels_spns)
    print(f"channels: {len(channels)} | drivers: "
          f"{', '.join(filename_to_driver_id(f.stem) for f in files)}")

    records = []
    for window_seconds in WINDOW_LENGTHS:
        for path in files:
            records.extend(measure_driver(path, channels, window_seconds))
        print(f"  {window_seconds:g}s done ({len(records)} measurements)")

    table = summarise(pd.DataFrame(records))
    table.to_csv(TABLE_PATH, index=False)

    definitions = load_dictionary()
    names = {spn: (definitions.get(spn) or {}).get("description", "")
             for spn in channels_spns}
    REPORT_PATH.write_text(build_report(
        table, [filename_to_driver_id(f.stem) for f in files], names))

    for window in WINDOW_LENGTHS:
        block = table[table.window_seconds == window]
        severe = sum(1 for r in block.itertuples(index=False)
                     if flag(r.variance_retained, r.antialias_delta,
                             r.sample_ratio) == "🔴")
        print(f"{window:>6g}s grid {RESIZE_STEPS/window:5.2f} Hz | "
              f"severe {severe:>2} | upsampled {int((block.sample_ratio < 1).sum()):>2} | "
              f"var retained {block.variance_retained.median():.3f} | "
              f"antialias {block.antialias_delta.median():.4f}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
