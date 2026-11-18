"""Verify the frozen Mantis embeddings against their tensors and against each other.

`build_embeddings.py` writes 24 files (2 read-out layers x 3 tokens x 4 window
lengths). This reads
them back and checks that each one is what it claims to be:

| Check | Fault it catches |
|---|---|
| shape | wrong token width (256 vs 512 per channel) or a channel lost |
| all finite | a NaN from a degenerate window |
| labels match the tensor | driver, start time or channel order out of step with the windows the rows came from |
| stored token and layer | a file mislabelled, or built at the wrong layer |
| `combined` = `cls_token` then `mean_token`, per channel | the three tokens not coming from one encoder pass definition |
| reproducible | re-embedding sampled windows from the tensor gives the stored rows |
| continuity with exp03 | the new `cls_token` files equal `embeddings_armB_*`, which exp03-exp05 were scored on |

The last check is what lets earlier results stand: if the new `cls_token` files
equal the old ones, nothing scored on the old files changes by switching.

Comparisons between separate GPU passes use a tolerance (`TOLERANCE`), because
GPU kernels need not be bit-identical across calls; the worst difference is
reported either way.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_embeddings
"""
from __future__ import annotations

import numpy as np

from src.config import DATA_INTERIM, MANTIS_LAYER, OUT_REPORTS
from src.features.build_embeddings import (LAYERS, PROFILE_LAYERS,
                                           PROFILE_TOKEN, PROFILE_WINDOWS,
                                           TOKENS, embedding_path, layer_name)
from src.features.build_tensors import WINDOW_LENGTHS, tensor_path
from src.models.embed_mantis import embed, load_encoder, pick_device

REPORT_PATH = OUT_REPORTS / "embedding_verification.md"

TOKEN_DIMS = {"cls_token": 256, "mean_token": 256, "combined": 512}
TOLERANCE = 1e-4          # worst absolute difference allowed between GPU passes
SPOT_WINDOWS = 64         # windows re-embedded per file for the reproducibility check
SPOT_SEED = 0


def old_cls_path(window_seconds: float):
    """Where exp03 saved its `cls_token` embeddings.

    Args:
        window_seconds: window length.

    Returns:
        Path under `data/interim_data/`.
    """
    return DATA_INTERIM / f"embeddings_armB_{window_seconds:g}s.npz"


def check_file(token: str, window_seconds: float, tensor,
               layer: int) -> list[tuple]:
    """Structural checks on one embedding file against its tensor.

    Args:
        token: output token.
        window_seconds: window length.
        tensor: the loaded window tensor `.npz`.
        layer: read-out block index.

    Returns:
        (check name, passed, detail) rows.
    """
    saved = np.load(embedding_path(token, window_seconds, layer),
                    allow_pickle=False)
    features = saved["E"]
    n_windows, n_channels, _ = tensor["X"].shape
    expected = (n_windows, n_channels * TOKEN_DIMS[token])
    non_finite = int((~np.isfinite(features)).sum())
    labels_ok = (np.array_equal(saved["driver"], tensor["driver"])
                 and np.array_equal(saved["start_time"], tensor["start_time"])
                 and np.array_equal(saved["channels"], tensor["channels"]))
    stored = (str(saved["token"][0]), int(saved["layer"][0]))
    return [
        ("shape", features.shape == expected,
         f"{features.shape}, expected {expected}"),
        ("all finite", non_finite == 0, f"{non_finite} non-finite values"),
        ("labels match the tensor", labels_ok,
         "driver, start_time and channels identical"
         if labels_ok else "MISMATCH"),
        ("stored token and layer", stored == (token, layer),
         f"{stored[0]}, layer {stored[1]}"),
    ]


def check_combined(window_seconds: float, n_channels: int,
                   layer: int) -> tuple:
    """Check `combined` is `cls_token` then `mean_token` for every channel.

    Args:
        window_seconds: window length.
        n_channels: channels in the tensor.
        layer: read-out block index.

    Returns:
        (check name, passed, detail).
    """
    parts = {t: np.load(embedding_path(t, window_seconds, layer))["E"]
             for t in TOKENS}
    combined = parts["combined"].reshape(-1, n_channels, 512)
    cls = parts["cls_token"].reshape(-1, n_channels, 256)
    mean = parts["mean_token"].reshape(-1, n_channels, 256)
    worst = max(float(np.abs(combined[:, :, :256] - cls).max()),
                float(np.abs(combined[:, :, 256:] - mean).max()))
    return ("combined = cls_token then mean_token, per channel",
            worst <= TOLERANCE, f"worst absolute difference {worst:.2e}")


