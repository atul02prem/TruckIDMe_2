"""Step 1b: verify the built tensors against their source before embedding.

`verify_resampling_distortion.py` measures the resampling *operation* — it reads
`data/processed_data/` and calls the same `resample_window` the pipeline uses. That
characterises the operation but cannot confirm that the saved `.npz` actually
contains it. A fault in `build_driver_windows`' windowing, in the channel ordering,
or in the write itself would pass unnoticed.

So this reads the artefacts and checks them:

1. **Channel order** matches the 50 expected SPNs exactly, in order. A silent
   reordering would mis-label every channel downstream while every shape still
   looked right.
2. **No excluded SPN is present.** Guards the failure that put SPN 2979 into a
   53-channel tensor: a decision recorded in DECISIONS.md but not reflected in the
   list a build script reads.
3. **No NaN or infinity**, which would propagate silently through the encoder.
4. **Shape and coverage** — `(n_windows, 50, 512)`, all 46 usable drivers present,
   every driver holding at least one window.
5. **Spot-check against raw.** For sampled (driver, window, channel) triples, the
   raw samples are pulled from `processed_data`, `resample_window` is applied to
   them, and the result is compared to the stored column. These must match
   *exactly* — same function, same inputs — so any mismatch is a windowing or
   indexing fault, not a tolerance question.

Check 5 is the one that makes "we verified the tensors" literally true.

Run from the repo root in the `truckidme` env, after build_tensors.py:
    python -m QC.verify_tensors
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (DATA_PROCESSED, EXCLUDE_DRIVERS, MIN_SAMPLES_PER_WINDOW,
                        OUT_REPORTS, RESIZE_STEPS)
from src.features.build_windows import (filename_to_driver_id, resample_window,
                                        resolve_channels)
from src.features.build_tensors import (EXCLUDED_SPNS, WINDOW_LENGTHS,
                                        arm_b_channels, tensor_path)

REPORT_PATH = OUT_REPORTS / "tensor_verification.md"

SPOT_DRIVERS = 3          # drivers sampled for the exact comparison
SPOT_WINDOWS = 3          # windows per sampled driver
SPOT_CHANNELS = 5         # channels per sampled window
SPOT_SEED = 0


def expected_drivers() -> set[str]:
    """The driver ids a complete tensor should cover.

    Returns:
        Canonical ids of every usable driver.
    """
    return {filename_to_driver_id(p.stem)
            for p in DATA_PROCESSED.glob("G*_Subject*.csv")
            if filename_to_driver_id(p.stem) not in EXCLUDE_DRIVERS}


def check_structure(bundle, channels: tuple[int, ...]) -> list[tuple[str, bool, str]]:
    """Channel order, exclusions, finiteness, shape and driver coverage.

    Args:
        bundle: the loaded `.npz`.
        channels: the SPNs the tensor should carry, in order.

    Returns:
        (check name, passed, detail) per check.
    """
    stored = [int(c) for c in bundle["channels"]]
    #print(f"  {bundle['X'].shape} tensor, {len(stored)} channels, " f"{len(set(bundle['driver']))} drivers")
    #print(stored)
    tensor = bundle["X"] #prints spn list
    #print(f"  {tensor.shape} tensor, {len(stored)} channels, {len(set(bundle['driver']))} drivers")   (3876, 50, 512) tensor, 50 channels, 46 drivers
    drivers = bundle["driver"]
    present, missing = set(drivers), expected_drivers() - set(drivers)
    counts = pd.Series(drivers).value_counts()
    leaked = sorted(set(stored) & set(EXCLUDED_SPNS))

    return [
        ("channel order exact",
         stored == list(channels),
         f"{len(stored)} channels" if stored == list(channels)
         else f"expected {list(channels)[:4]}..., stored {stored[:4]}..."),
        ("no excluded SPN present", not leaked,
         "none" if not leaked else f"LEAKED: {leaked}"),
        ("all finite",
         bool(np.isfinite(tensor).all()),
         f"{int((~np.isfinite(tensor)).sum())} non-finite values"),
        ("shape is (n, channels, steps)",
         tensor.ndim == 3 and tensor.shape[1] == len(channels)
         and tensor.shape[2] == RESIZE_STEPS,
         str(tensor.shape)),
        ("all usable drivers present", not missing,
         f"{len(present)} drivers" if not missing else f"missing {sorted(missing)}"),
        ("every driver has a window",
         bool(counts.min() >= 1),
         f"min {int(counts.min())}, median {counts.median():g}, "
         f"max {int(counts.max())} windows per driver"),
    ]


def spot_check(bundle, channels: tuple[int, ...], window_seconds: float,
               rng: np.random.Generator) -> tuple[int, int, float]:
    """Recompute sampled tensor columns from raw data and compare exactly.

    Args:
        bundle: the loaded `.npz`.
        channels: the SPNs the tensor carries, in order.
        window_seconds: window length the tensor was built at.
        rng: seeded generator for reproducible sampling.

    Returns:
        (comparisons, mismatches, worst_absolute_difference).
    """
    #print(bundle.keys())# prints dict_keys(['X', 'driver', 'start_time', 'channels'])
    #print(f"  {bundle['X'].shape} tensor, {len(bundle['channels'])} channels, {len(set(bundle['driver']))} drivers")   
    #print(f"  tensor[0, :, :]: {bundle['X'][0, :, :]}")  # prints the first window for all channels
    drivers = bundle["driver"]
    starts = bundle["start_time"]
    tensor = bundle["X"]

    chosen = rng.choice(sorted(set(drivers)), size=min(SPOT_DRIVERS,
                                                       len(set(drivers))),
                        replace=False)
    compared, mismatched, worst = 0, 0, 0.0

    for driver in chosen:
        path = next(p for p in DATA_PROCESSED.glob("G*_Subject*.csv")
                    if filename_to_driver_id(p.stem) == driver)
        #print(f"spot-checking {driver} -> {path.name}")
        rows = np.flatnonzero(drivers == driver)
        picks = rng.choice(rows, size=min(SPOT_WINDOWS, rows.size), replace=False)
        spns = rng.choice(channels, size=min(SPOT_CHANNELS, len(channels)),
                          replace=False)

        resolved = resolve_channels(pd.read_csv(path, nrows=0).columns.tolist(),
                                    tuple(int(s) for s in spns))

        needed = [c for pair in resolved.values() for c in pair]
        frame = pd.read_csv(path, usecols=sorted(set(needed)))

        for row in picks:
            start = float(starts[row])
            end = start + window_seconds
            for spn in spns:
                signal_col, time_col = resolved[int(spn)]
                pair = frame[[time_col, signal_col]].dropna().sort_values(time_col)
                times = pair[time_col].to_numpy(float)
                values = pair[signal_col].to_numpy(float)
                inside = (times >= start) & (times < end)
                if inside.sum() < MIN_SAMPLES_PER_WINDOW:
                    continue
                rebuilt = resample_window(times[inside], values[inside], start, end)
                stored = tensor[row, channels.index(int(spn)), :]
                difference = float(np.max(np.abs(rebuilt - stored)))
                compared += 1
                worst = max(worst, difference)
                if difference > 0:
                    mismatched += 1
    return compared, mismatched, worst


def build_report(results: dict) -> str:
    """Render the verification outcome.

    Args:
        results: window length to (structure checks, spot-check tuple).

    Returns:
        Markdown report.
    """
    lines = [
        "# Tensor verification — do the built artefacts match their source?",
        "",
        "`verify_resampling_distortion.py` measures the resampling *operation*. "
        "This reads the saved `.npz` files and checks that they contain it — "
        "catching faults in windowing, channel ordering or the write itself, which "
        "measuring a parallel re-derivation cannot see.",
        "",
    ]
    for window_seconds, (checks, (compared, mismatched, worst)) in results.items():
        passed = all(ok for _, ok, _ in checks) and mismatched == 0
        lines += [
            f"## {'🟢' if passed else '🔴'} {window_seconds:g} s window",
            "",
            "| Check | Result | Detail |",
            "|---|:-:|---|",
        ]
        for name, ok, detail in checks:
            lines.append(f"| {name} | {'🟢' if ok else '🔴'} | {detail} |")
        lines.append(
            f"| exact match vs raw | {'🟢' if mismatched == 0 else '🔴'} | "
            f"{compared} comparisons, {mismatched} mismatched, "
            f"worst absolute difference {worst:.2e} |")
        lines.append("")
    lines += [
        "## On the exact-match check",
        "",
        "The comparison recomputes `resample_window` on the raw samples inside each "
        "sampled window and requires **bit-identical** agreement with the stored "
        "column — not agreement within a tolerance. Both paths call the same "
        "function on the same inputs, so any non-zero difference is a windowing or "
        "indexing fault rather than numerical drift, and a tolerance would hide "
        "exactly the bug this check exists to find.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Verify every built tensor and write the report."""
    channels = arm_b_channels()
    print(f"expecting {len(channels)} channels, {len(expected_drivers())} drivers")

    results, failures = {}, 0
    for window_seconds in WINDOW_LENGTHS:
        path = tensor_path(window_seconds)
        if not path.exists():
            raise FileNotFoundError(f"run build_tensors.py first; missing {path}")
        bundle = np.load(path, allow_pickle=False)
        checks = check_structure(bundle, channels)
        #print(checks)
        spot = spot_check(bundle, channels, window_seconds,
                          np.random.default_rng(SPOT_SEED))
        results[window_seconds] = (checks, spot)

        bad = [name for name, ok, _ in checks if not ok]
        if spot[1]:
            bad.append("exact match vs raw")
        failures += len(bad)
        mark = "🟢" if not bad else "🔴"
        print(f"  {mark} {window_seconds:>6g}s  {bundle['X'].shape}  "
              f"{spot[0]} spot comparisons, worst diff {spot[2]:.2e}"
              + (f"  FAILED: {', '.join(bad)}" if bad else ""))

    REPORT_PATH.write_text(build_report(results))
    print(f"\n{'all checks passed' if not failures else f'{failures} CHECKS FAILED'}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
