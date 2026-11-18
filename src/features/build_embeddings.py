"""Build the frozen Mantis embeddings: 3 output tokens x 4 window lengths.

The frozen encoder is deterministic and never trained, so its output is an
artefact of the tensors, like the tensors are of the raw data. It is built once
here and every experiment reads it. Before this, frozen embeddings were made in
three places (exp03 `embed.py` for `cls_token`, exp06 `run.py` on the fly, exp06
`rescore_frozen.py` for all three tokens), and one artefact built three ways can
drift without anyone noticing.

Each channel is encoded on its own and the per-channel vectors concatenated:

| Token | Per channel | 50 channels |
|---|--:|--:|
| `cls_token` | 256 | 12,800 |
| `mean_token` | 256 | 12,800 |
| `combined` | 512 (`cls_token` then `mean_token`) | 25,600 |

The token and read-out layer are saved inside every file, so a file cannot be
mistaken for a different configuration. Driver labels, window start times and
channel order are carried over from the tensor unchanged.

Checked by `QC/verify_embeddings.py`.

Run from the repo root in the `truckidme` env:
    python -m src.features.build_embeddings
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import torch

from src.config import DATA_INTERIM, MANTIS_CHECKPOINT, MANTIS_LAYER, OUT_REPORTS
from src.features.build_tensors import WINDOW_LENGTHS, tensor_path
from src.models.embed_mantis import embed, load_encoder, pick_device
from src.models.splits import TRAIN_END

TOKENS: tuple[str, ...] = ("cls_token", "mean_token", "combined")
# Mantis indexes its 6 transformer blocks from 0: index 2 is the output after
# the 3rd block (the project's read-out), -1 after the 6th (final) block.
LAYERS: tuple[int, ...] = (MANTIS_LAYER, -1)
# The layer profile: every block, for the headline token, at every window.
PROFILE_TOKEN = "mean_token"
PROFILE_WINDOWS: tuple[float, ...] = WINDOW_LENGTHS
PROFILE_LAYERS: tuple[int, ...] = (0, 1, 3, 4)   # 2 and final are in LAYERS
REPORT_PATH = OUT_REPORTS / "embeddings.md"


def layer_name(layer: int) -> str:
    """Human-readable read-out layer.

    Args:
        layer: 0-based block index, or -1 for the final block.

    Returns:
        e.g. 'index 2 (block 3 of 6)' or 'final (block 6 of 6)'.
    """
    if layer == -1:
        return "final (block 6 of 6)"
    return f"index {layer} (block {layer + 1} of 6)"


def embedding_path(token: str, window_seconds: float,
                   layer: int = MANTIS_LAYER) -> Path:
    """Where one token's frozen embeddings at one window length are saved.

    The project's read-out layer keeps the original file names, so every
    existing reader is unchanged; other layers are marked in the name.

    Args:
        token: 'cls_token', 'mean_token' or 'combined'.
        window_seconds: window length.
        layer: read-out block index; defaults to the project's.

    Returns:
        Path under `data/interim_data/`.
    """
    if layer == MANTIS_LAYER:
        return DATA_INTERIM / f"embeddings_frozen_{token}_{window_seconds:g}s.npz"
    if layer == -1:
        return (DATA_INTERIM /
                f"embeddings_frozen_final_{token}_{window_seconds:g}s.npz")
    return (DATA_INTERIM /
            f"embeddings_frozen_layer{layer}_{token}_{window_seconds:g}s.npz")


def build_one(token: str, window_seconds: float, device: str,
              layer: int) -> dict:
    """Embed one window length's tensor under one token and save it.

    Args:
        token: output token.
        window_seconds: window length.
        device: torch device string.
        layer: read-out block index.

    Returns:
        Shapes, elapsed seconds and file size for the report.
    """
    bundle = np.load(tensor_path(window_seconds), allow_pickle=False)
    windows = bundle["X"]
    model = load_encoder(device, token=token, layer=layer)
    started = time.perf_counter()
    features = embed(model, windows)
    elapsed = time.perf_counter() - started
    del model
    if device == "cuda":
        torch.cuda.empty_cache()

    path = embedding_path(token, window_seconds, layer)
    np.savez_compressed(path, E=features, driver=bundle["driver"],
                        start_time=bundle["start_time"],
                        channels=bundle["channels"],
                        token=np.asarray([token]),
                        layer=np.asarray([layer]),
                        checkpoint=np.asarray([MANTIS_CHECKPOINT]))
    return {
        "token": token,
        "layer": layer,
        "window_seconds": window_seconds,
        "windows": int(windows.shape[0]),
        "channels": int(windows.shape[1]),
        "features": int(features.shape[1]),
        "dims_per_channel": int(features.shape[1] // windows.shape[1]),
        "features_per_train_example":
            features.shape[1] / (windows.shape[0] * TRAIN_END),
        "seconds": elapsed,
        "megabytes": path.stat().st_size / 1e6,
    }


def build_report(rows: list[dict], device: str) -> str:
    """Render what was built.

    Args:
        rows: one summary per (token, window).
        device: torch device used.

    Returns:
        Markdown report.
    """
    lines = [
        "# Frozen Mantis embeddings",
        "",
        f"`{MANTIS_CHECKPOINT}`, frozen (no training), on **{device}**, read "
        f"out at two layers: **{layer_name(MANTIS_LAYER)}**, the project's, and "
        f"**{layer_name(-1)}**. Mantis numbers its 6 blocks from 0. Built by `src/features/build_embeddings.py` "
        "from the window tensors; checked by `QC/verify_embeddings.py`.",
        "",
        "Each of the 50 channels is encoded on its own and the per-channel "
        "vectors are concatenated. `combined` is `cls_token` followed by "
        "`mean_token` for each channel, so it holds twice the numbers but is "
        "built from the same 256-wide token space.",
        "",
        "| Layer | Token | Window | Windows | Dims/ch | Features | Features per "
        "train example | Size | Time |",
        "|---|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        lines.append(
            f"| {layer_name(row['layer'])} | `{row['token']}` | "
            f"{row['window_seconds']:g} s | "
            f"{row['windows']} | {row['dims_per_channel']} | "
            f"{row['features']:,} | **{row['features_per_train_example']:.1f}** | "
            f"{row['megabytes']:.0f} MB | {row['seconds']:.1f} s |")
    lines += [
        "",
        "## Features per training example",
        "",
        f"Features divided by training windows ({TRAIN_END:.0%} of each "
        "driver's windows under the chronological split). Every value is above "
        "1: there are more features than training examples in every "
        "configuration, which is why every read-out downstream standardises and "
        "projects before measuring distance. `combined` doubles the ratio at "
        "every window.",
        "",
        "Shorter windows give more examples at the same width, but those extra "
        "windows come from the same 46 drives and are correlated, so the "
        "effective sample size grows less than the count suggests.",
        "",
        "## Which experiments read which token",
        "",
        "| Token | Read by |",
        "|---|---|",
        "| `cls_token` | exp03 analysis, exp04, exp05 — chosen early in "
        "`DECISIONS.md` D10, later superseded |",
        "| `mean_token` | exp06 onward — chosen on inner validation in exp06 |",
        "| `combined` | exp06 token comparison only |",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Embed every window length under every token with the frozen encoder."""
    missing = [w for w in WINDOW_LENGTHS if not tensor_path(w).exists()]
    if missing:
        raise FileNotFoundError(
            "run src.features.build_tensors first; missing: "
            + ", ".join(f"{w:g}s" for w in missing))

    device = pick_device()
    rows = []
    cells = [(layer, token, window_seconds) for layer in LAYERS
             for token in TOKENS for window_seconds in WINDOW_LENGTHS]
    cells += [(layer, PROFILE_TOKEN, window_seconds)
              for window_seconds in PROFILE_WINDOWS for layer in PROFILE_LAYERS]
    for layer, token, window_seconds in cells:
        row = build_one(token, window_seconds, device, layer)
        rows.append(row)
        print(f"  L{layer:<3} {token:<11} {window_seconds:>5g}s  "
              f"{row['windows']:>5} windows  {row['features']:>6} features  "
              f"{row['seconds']:>5.1f}s", flush=True)

    REPORT_PATH.write_text(build_report(rows, device))
    print(f"\nreport -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