def check_reproducible(token: str, window_seconds: float, tensor, model,
                       rng: np.random.Generator, layer: int) -> tuple:
    """Re-embed sampled windows and compare with the stored rows.

    Args:
        token: output token.
        window_seconds: window length.
        tensor: the loaded window tensor `.npz`.
        model: frozen encoder loaded for this token.
        rng: seeded generator.
        layer: read-out block index.

    Returns:
        (check name, passed, detail).
    """
    stored = np.load(embedding_path(token, window_seconds, layer))["E"]
    picks = np.sort(rng.choice(stored.shape[0], size=SPOT_WINDOWS,
                               replace=False))
    fresh = embed(model, tensor["X"][picks])
    worst = float(np.abs(fresh - stored[picks]).max())
    return ("reproducible", worst <= TOLERANCE,
            f"{SPOT_WINDOWS} windows re-embedded, worst difference {worst:.2e}")


def check_continuity(window_seconds: float) -> tuple:
    """Compare the new `cls_token` file with exp03's `embeddings_armB_*`.

    Args:
        window_seconds: window length.

    Returns:
        (check name, passed, detail).
    """
    old_path = old_cls_path(window_seconds)
    if not old_path.exists():
        return ("continuity with exp03", False, f"{old_path.name} not found")
    old = np.load(old_path)["E"]
    new = np.load(embedding_path("cls_token", window_seconds))["E"]
    if old.shape != new.shape:
        return ("continuity with exp03", False,
                f"shape {old.shape} vs {new.shape}")
    worst = float(np.abs(old - new).max())
    return ("continuity with exp03", worst <= TOLERANCE,
            f"worst difference {worst:.2e} against {old_path.name}")


def build_report(results: dict) -> str:
    """Render the verification report, violations first.

    Args:
        results: section title -> list of (check, passed, detail).

    Returns:
        Markdown report.
    """
    failures = [(section, row) for section, rows in results.items()
                for row in rows if not row[1]]
    lines = [
        "# Embedding verification — do the frozen embeddings match their source?",
        "",
        "Reads the 24 files written by `src/features/build_embeddings.py` "
        f"({len(LAYERS)} layers x 3 tokens x {len(WINDOW_LENGTHS)} window "
        "lengths) and checks them "
        "against the window tensors, against each other, and against exp03's "
        "earlier `cls_token` files.",
        "",
        f"Comparisons between GPU passes allow a worst absolute difference of "
        f"{TOLERANCE:.0e}; the measured value is reported either way.",
        "",
    ]
    if failures:
        lines += [f"## 🔴 Violations — {len(failures)}", ""]
        for section, (check, _, detail) in failures:
            lines.append(f"- 🔴 {section}: {check} — {detail}")
        lines.append("")
    else:
        lines += ["## 🟢 No violations", ""]

    for section, rows in results.items():
        lines += [f"## {section}", "", "| Check | Result | Detail |",
                  "|---|:-:|---|"]
        for check, passed, detail in rows:
            lines.append(f"| {check} | {'🟢' if passed else '🔴'} | {detail} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Run every check on every file and write the report."""
    device = pick_device()
    rng = np.random.default_rng(SPOT_SEED)
    tensors = {w: np.load(tensor_path(w), allow_pickle=False)
               for w in WINDOW_LENGTHS}
    results: dict[str, list[tuple]] = {}

    for layer in LAYERS:
        for token in TOKENS:
            model = load_encoder(device, token=token, layer=layer)
            for window_seconds in WINDOW_LENGTHS:
                tensor = tensors[window_seconds]
                rows = check_file(token, window_seconds, tensor, layer)
                rows.append(check_reproducible(token, window_seconds, tensor,
                                               model, rng, layer))
                results[f"{layer_name(layer)}, `{token}`, "
                        f"{window_seconds:g} s"] = rows
            del model

    for layer in PROFILE_LAYERS:
        model = load_encoder(device, token=PROFILE_TOKEN, layer=layer)
        for window_seconds in PROFILE_WINDOWS:
            tensor = tensors[window_seconds]
            rows = check_file(PROFILE_TOKEN, window_seconds, tensor, layer)
            rows.append(check_reproducible(PROFILE_TOKEN, window_seconds,
                                           tensor, model, rng, layer))
            results[f"layer profile: {layer_name(layer)}, `{PROFILE_TOKEN}`, "
                    f"{window_seconds:g} s"] = rows
        del model

    for layer in LAYERS:
        for window_seconds in WINDOW_LENGTHS:
            n_channels = tensors[window_seconds]["X"].shape[1]
            rows = [check_combined(window_seconds, n_channels, layer)]
            # exp03's files exist only at the project's read-out layer
            if layer == MANTIS_LAYER:
                rows.append(check_continuity(window_seconds))
            results[f"{layer_name(layer)}, across tokens, "
                    f"{window_seconds:g} s"] = rows

    REPORT_PATH.write_text(build_report(results))
    failed = sum(not row[1] for rows in results.values() for row in rows)
    total = sum(len(rows) for rows in results.values())
    for section, rows in results.items():
        flags = "".join("🟢" if row[1] else "🔴" for row in rows)
        print(f"  {flags}  {section}")
    print(f"\n{total - failed} of {total} checks passed")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
