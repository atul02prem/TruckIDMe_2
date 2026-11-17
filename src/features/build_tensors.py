"""Step 1 of Arm B end-to-end: build and save the window tensors.

The model input is the **50 channels** of DECISIONS.md S3: the 62 that survived
`build_processed_data` minus S1's nine exclusions, minus SPN 51, 3030 and 2979 on
data quality. Four window lengths, because RESIZE_STEPS is fixed at 512, so the
window length *is* the grid rate -- 30 s gives 17.07 Hz, 120 s gives 4.27 Hz.

This is the only slow step in Arm B. Tensor building reads all 46 processed CSVs per
window length, about two minutes each; the frozen Mantis forward pass afterwards
takes seconds.

**The tensor is built at the final channel count on purpose.** An earlier version
built 53 channels and left a subsetting step in `embed.py` to apply S3. That let the
tensor and the decision record drift apart, and they did: SPN 2979 had been recorded
in S1 as "kept conditionally" rather than excluded, so it never entered the list the
build script read, and once its precondition was deferred the conditional silently
became an inclusion. Building the model input directly removes the gap --
`main` asserts that no excluded SPN is present, so a decision recorded in
DECISIONS.md but missing from EXCLUDED_SPNS fails loudly instead of shipping.

The channel order is still saved alongside each tensor, so downstream code selects
by SPN rather than by column position.

Tensors go to `data/interim_data/` (gitignored) rather than into this experiment
folder, since four window lengths come to roughly 400 MB.

Run from the repo root in the `truckidme` env:
    python -m src.features.build_tensors
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATA_INTERIM, DATA_PROCESSED, OUT_REPORTS, RESIZE_STEPS
from src.features.build_windows import audited_channel_spns, build_dataset

MANIFEST_PATH = OUT_REPORTS / "tensors.md"

WINDOW_LENGTHS: tuple[float, ...] = (30.0, 51.2, 90.0, 120.0)

# Everything excluded beyond what processed_data already dropped. Named here rather
# than imported from config so this stays reproducible after config.py is updated.
#
# S1's nine exclusions:
#   515 2978 3229 3230 3231 3232 3239 4154 5015
# S3's three data-quality drops:
#   51    one value 98.35% of a drive, worst anti-alias delta of any kept channel
#   3030  16-36 genuine multi-second blackouts per drive, interpolated across
#   2979  11b "Not available" sentinel 28.57% of samples, 11x above its 0-1 range;
#         40.2% of aggregated values illegal, round-trip error 1.150
#
# The tensor is built at the final channel count so it IS the model input, with no
# later subsetting step to fall out of step with the decision record.
EXCLUDED_SPNS: tuple[int, ...] = (51, 515, 2978, 2979, 3030, 3229, 3230, 3231,
                                  3232, 3239, 4154, 5015)


def arm_b_channels() -> tuple[int, ...]:
    """The 50 model channels, in ascending SPN order.

    Returns:
        SPNs present in processed data and not excluded by S1 or S3.
    """
    header = pd.read_csv(sorted(DATA_PROCESSED.glob("G*_Subject*.csv"))[0],
                         nrows=0).columns.tolist()
    return tuple(s for s in audited_channel_spns(header) if s not in EXCLUDED_SPNS)


def tensor_path(window_seconds: float) -> Path:
    """Where one window length's tensor is saved.

    Args:
        window_seconds: window length.

    Returns:
        Path under DATA_INTERIM, tagged with arm and window length.
    """
    return DATA_INTERIM / f"windows_armB_{window_seconds:g}s.npz"


def build_one(channels: tuple[int, ...], window_seconds: float) -> dict:
    """Build, save and summarise one window length's tensor.

    Args:
        channels: SPNs to stack, in this order.
        window_seconds: window length.

    Returns:
        Shape, window count, per-driver spread and elapsed seconds.
    """
    started = time.time()
    tensor, drivers, starts, counts = build_dataset(channels, window_seconds,
                                                    verbose=False)
    path = tensor_path(window_seconds)
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, X=tensor, driver=drivers, start_time=starts,
                        channels=np.asarray([str(s) for s in channels]))
    per_driver = np.array(list(counts.values()))
    return {
        "window_seconds": window_seconds,
        "grid_hz": RESIZE_STEPS / window_seconds,
        "shape": tensor.shape,
        "windows": int(len(tensor)),
        "drivers": int((per_driver > 0).sum()),
        "min_per_driver": int(per_driver.min()),
        "median_per_driver": float(np.median(per_driver)),
        "max_per_driver": int(per_driver.max()),
        "megabytes": path.stat().st_size / 1e6,
        "seconds": time.time() - started,
        "path": path,
    }


def build_manifest(rows: list[dict], channels: tuple[int, ...]) -> str:
    """Render what was built, as a reproducibility record.

    Args:
        rows: one summary per window length.
        channels: the SPNs stacked, in order.

    Returns:
        Markdown manifest.
    """
    lines = [
        "# Arm B window tensors",
        "",
        f"**{len(channels)} channels** x **{len(rows)} window lengths**, built from "
        "`data/processed_data/` by `build_tensors.py`.",
        "",
        "`RESIZE_STEPS = 512` is fixed, so window length sets the grid rate.",
        "",
        "| Window | Grid | Shape | Windows | Drivers | Per driver (min/med/max) | Size | Built in |",
        "|--:|--:|---|--:|--:|---|--:|--:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['window_seconds']:g}s | {row['grid_hz']:.2f} Hz | "
            f"`{row['shape']}` | {row['windows']} | {row['drivers']} | "
            f"{row['min_per_driver']}/{row['median_per_driver']:g}/"
            f"{row['max_per_driver']} | {row['megabytes']:.0f} MB | "
            f"{row['seconds']:.0f}s |")
    lines += [
        "",
        "## Channels",
        "",
        f"Stacked in this order, saved in each `.npz` under `channels`: "
        f"{', '.join(str(s) for s in channels)}",
        "",
        "## Excluded before this step",
        "",
        f"{len(EXCLUDED_SPNS)} SPNs beyond the 40 that `data/processed_data/` had "
        f"already dropped: {', '.join(str(s) for s in EXCLUDED_SPNS)} — S1's nine "
        "plus S3's three data-quality drops (51, 3030, 2979). The tensor is built "
        "at the final channel count, so it is the model input with no later "
        "subsetting step that could fall out of step with DECISIONS.md.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Build every window length's tensor and write the manifest."""
    channels = arm_b_channels()
    stray = sorted(set(channels) & set(EXCLUDED_SPNS))
    if stray:
        raise ValueError(f"excluded SPNs leaked into the channel set: {stray}")
    print(f"arm B: {len(channels)} channels | windows: "
          + ", ".join(f"{w:g}s" for w in WINDOW_LENGTHS))

    rows = []
    for window_seconds in WINDOW_LENGTHS:
        row = build_one(channels, window_seconds)
        rows.append(row)
        print(f"  {row['window_seconds']:>6g}s  {row['grid_hz']:5.2f} Hz  "
              f"{str(row['shape']):>20}  {row['megabytes']:>5.0f} MB  "
              f"{row['seconds']:>4.0f}s")

    MANIFEST_PATH.write_text(build_manifest(rows, channels))
    print(f"\nmanifest -> {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
