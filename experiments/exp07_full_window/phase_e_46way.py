"""Phase E — 46-way closed-set identification, with every driver enrolled.

## Why this run exists

Every fine-tuned result so far is **36-way**, because the open-set protocol
holds 10 of the 46 drivers out as strangers and only the remaining 36 can be
enrolled. 36-way is an easier problem than 46-way (chance 2.8% against 2.2%),
so Phase B's 45.3% cannot stand in for a 46-way number. This run measures the
fine-tuned encoder with all 46 drivers enrolled.

No partitions are needed: with every driver enrolled there are no strangers to
vary. Instead the run is repeated at **two seeds**, which varies the
initialisation of the classification head and the batch ordering, giving an
error bar on the training process rather than on the driver draw.

## Configuration

Everything is carried over from the earlier phases and nothing is re-tuned:

| | | chosen by |
|---|---|---|
| output token | `mean_token` | inner validation, 4/4 windows (`exp06/confirm_token.md`) |
| window | 30 s | inner validation (`phase_a.md`) |
| arm | `full`, all 8,590,372 parameters | the project's spine |
| epochs | 60 | pinned |
| learning rate | 1e-4 | the value the EEG paper used for Mantis |

A `frozen` row is included at no extra GPU cost, so the fine-tuning gain is
visible at 46-way too.

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_e_46way
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

from experiments.exp06_encoder_readout.run import embed_with_token
from src.config import DATA_INTERIM, MANTIS_CHECKPOINT, MANTIS_LAYER
from src.features.build_tensors import tensor_path
from src.models.finetune import BATCH_SIZE, EPOCHS, LEARNING_RATE, OUTPUT_TOKEN
from src.models.readouts import closed_set_heads, HEADS
from src.models.splits import split_by_driver

WINDOW_SECONDS = 30.0
SEEDS = (42, 1337)
RESULTS_PATH = Path(__file__).parent / "phase_e_46way.md"


def embedding_path(seed: int) -> Path:
    """Where one seed's fine-tuned embeddings are saved.

    Args:
        seed: the training seed.

    Returns:
        Path under `data/interim_data/`.
    """
    return (DATA_INTERIM /
            f"embeddings_46way_{OUTPUT_TOKEN}_{WINDOW_SECONDS:g}s_s{seed}.npz")


def fine_tune_46(windows: np.ndarray, labels: np.ndarray,
                 fit_index: np.ndarray, seed: int) -> tuple[np.ndarray, float]:
    """Fine-tune on every driver's training windows and embed everything.

    Args:
        windows: (n_windows, n_channels, 512) tensor.
        labels: integer driver label per window, valid on fit_index.
        fit_index: training window positions.
        seed: seed for initialisation and batch order.

    Returns:
        (embeddings for every window, minutes taken).
    """
    torch.manual_seed(seed)
    np.random.seed(seed)
    network = MantisV1(device="cuda", return_transf_layer=MANTIS_LAYER,
                       output_token=OUTPUT_TOKEN).from_pretrained(
        MANTIS_CHECKPOINT)
    model = MantisTrainer(device="cuda", network=network)
    clock = time.perf_counter()
    model.fit(windows[fit_index], labels[fit_index], fine_tuning_type="full",
              adapter=None, num_epochs=EPOCHS, batch_size=BATCH_SIZE,
              base_learning_rate=LEARNING_RATE)
    minutes = (time.perf_counter() - clock) / 60
    return model.transform(windows, batch_size=256), minutes


def write_report(rows: list[dict], frozen: dict, minutes: list[float]) -> None:
    """Write the 46-way report inside the experiment folder.

    Args:
        rows: one dict per seed for the fine-tuned arm.
        frozen: the frozen arm's accuracies.
        minutes: fine-tuning minutes per seed.
    """
    lines = [
        "# exp07 Phase E — 46-way closed-set identification",
        "",
        f"All **46 drivers enrolled**, chance **2.2%**. "
        f"`{OUTPUT_TOKEN}`, {WINDOW_SECONDS:g} s windows, per-driver "
        "chronological 70/5/25 split. The fine-tuned arm is repeated at "
        f"{len(SEEDS)} seeds ({', '.join(str(s) for s in SEEDS)}); the frozen "
        "arm is deterministic.",
        "",
        "Every other fine-tuned number in exp07 is 36-way, which is an easier "
        "problem; this is the full-cohort measurement.",
        "",
        "## Results",
        "",
        "| Arm | linear probe | LDA + centroid | random forest |",
        "|---|--:|--:|--:|",
    ]
    cells = []
    for head in HEADS:
        values = [row[head] for row in rows]
        cells.append(f"**{np.mean(values) * 100:.1f}%** ± "
                     f"{np.std(values) * 100:.1f}%")
    lines.append(f"| `full` (fine-tuned) | " + " | ".join(cells) + " |")
    lines.append("| `frozen` | "
                 + " | ".join(f"{frozen[h] * 100:.1f}%" for h in HEADS)
                 + " |")

    best = max(np.mean([row[h] for row in rows]) for h in HEADS)
    lines += [
        "",
        "## Comparison at the same cohort size",
        "",
        "| | 46-way top-1 |",
        "|---|--:|",
        f"| **fine-tuned Mantis, `{OUTPUT_TOKEN}`, {WINDOW_SECONDS:g} s** "
        f"| **{best * 100:.1f}%** |",
        "| frozen Mantis, `mean_token`, block 1, 90 s, LDA (exp06 grid; D14) | 44.9% |",
        "| frozen Mantis, `mean_token`, 120 s, LDA (`exp06`) | 36.7% |",
        "| frozen Mantis, `cls_token`, 120 s, LDA (`exp05`) | 27.7% |",
        "| chance | 2.2% |",
        "",
        f"Fine-tuning cost: **{np.mean(minutes):.1f} min** per seed.",
        "",
        "## Per-seed detail",
        "",
        "| Seed | linear probe | LDA + centroid | random forest | min |",
        "|---|--:|--:|--:|--:|",
    ]
    for row, spent in zip(rows, minutes):
        lines.append(f"| {row['seed']} | "
                     + " | ".join(f"{row[h] * 100:.1f}%" for h in HEADS)
                     + f" | {spent:.1f} |")

    lines += [
        "",
        "## Limitations",
        "",
        "- **Two seeds vary the training process, not the data.** The split is "
        "fixed, so this error bar does not capture how much the result depends "
        "on which windows land in train versus test.",
        "- **No open-set measurement is possible here** — with all 46 drivers "
        "enrolled there are no strangers. That is measured at 36-way in "
        "Phase C and Phase D.",
        "- Fixed 60-epoch budget, final epoch, no model selection.",
        "- Resampling is `np.interp`, which aliases on downsample; at 30 s the "
        "grid is 17.07 Hz, the least affected of the four window lengths.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Fine-tune at each seed on all 46 drivers and report closed-set accuracy."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, action="append", default=None)
    arguments = parser.parse_args()
    seeds = arguments.seed or list(SEEDS)

    cached = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=True)
    tensor, drivers = cached["X"], cached["driver"]
    starts, channels = cached["start_time"], cached["channels"]
    cohort = np.unique(drivers)
    fit_index, _ = split_by_driver(drivers, starts)

    codes = np.full(len(drivers), -1, dtype=np.int64)
    for code, driver in enumerate(cohort):
        codes[drivers == driver] = code

    print(f"{tensor.shape} | {len(cohort)} drivers enrolled | "
          f"chance {100 / len(cohort):.1f}% | "
          f"{len(fit_index):,} training windows | seeds {seeds}")

    print("\nfrozen reference")
    frozen_features, seconds = embed_with_token(tensor, OUTPUT_TOKEN, "cuda")
    frozen_heads = closed_set_heads(frozen_features, drivers, starts, cohort)
    frozen = {h: frozen_heads[h][1] for h in HEADS}
    print(f"  embedded in {seconds:.1f}s | "
          + "  ".join(f"{h.split('_')[0]} {frozen[h] * 100:5.1f}%"
                      for h in HEADS))

    rows, minutes = [], []
    for seed in seeds:
        print(f"\nseed {seed}")
        features, spent = fine_tune_46(tensor, codes, fit_index, seed)
        np.savez_compressed(embedding_path(seed), E=features, driver=drivers,
                            start_time=starts, channels=channels)
        heads = closed_set_heads(features, drivers, starts, cohort)
        row = {"seed": seed, **{h: heads[h][1] for h in HEADS}}
        rows.append(row)
        minutes.append(spent)
        print(f"  {spent:.1f} min | "
              + "  ".join(f"{h.split('_')[0]} {row[h] * 100:5.1f}%"
                          for h in HEADS))
        write_report(rows, frozen, minutes)

    write_report(rows, frozen, minutes)
    best_head = max(HEADS, key=lambda h: np.mean([r[h] for r in rows]))
    print(f"\n46-way best: {best_head} "
          f"{np.mean([r[best_head] for r in rows]) * 100:.1f}% "
          f"(frozen mean_token 120s 36.7%)")
    print(f"results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
