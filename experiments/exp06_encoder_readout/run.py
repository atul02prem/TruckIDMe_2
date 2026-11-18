"""Which Mantis output token should we read out, measured properly this time.

## Why this is being re-run

`outputs/reports/encoder_config_selection.md` chose `cls_token` over `combined`
(21.3% vs 16.9%). That selection is not safe to rely on:

1. It used a **nearest-centroid** read-out. exp04's H4 showed nearest-centroid
   understates these representations by ~18pp (10.6% -> 28.7% on identical
   embeddings), so it is the worst available instrument for ranking encoders.
2. It ran on an **earlier 8-channel configuration**, not the audited 50.
3. It measured **closed set only** — the open-set question was never asked.
4. **`mean_token` was never tested at all.** The table contains only `cls_token`
   and `combined`.

So the choice baked into `src/config.py` rests on one measurement, taken with a
bad instrument, on a configuration we no longer use.

## What the three options are

`MantisV1`'s transformer prepends a CLS token to the 32 patch tokens. After the
transformer, `output_token` selects what leaves the encoder:

| Option | Dims/channel | What it is |
|---|--:|---|
| `cls_token` | 256 | the CLS token alone — a learned summary slot |
| `mean_token` | 256 | the mean over the 32 patch tokens |
| `combined` | **512** | the two concatenated |

All three use the **same pre-trained weights**; this is a read-out choice, not a
different model. `hidden_dim` itself is fixed at 256 by the checkpoint and
cannot be changed without discarding the pre-training.

## The cost that argues against `combined`

`combined` doubles the feature count: 50 x 512 = **25,600** features. At 51.2 s
there are ~1,240 training windows, so features-per-training-example goes from
8.1 to **16.2**. Whether the extra information outweighs that is exactly what
this measures, and it is why `combined` is scored with the same read-outs as
the others rather than being argued about.

## Design

| Axis | Levels |
|---|---|
| output token | `cls_token`, `mean_token`, `combined` |
| window length | 51.2 s (10.00 Hz, native-rate match), 120 s (4.27 Hz, best frozen result so far) |
| read-out | `linear_probe`, `lda_centroid`, `random_forest` |
| task | closed set 46-way, **and** open set over 5 partitions |

Frozen encoder throughout — no fine-tuning, so the comparison isolates the
read-out token and nothing else.

## Commands

```bash
python -u -m experiments.exp06_encoder_readout.run
python -u -m experiments.exp06_encoder_readout.run --window 51.2
```
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch
from mantis.architecture import MantisV1
from mantis.trainer import MantisTrainer

from src.config import MANTIS_CHECKPOINT, MANTIS_LAYER
from src.features.build_tensors import tensor_path
from src.models.open_set import (evaluate_partition, N_PARTITIONS, N_UNKNOWN,
                                 SEED, summarise)
from src.models.readouts import closed_set_heads
from src.models.splits import known_unknown_partitions

TOKENS = ("cls_token", "mean_token", "combined")
WINDOWS = (51.2, 120.0)
HEADS = ("linear_probe", "lda_centroid", "random_forest")
RULES = ("euclidean", "cosine", "ratio", "mahalanobis", "msp")
BATCH_SIZE = 256
RESULTS_PATH = Path(__file__).parent / "results.md"


def embed_with_token(windows: np.ndarray, token: str, device: str
                     ) -> tuple[np.ndarray, float]:
    """Embed every window with the frozen encoder under one output token.

    Args:
        windows: (n_windows, n_channels, 512) tensor.
        token: 'cls_token', 'mean_token' or 'combined'.
        device: torch device string.

    Returns:
        (embeddings of shape (n_windows, n_channels * dims), seconds taken).
    """
    network = MantisV1(device=device, return_transf_layer=MANTIS_LAYER,
                       output_token=token).from_pretrained(MANTIS_CHECKPOINT)
    model = MantisTrainer(device=device, network=network)
    clock = time.perf_counter()
    embeddings = model.transform(windows, batch_size=BATCH_SIZE)
    return embeddings, time.perf_counter() - clock


def write_report(rows: list[dict]) -> None:
    """Write the comparison report inside the experiment folder.

    Args:
        rows: one dict per (window, token) cell.
    """
    lines = [
        "# exp06 — Mantis output token, measured with real read-outs",
        "",
        "Frozen encoder, audited 50 channels, 46 drivers. `cls_token` and "
        "`mean_token` give 256 dims per channel; `combined` concatenates them "
        "for 512. All three use the same pre-trained weights — this is a "
        "read-out choice, not a different model.",
        "",
        "Supersedes the `output_token` row of "
        "`outputs/reports/encoder_config_selection.md`, which ranked these "
        "with a **nearest-centroid** read-out (shown by exp04 to understate "
        "these embeddings by ~18pp), on an earlier 8-channel configuration, "
        "closed set only, and never tested `mean_token`.",
        "",
        "## Closed set — 46-way, chance 2.2%",
        "",
        "| Window | Output token | Features | linear probe | LDA + centroid | "
        "random forest | embed s |",
        "|---|---|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        cells = " | ".join(f"{row[h] * 100:.1f}%" for h in HEADS)
        lines.append(
            f"| {row['window']:g} s | `{row['token']}` | "
            f"{row['features']:,} | {cells} | {row['embed_s']:.1f} |")

    best = max(rows, key=lambda r: max(r[h] for h in HEADS))
    lines += [
        "",
        f"Best: **{best['token']}** at {best['window']:g} s, "
        f"{max(best[h] for h in HEADS) * 100:.1f}%.",
        "",
        "## Open set — 5 partitions of 36 known / 10 unknown",
        "",
        "Window-level AUROC; **0.500 is chance**. The question "
        "`encoder_config_selection.md` never asked.",
        "",
        "| Window | Output token | " + " | ".join(f"`{r}`" for r in RULES) + " |",
        "|---|---|" + "--:|" * len(RULES),
    ]
    for row in rows:
        cells = " | ".join(f"{row['auroc'][r][0]:.3f} ± {row['auroc'][r][1]:.3f}"
                           for r in RULES)
        lines.append(f"| {row['window']:g} s | `{row['token']}` | {cells} |")

    lines += [
        "",
        "## Features per training example",
        "",
        "`combined` doubles the feature count at no change in sample size. "
        "Above 1 there are more features than examples, and distance-based "
        "scoring degrades as the ratio grows.",
        "",
        "| Window | `cls_token` / `mean_token` | `combined` |",
        "|---|--:|--:|",
        "| 51.2 s | 8.1 | **16.2** |",
        "| 120 s | 19.0 | **38.0** |",
        "",
        "## Limitations",
        "",
        "- **Frozen encoder only.** A different output token might interact "
        "with fine-tuning differently; untested.",
        "- **Read-out layer fixed at 2.** The layer axis was ranked only by the "
        "same superseded nearest-centroid selection.",
        "- Single chronological split for the closed-set column; the open-set "
        "column has five partitions.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Score every output token at every window length and write the report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, action="append", default=None)
    arguments = parser.parse_args()
    windows_wanted = arguments.window or list(WINDOWS)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows: list[dict] = []

    for window in windows_wanted:
        cached = np.load(tensor_path(window), allow_pickle=True)
        tensor, drivers = cached["X"], cached["driver"]
        starts = cached["start_time"]
        cohort = np.unique(drivers)
        partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                              n_partitions=N_PARTITIONS,
                                              seed=SEED)
        print(f"\n=== {window:g} s | {tensor.shape} | {len(cohort)} drivers ===")

        for token in TOKENS:
            features, embed_s = embed_with_token(tensor, token, device)
            heads = closed_set_heads(features, drivers, starts, cohort)
            open_rows = [evaluate_partition(features, drivers, starts, k, u)
                         for k, u in partitions]
            summary = summarise(open_rows)

            row = {"window": window, "token": token,
                   "features": features.shape[1], "embed_s": embed_s,
                   "auroc": {r: summary[f"auroc:{r}"] for r in RULES},
                   **{h: heads[h][1] for h in HEADS}}
            rows.append(row)
            best_rule = max(RULES, key=lambda r: row["auroc"][r][0])
            print(f"  {token:11s} {features.shape[1]:>6,} feat | "
                  + "  ".join(f"{h.split('_')[0]} {row[h] * 100:5.1f}%"
                              for h in HEADS)
                  + f" | AUROC {row['auroc'][best_rule][0]:.3f} ({best_rule})")

    write_report(rows)
    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
