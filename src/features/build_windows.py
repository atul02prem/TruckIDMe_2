"""Processed CAN CSVs → a (window, timestep, channel) tensor for the encoder.

Reads native-rate signals straight from `data/processed_data/`, so the MVP path
never depends on the 10 Hz master timeline. Each channel's native samples inside
a window are resampled onto a uniform RESIZE_STEPS grid by linear interpolation
in time — which is what the encoder does to its input anyway.

Windows are non-overlapping and ordered in time per driver, so a downstream
chronological split (train early, test late) stays honest.

Run from the repo root:
    python -m src.features.build_windows
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (DATA_INTERIM, DATA_PROCESSED, EXCLUDE_DRIVERS,
                        MIN_SAMPLES_PER_WINDOW, MVP_CHANNEL_SPNS, OUT_REPORTS,
                        RESIZE_STEPS, WINDOW_SECONDS)

OUT_PATH = DATA_INTERIM / f"windows_{WINDOW_SECONDS}s.npz"
REPORT_PATH = OUT_REPORTS / "windows_build.md"

_DRIVER_RE = re.compile(r"^G(\d+)_Subject(\d+)$")


def filename_to_driver_id(stem: str) -> str:
    """Convert a filename stem to the canonical driver id.

    Args:
        stem: file stem, e.g. 'G1_Subject4'.

    Returns:
        Canonical id, e.g. 'G1S04'.
    """
    match = _DRIVER_RE.match(stem)
    if match is None:
        raise ValueError(f"unexpected driver filename: {stem}")
    return f"G{match.group(1)}S{int(match.group(2)):02d}"


def audited_channel_spns(columns: list[str]) -> tuple[int, ...]:
    """Every CAN signal surviving the audit, i.e. present in processed data.

    `build_processed_data` has already dropped EXCLUDE_SPNS, so any signal column
    with a paired TimeXXX column here is an audited, kept channel.

    Args:
        columns: all column names in a processed driver CSV.

    Returns:
        Sorted SPNs usable as channels.
    """
    spns = []
    for col in columns:
        match = re.match(r"^(\d+)\s", col)
        if match and f"Time{match.group(1)}" in columns:
            spns.append(int(match.group(1)))
    return tuple(sorted(set(spns)))


def resolve_channels(columns: list[str],
                     channel_spns: tuple[int, ...] = MVP_CHANNEL_SPNS
                     ) -> dict[int, tuple[str, str]]:
    """Map each requested SPN to its (value column, time column).

    Args:
        columns: all column names in a processed driver CSV.
        channel_spns: SPNs to resolve.

    Returns:
        {spn: (signal_column, time_column)} for every SPN present with its
        paired TimeXXX column.
    """
    resolved: dict[int, tuple[str, str]] = {}
    for spn in channel_spns:
        signal = next((c for c in columns if re.match(rf"^{spn}\s", c)), None)
        time_col = f"Time{spn}"
        if signal is not None and time_col in columns:
            resolved[spn] = (signal, time_col)
    return resolved


def resample_window(times: np.ndarray, values: np.ndarray,
                    start: float, end: float, steps: int = RESIZE_STEPS) -> np.ndarray:
    """Resample one channel's samples in one window onto a uniform grid.

    Args:
        times: sample timestamps (seconds), ascending.
        values: sample values, same length as times.
        start: window start time (seconds).
        end: window end time (seconds).

    Returns:
        An array of length RESIZE_STEPS, linearly interpolated in time.
    """
    grid = np.linspace(start, end, steps)
    return np.interp(grid, times, values).astype(np.float32)


def build_driver_windows(csv_path: Path,
                         channel_spns: tuple[int, ...] = MVP_CHANNEL_SPNS,
                         window_seconds: float = WINDOW_SECONDS
                         ) -> tuple[np.ndarray, np.ndarray]:
    """Build every full window for one driver.

    Args:
        csv_path: processed CSV for one driver.

    Returns:
        (windows, start_times) where windows has shape
        (n_windows, n_channels, RESIZE_STEPS) — channel-first, as the encoder
        expects — and start_times is per window.
    """
    header = pd.read_csv(csv_path, nrows=0).columns.tolist()
    channels = resolve_channels(header, channel_spns)
    if len(channels) != len(channel_spns):
        missing = sorted(set(channel_spns) - set(channels))
        raise ValueError(f"{csv_path.name}: missing channels {missing}")

    needed = ["canloggerTime"] + [c for pair in channels.values() for c in pair]
    frame = pd.read_csv(csv_path, usecols=sorted(set(needed)))

    clock = frame["canloggerTime"].dropna()
    t0, t1 = float(clock.min()), float(clock.max())
    n_windows = int((t1 - t0) // window_seconds)      # drop the trailing partial

    series = {}
    for spn, (signal_col, time_col) in channels.items():
        pair = frame[[time_col, signal_col]].dropna().sort_values(time_col)
        series[spn] = (pair[time_col].to_numpy(dtype=float),
                       pair[signal_col].to_numpy(dtype=float))

    windows, starts = [], []
    for index in range(n_windows):
        start = t0 + index * window_seconds
        end = start + window_seconds
        channel_stack = []
        for spn in channel_spns:
            times, values = series[spn]
            inside = (times >= start) & (times < end)
            if inside.sum() < MIN_SAMPLES_PER_WINDOW:
                channel_stack = []
                break
            channel_stack.append(resample_window(times[inside], values[inside],
                                                 start, end))
        if channel_stack:
            windows.append(np.stack(channel_stack, axis=0))
            starts.append(start)

    if not windows:
        return np.empty((0, len(channel_spns), RESIZE_STEPS), np.float32), np.empty(0)
    return np.stack(windows), np.asarray(starts)


def build_dataset(channel_spns: tuple[int, ...] = MVP_CHANNEL_SPNS,
                  window_seconds: float = WINDOW_SECONDS, *, verbose: bool = True
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
    """Build the window tensor for every usable driver.

    Args:
        channel_spns: SPNs to use as channels.
        window_seconds: window length in seconds.
        verbose: print per-driver counts.

    Returns:
        (tensor, drivers, start_times, counts_per_driver).
    """
    all_windows, all_drivers, all_starts, counts = [], [], [], {}
    for csv_path in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_path.stem)
        if driver_id in EXCLUDE_DRIVERS:
            continue
        windows, starts = build_driver_windows(csv_path, channel_spns, window_seconds)
        counts[driver_id] = len(windows)
        if verbose:
            print(f"  {driver_id}: {len(windows):>3} windows")
        if len(windows):
            all_windows.append(windows)
            all_starts.append(starts)
            all_drivers.extend([driver_id] * len(windows))
    return (np.concatenate(all_windows).astype(np.float32),
            np.asarray(all_drivers), np.concatenate(all_starts), counts)


def write_report(counts: dict[str, int], total: int) -> Path:
    """Write the per-driver window-count QC report.

    Args:
        counts: windows per driver id.
        total: total windows built.

    Returns:
        The report path.
    """
    low = {d: n for d, n in counts.items() if n < 20}
    lines = [
        f"# Window tensor — {WINDOW_SECONDS}s windows, {len(MVP_CHANNEL_SPNS)} channels",
        "",
        f"Built from `data/processed_data/` at native rates, resampled to "
        f"{RESIZE_STEPS} steps per window.",
        "",
        f"- drivers: **{len(counts)}**",
        f"- windows: **{total}**",
        f"- mean windows/driver: **{total / max(len(counts), 1):.1f}**",
        f"- tensor: `({total}, {len(MVP_CHANNEL_SPNS)}, {RESIZE_STEPS})` float32 "
        f"(channel-first, as the encoder expects)",
        "",
        "## Violations" if low else "## Violations — none",
    ]
    if low:
        lines += ["", "| Flag | Driver | Windows |", "|---|---|---|"]
        lines += [f"| 🔴 | {d} | {n} |" for d, n in sorted(low.items())]
    lines += ["", "## Windows per driver", "", "| Driver | Windows |", "|---|---|"]
    lines += [f"| {d} | {n} |" for d, n in sorted(counts.items())]
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    return REPORT_PATH


def main() -> None:
    """Build the window tensor for every usable driver and save it."""
    tensor, drivers, starts, counts = build_dataset()

    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT_PATH, X=tensor, driver=drivers, start_time=starts,
                        channels=np.asarray([str(s) for s in MVP_CHANNEL_SPNS]))
    print(f"\ntensor {tensor.shape} -> {OUT_PATH}")
    print(f"report -> {write_report(counts, len(tensor))}")


if __name__ == "__main__":
    main()
