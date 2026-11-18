"""Window tensor → Mantis embeddings with a frozen encoder.

Each channel is sent through the encoder independently and the per-channel
embeddings are concatenated, so a window of C channels becomes a vector of
C x hidden_dim. Nothing is trained here: this stage measures what the
pre-trained representation already separates.

Run from the repo root, in the `truckidme` env:
    python -m src.models.embed_mantis
"""

import time
from pathlib import Path

import numpy as np
import torch
from mantis.architecture import MantisV1
from mantis.trainer import MantisTrainer

from src.config import (DATA_INTERIM, MANTIS_CHECKPOINT, MANTIS_LAYER,
                        MANTIS_OUTPUT_TOKEN, OUT_REPORTS, WINDOW_SECONDS)

CHECKPOINT = MANTIS_CHECKPOINT
BATCH_SIZE = 256

WINDOWS_PATH = DATA_INTERIM / f"windows_{WINDOW_SECONDS}s.npz"
OUT_PATH = DATA_INTERIM / f"embeddings_{WINDOW_SECONDS}s.npz"
REPORT_PATH = OUT_REPORTS / "embeddings_build.md"


def pick_device() -> str:
    """Return the device to run on, preferring CUDA."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_encoder(device: str, token: str = MANTIS_OUTPUT_TOKEN) -> MantisTrainer:
    """Load the pre-trained Mantis encoder, frozen.

    Args:
        device: 'cuda' or 'cpu'.
        token: 'cls_token', 'mean_token' or 'combined'; defaults to the
            config value so existing callers are unchanged.

    Returns:
        A MantisTrainer wrapping the pre-trained network, ready for transform().
    """
    network = MantisV1(device=device, return_transf_layer=MANTIS_LAYER,
                       output_token=token)
    network = network.from_pretrained(CHECKPOINT)
    if hasattr(network, "remove_transf_layers"):
        network.remove_transf_layers()      # discard layers above the read-out
    return MantisTrainer(device=device, network=network)


def embed(model: MantisTrainer, windows: np.ndarray) -> np.ndarray:
    """Embed every window with the frozen encoder.

    Args:
        model: the loaded MantisTrainer.
        windows: float32 array of shape (n_windows, n_channels, seq_len).

    Returns:
        Embeddings of shape (n_windows, n_channels * hidden_dim).
    """
    return model.transform(windows, batch_size=BATCH_SIZE, to_numpy=True)


def write_report(windows: np.ndarray, embeddings: np.ndarray, drivers: np.ndarray,
                 device: str, duration_s: float) -> Path:
    """Write the embedding QC report.

    Args:
        windows: the input tensor.
        embeddings: the produced embeddings.
        drivers: driver id per window.
        device: device used.
        duration_s: wall-clock seconds for the embedding pass.

    Returns:
        The report path.
    """
    finite = np.isfinite(embeddings)
    unique, counts = np.unique(drivers, return_counts=True)
    lines = [
        "# Mantis embeddings — frozen encoder",
        "",
        f"- checkpoint: `{CHECKPOINT}`, read-out layer {MANTIS_LAYER}, "
        f"`{MANTIS_OUTPUT_TOKEN}` tokens",
        f"- device: **{device}**, duration: **{duration_s:.1f}s**",
        f"- input tensor: `{windows.shape}` (windows, channels, steps)",
        f"- embeddings: `{embeddings.shape}` "
        f"({embeddings.shape[1] // windows.shape[1]} dims per channel)",
        f"- drivers: **{len(unique)}**, windows/driver "
        f"min **{counts.min()}**, median **{int(np.median(counts))}**, max **{counts.max()}**",
        "",
        "## Violations" if not finite.all() else "## Violations — none",
    ]
    if not finite.all():
        lines += ["", f"| 🔴 | non-finite values | {int((~finite).sum())} entries |"]
    lines += [
        "",
        "## Embedding statistics",
        "",
        "| Statistic | Value |",
        "|---|---|",
        f"| mean | {embeddings.mean():.4f} |",
        f"| std | {embeddings.std():.4f} |",
        f"| min | {embeddings.min():.4f} |",
        f"| max | {embeddings.max():.4f} |",
        f"| all-zero dimensions | {int((embeddings.std(axis=0) == 0).sum())} |",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    return REPORT_PATH


def main() -> None:
    """Load windows, embed them with the frozen encoder, and save."""
    if not WINDOWS_PATH.exists():
        raise FileNotFoundError(
            f"{WINDOWS_PATH} not found — run `python -m src.features.build_windows` first")

    bundle = np.load(WINDOWS_PATH, allow_pickle=False)
    windows, drivers = bundle["X"], bundle["driver"]
    print(f"windows {windows.shape} from {WINDOWS_PATH.name}")

    device = pick_device()
    print(f"loading {CHECKPOINT} on {device}")
    model = load_encoder(device)

    clock = time.perf_counter()
    embeddings = embed(model, windows)
    duration = time.perf_counter() - clock
    print(f"embeddings {embeddings.shape} in {duration:.1f}s")

    np.savez_compressed(OUT_PATH, Z=embeddings, driver=drivers,
                        start_time=bundle["start_time"], channels=bundle["channels"],
                        checkpoint=np.asarray([CHECKPOINT]))
    print(f"saved -> {OUT_PATH}")
    print(f"report -> {write_report(windows, embeddings, drivers, device, duration)}")


if __name__ == "__main__":
    main()
