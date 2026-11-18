"""Step 2 of Arm B: frozen Mantis embeddings for each window length.

SUPERSEDED by `src/features/build_embeddings.py`, which builds all three tokens at all four windows and is checked by `QC/verify_embeddings.py`. Kept runnable: its `cls_token` files are what exp03-exp05 were scored on, and the verification shows the new `cls_token` files equal them.

Mantis is a univariate encoder: it takes one channel of RESIZE_STEPS points and
returns a fixed-width vector. Multivariate input is handled by encoding each
channel independently and concatenating, so a window of 50 channels becomes
50 x hidden_dim features. Nothing is trained here -- the encoder is frozen and this
is a forward pass.

That concatenation is also the problem the next step has to solve. At 120 s there
are 964 windows and 50 x 256 = 12,800 features. The chronological split trains on
70% of each driver's windows, roughly 675, so that is about **19 features per
training example** -- and the effective sample size is nearer 46 drives than 675
windows, because windows from one drive are correlated. In that regime Euclidean
distances between all points converge toward each other, which is exactly the
quantity nearest-centroid and KNN depend on. Hence PCA before scoring, fitted on
training windows only.

Reuses `load_encoder` and `embed` from `src.models.embed_mantis`; only the paths
differ, since that module is pinned to a single WINDOW_SECONDS.

Run from the repo root in the `truckidme` env:
    python -m experiments.exp03_arm_b_mantis.embed
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from src.config import DATA_INTERIM
from src.models.embed_mantis import embed, load_encoder, pick_device

EXPERIMENT_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = EXPERIMENT_DIR / "embeddings.md"

WINDOW_LENGTHS: tuple[float, ...] = (30.0, 51.2, 90.0, 120.0)
TRAIN_FRACTION = 0.70     # matches splits.TRAIN_END, for the per-example ratio


def tensor_path(window_seconds: float) -> Path:
    """Where `build_tensors.py` saved one window length's tensor.

    Args:
        window_seconds: window length.

    Returns:
        Path to the Arm B window tensor.
    """
    return DATA_INTERIM / f"windows_armB_{window_seconds:g}s.npz"


def embedding_path(window_seconds: float) -> Path:
    """Where this script saves one window length's embeddings.

    Args:
        window_seconds: window length.

    Returns:
        Path to the Arm B embeddings.
    """
    return DATA_INTERIM / f"embeddings_armB_{window_seconds:g}s.npz"


def embed_one(model, window_seconds: float) -> dict:
    """Embed one window length's tensor and save the result.

    Driver labels, window start times and the channel order are carried across
    unchanged, so the embedding file is self-sufficient for splitting and scoring.

    Args:
        model: the loaded, frozen MantisTrainer.
        window_seconds: window length.

    Returns:
        Shapes, dims per channel and elapsed seconds.
    """
    bundle = np.load(tensor_path(window_seconds), allow_pickle=False)
    windows = bundle["X"]
    started = time.time()
    embeddings = embed(model, windows)
    elapsed = time.time() - started

    path = embedding_path(window_seconds)
    np.savez_compressed(path, E=embeddings, driver=bundle["driver"],
                        start_time=bundle["start_time"],
                        channels=bundle["channels"])
    return {
        "window_seconds": window_seconds,
        "windows": int(windows.shape[0]),
        "channels": int(windows.shape[1]),
        "features": int(embeddings.shape[1]),
        "dims_per_channel": int(embeddings.shape[1] // windows.shape[1]),
        "drivers": int(len(np.unique(bundle["driver"]))),
        "features_per_train_example":
            embeddings.shape[1] / (windows.shape[0] * TRAIN_FRACTION),
        "seconds": elapsed,
        "megabytes": path.stat().st_size / 1e6,
    }


def build_manifest(rows: list[dict], device: str) -> str:
    """Render what was embedded.

    Args:
        rows: one summary per window length.
        device: the torch device used.

    Returns:
        Markdown manifest.
    """
    lines = [
        "# Arm B frozen Mantis embeddings",
        "",
        f"Frozen encoder on **{device}**, no training. Each channel is encoded "
        "independently and the per-channel vectors concatenated.",
        "",
        "| Window | Windows | Channels | Dims/ch | Features | Features per train example | Size | Time |",
        "|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['window_seconds']:g}s | {row['windows']} | "
            f"{row['channels']} | {row['dims_per_channel']} | "
            f"{row['features']} | **{row['features_per_train_example']:.1f}** | "
            f"{row['megabytes']:.0f} MB | {row['seconds']:.1f}s |")
    lines += [
        "",
        "## Why the features-per-train-example column matters",
        "",
        "It is the ratio that decides whether distance-based scoring can work at "
        "all, and it is computed against the **training** windows only "
        f"({TRAIN_FRACTION:.0%} of each driver's, per the chronological split) "
        "rather than all of them, since the test windows are not available to fit "
        "anything. Above 1 there are more features than examples, and in high "
        "dimension Euclidean distances between all points converge toward each "
        "other — precisely the quantity nearest-centroid and KNN rely on.",
        "",
        "Shorter windows improve the ratio by producing more windows at identical "
        "feature width, but those extra windows come from the same 46 drives and "
        "are correlated, so the *effective* sample size improves far less than the "
        "count suggests. PCA in the next step addresses the dimension directly.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Embed every window length with the frozen encoder."""
    missing = [w for w in WINDOW_LENGTHS if not tensor_path(w).exists()]
    if missing:
        raise FileNotFoundError(
            f"run build_tensors.py first; missing: "
            f"{', '.join(f'{w:g}s' for w in missing)}")

    device = pick_device()
    model = load_encoder(device)
    print(f"encoder on {device}")

    rows = []
    for window_seconds in WINDOW_LENGTHS:
        row = embed_one(model, window_seconds)
        rows.append(row)
        print(f"  {row['window_seconds']:>6g}s  {row['windows']:>5} windows  "
              f"{row['features']:>6} features  "
              f"{row['features_per_train_example']:>5.1f} per train ex  "
              f"{row['seconds']:>5.1f}s")

    MANIFEST_PATH.write_text(build_manifest(rows, device))
    print(f"\nmanifest -> {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
