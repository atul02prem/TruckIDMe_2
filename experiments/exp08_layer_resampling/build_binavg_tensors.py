"""Build the Arm B window tensors with bin-averaged resampling.

exp03's tensors resample every channel onto Mantis's 512-point grid with
`np.interp`, which reads the signal *at* 512 instants. For a channel sampled
faster than the grid that is point sampling: the samples between grid points
are discarded and fast content aliases. At 30 s the grid is 17.07 Hz and 30 of
the 50 channels are above it; at 120 s it is 4.27 Hz and 39 are.

Bin averaging divides the window into 512 equal bins and takes the mean of the
raw samples inside each one, which is the correct anti-aliased downsample. A
bin with no sample in it (a channel slower than the grid) is filled by linear
interpolation at the bin centre, exactly as before — nothing can be recovered
there, so slow channels are essentially unchanged.

Everything else is exp03's code path: same channels, same drivers, same window
boundaries, same minimum-samples rule. Only `resample_window` is swapped, so
the two tensors are row-for-row comparable, and `main` asserts that they are.

Output: `data/interim_data/windows_armB_binavg_<w>s.npz`. exp03's tensors are
not touched.

Run:
    python -u -m experiments.exp08_layer_resampling.build_binavg_tensors --window 30
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

import src.features.build_windows as build_windows
from src.config import DATA_INTERIM, RESIZE_STEPS
from src.features.build_tensors import (arm_b_channels, EXCLUDED_SPNS,
                                        tensor_path)

WINDOW_LENGTHS = (30.0, 51.2, 90.0, 120.0)


def binavg_path(window_seconds: float) -> Path:
    """Where one window length's bin-averaged tensor is saved.

    Args:
        window_seconds: window length.

    Returns:
        Path under DATA_INTERIM.
    """
    return DATA_INTERIM / f"windows_armB_binavg_{window_seconds:g}s.npz"


def resample_window_binavg(times: np.ndarray, values: np.ndarray, start: float,
                           end: float, steps: int = RESIZE_STEPS) -> np.ndarray:
    """Resample one channel in one window by averaging within equal bins.

    Args:
        times: sample timestamps (seconds), ascending.
        values: sample values, same length as times.
        start: window start time (seconds).
        end: window end time (seconds).
        steps: number of output points.

    Returns:
        An array of length `steps`: the mean of the samples in each bin, with
        empty bins filled by linear interpolation at the bin centre.
    """
    width = (end - start) / steps
    bins = np.clip(((times - start) / width).astype(int), 0, steps - 1)
    counts = np.bincount(bins, minlength=steps)
    sums = np.bincount(bins, weights=values, minlength=steps)
    centres = start + (np.arange(steps) + 0.5) * width
    out = np.interp(centres, times, values)
    filled = counts > 0
    out[filled] = sums[filled] / counts[filled]
    return out.astype(np.float32)


def main() -> None:
    """Build one window length's bin-averaged tensor and check alignment."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, required=True,
                        choices=WINDOW_LENGTHS)
    arguments = parser.parse_args()

    channels = arm_b_channels()
    if set(channels) & set(EXCLUDED_SPNS):
        raise ValueError("excluded SPNs leaked into the channel set")

    # build_driver_windows looks `resample_window` up in its own module, so
    # replacing it there swaps the resampler and nothing else in exp03's path
    build_windows.resample_window = resample_window_binavg

    started = time.time()
    tensor, drivers, starts, _ = build_windows.build_dataset(
        channels, arguments.window, verbose=False)

    reference = np.load(tensor_path(arguments.window), allow_pickle=True)
    if tensor.shape != reference["X"].shape:
        raise ValueError(f"shape {tensor.shape} != interp {reference['X'].shape}")
    if not (np.array_equal(drivers, reference["driver"])
            and np.allclose(starts, reference["start_time"])):
        raise ValueError("windows are not row-aligned with the interp tensor")

    np.savez_compressed(binavg_path(arguments.window), X=tensor, driver=drivers,
                        start_time=starts,
                        channels=np.asarray([str(s) for s in channels]))
    difference = np.abs(tensor - reference["X"])
    scale = np.abs(reference["X"]).mean(axis=(0, 2)) + 1e-9
    relative = difference.mean(axis=(0, 2)) / scale
    print(f"{arguments.window:g}s {tensor.shape} built in "
          f"{time.time() - started:.0f}s | row-aligned with interp tensor | "
          f"mean relative change per channel: median {np.median(relative):.4f}, "
          f"max {relative.max():.4f} (SPN {channels[int(relative.argmax())]})")


if __name__ == "__main__":
    main()
