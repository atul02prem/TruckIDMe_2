"""Fine-tuned Mantis reading out at block 1, on the test split.

## Why this exists

The frozen layer profile (`layer_profile.md`) moved the frozen arm from block
index 2 to index 0 under a pre-registered rule: driver information sits in the
early blocks. Every fine-tuned result so far trained through block index 2.
Step 1 (`round1.py --layer 0`) decides on inner validation whether the
fine-tuned arm should read out at index 0 too. This script runs only if it does,
and reports that configuration on test.

## What is fixed before this runs

| | |
|---|---|
| block | index 0 (block 1 of 6), from Step 1's rule |
| window | chosen on Step 1's inner validation; passed as `--window` |
| everything else | exp07 Phase B / E: `mean_token`, `np.interp`, `full`, 60 epochs, lr 1e-4, batch 64 |

Nothing here chooses anything. The headline moves to block index 0 because Step
1 met its rule on inner validation; this script measures the result on test.

## What it measures

| Job | Mirrors | Output |
|---|---|---|
| `--partition N` | exp07 Phase B | 36-way closed set (probe / LDA / forest) and open-set AUROC (pre-registered scoring), one 36/10 partition |
| `--seed S` | exp07 Phase E | 46-way closed set, all drivers enrolled, one training seed |

Each job writes its own result file, so jobs can be split across GPUs freely.

## Compared against, all read from disk

| Reference | Source |
|---|---|
| fine-tuned, block index 2, same window, 5 partitions | `round2_cells/interp_{w}s.json` |
| fine-tuned, block index 2, 46-way (30 s only) | exp07 Phase E's saved embeddings, re-scored |
| frozen, block index 0, same window | `exp06/rescore_frozen_cells.json` |

## Commands

```bash
CUDA_VISIBLE_DEVICES=0 python -u -m experiments.exp08_layer_resampling.block1_test \\
    --window 30 --partition 1 --partition 2 --partition 3 --seed 42
CUDA_VISIBLE_DEVICES=1 python -u -m experiments.exp08_layer_resampling.block1_test \\
    --window 30 --partition 4 --partition 5 --seed 1337
python -u -m experiments.exp08_layer_resampling.block1_test --window 30 --summarise
```
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from experiments.exp08_layer_resampling.round1 import load_tensor
from src.config import DATA_INTERIM
from src.models.finetune import BATCH_SIZE, build_model, EPOCHS, LEARNING_RATE
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, PRE_REGISTERED,
                                 score_config, SEED)
from src.models.readouts import closed_set_heads, HEADS
from src.models.splits import (known_train_index, known_unknown_partitions,
                               split_by_driver)

BLOCK = 0
RESULT_DIR = Path(__file__).parent / "block1_test_cells"
ROUND2_DIR = Path(__file__).parent / "round2_cells"
FROZEN_CELLS = (Path(__file__).parents[1] / "exp06_encoder_readout"
                / "rescore_frozen_cells.json")
PHASE_E_SEEDS = (42, 1337)


def fine_tune(tensor: np.ndarray, drivers: np.ndarray, fit_index: np.ndarray,
              seed: int) -> tuple[np.ndarray, float]:
    """Fine-tune Mantis reading out at block index 0, then embed every window.

    Args:
        tensor: (n_windows, n_channels, 512) input.
        drivers: driver id per window.
        fit_index: training window positions.
        seed: seed for initialisation and batch order.

    Returns:
        (embeddings for every window, minutes taken).
    """
    codes = np.full(len(drivers), -1, dtype=np.int64)
    for code, driver in enumerate(np.unique(drivers[fit_index])):
        codes[drivers == driver] = code
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = build_model(BLOCK)
    clock = time.perf_counter()
    model.fit(tensor[fit_index], codes[fit_index], fine_tuning_type="full",
              adapter=None, num_epochs=EPOCHS, batch_size=BATCH_SIZE,
              base_learning_rate=LEARNING_RATE)
    minutes = (time.perf_counter() - clock) / 60
    features = model.transform(tensor, batch_size=256)
    del model
    torch.cuda.empty_cache()
    return features, minutes


def run_partition(window: float, partition: int) -> None:
    """Phase B mirror: one 36/10 partition, closed and open set.

    Args:
        window: window length in seconds.
        partition: 1-based partition number.
    """
    cached = load_tensor(window, "interp")
    tensor, drivers, starts = cached["X"], cached["driver"], cached["start_time"]
    known, unknown = known_unknown_partitions(
        drivers, n_unknown=N_UNKNOWN, n_partitions=N_PARTITIONS,
        seed=SEED)[partition - 1]
    fit_index = known_train_index(drivers, starts, known)
    features, minutes = fine_tune(tensor, drivers, fit_index, SEED)
    np.savez_compressed(
        DATA_INTERIM / f"embeddings_block1ft_{window:g}s_p{partition}.npz",
        E=features, driver=drivers, start_time=starts,
        channels=cached["channels"], known=known, unknown=unknown)

    heads = closed_set_heads(features, drivers, starts, known)
    window_auroc, driver_auroc = score_config(
        {"E": features, "driver": drivers, "start_time": starts,
         "known": known, "unknown": unknown}, PRE_REGISTERED)
    result = {"partition": partition, "minutes": minutes,
              **{h: heads[h][1] for h in HEADS},
              "window_auroc": window_auroc, "driver_auroc": driver_auroc}
    (RESULT_DIR / f"{window:g}s_p{partition}.json").write_text(
        json.dumps(result, indent=2))
    print(f"p{partition}: {minutes:.1f} min | LDA "
          f"{result['lda_centroid'] * 100:.1f}% | driver AUROC "
          f"{driver_auroc:.3f}", flush=True)


def run_seed(window: float, seed: int) -> None:
    """Phase E mirror: all 46 drivers enrolled, one training seed.

    Args:
        window: window length in seconds.
        seed: training seed.
    """
    cached = load_tensor(window, "interp")
    tensor, drivers, starts = cached["X"], cached["driver"], cached["start_time"]
    fit_index, _ = split_by_driver(drivers, starts)
    features, minutes = fine_tune(tensor, drivers, fit_index, seed)
    np.savez_compressed(
        DATA_INTERIM / f"embeddings_block1ft_46way_{window:g}s_s{seed}.npz",
        E=features, driver=drivers, start_time=starts,
        channels=cached["channels"])

    heads = closed_set_heads(features, drivers, starts, np.unique(drivers))
    result = {"seed": seed, "minutes": minutes,
              **{h: heads[h][1] for h in HEADS}}
    (RESULT_DIR / f"{window:g}s_46way_s{seed}.json").write_text(
        json.dumps(result, indent=2))
    print(f"46-way seed {seed}: {minutes:.1f} min | LDA "
          f"{result['lda_centroid'] * 100:.1f}%", flush=True)


def phase_e_reference(window: float) -> list[float] | None:
    """46-way LDA for fine-tuned block index 2, re-scored from Phase E's files.

    Args:
        window: window length in seconds.

    Returns:
        LDA top-1 per seed, or None when Phase E did not run at this window.
    """
    paths = [DATA_INTERIM / f"embeddings_46way_mean_token_{window:g}s_s{s}.npz"
             for s in PHASE_E_SEEDS]
    if not all(p.exists() for p in paths):
        return None
    values = []
    for path in paths:
        saved = np.load(path, allow_pickle=True)
        heads = closed_set_heads(saved["E"], saved["driver"],
                                 saved["start_time"], np.unique(saved["driver"]))
        values.append(heads["lda_centroid"][1])
    return values


def mean_sd(values: list[float], percent: bool) -> str:
    """Format a mean ± sd.

    Args:
        values: one value per partition or seed.
        percent: format as a percentage.

    Returns:
        Formatted string.
    """
    if percent:
        return f"{np.mean(values) * 100:.1f}% ± {np.std(values) * 100:.1f}"
    return f"{np.mean(values):.3f} ± {np.std(values):.3f}"


def summarise(window: float) -> None:
    """Write the comparison report, block index 0 against its references.

    Args:
        window: window length in seconds.
    """
    ours = [json.loads(p.read_text()) for p in
            sorted(RESULT_DIR.glob(f"{window:g}s_p*.json"))]
    seeds = [json.loads(p.read_text()) for p in
             sorted(RESULT_DIR.glob(f"{window:g}s_46way_s*.json"))]
    block3 = json.loads((ROUND2_DIR / f"interp_{window:g}s.json").read_text())
    block3_rows = {r["partition"]: r for r in block3["rows"]}
    frozen = json.loads(FROZEN_CELLS.read_text()).get(f"mean_token|{window:g}|0")
    reference_46 = phase_e_reference(window)

    lines = [
        f"# exp08 — fine-tuned Mantis reading out at block 1, {window:g} s, test",
        "",
        "Block index 0 (the output after block 1 of 6) was chosen for the "
        "fine-tuned arm on inner validation (`round1.py --layer 0`, Step 1). "
        "Everything else matches exp07 Phases B and E. Every number below is on "
        "the **test** split.",
        "",
        "## Closed set (46-way) and open set (36 enrolled / 10 strangers)",
        "",
        "| Arm | Block | 46-way LDA | 36-way LDA | driver AUROC | window AUROC |",
        "|---|---|--:|--:|--:|--:|",
    ]
    if frozen:
        lines.append(
            f"| frozen | 1 of 6 | {frozen['closed46']['lda_centroid'] * 100:.1f}% | "
            + mean_sd([r["lda_centroid"] for r in frozen["partitions"]], True)
            + " | " + mean_sd([r["driver_auroc"] for r in frozen["partitions"]],
                              False)
            + " | " + mean_sd([r["window_auroc"] for r in frozen["partitions"]],
                              False) + " |")
    ref46 = mean_sd(reference_46, True) if reference_46 else "not run"
    lines.append(
        f"| fine-tuned | 3 of 6 | {ref46} | "
        + mean_sd([r["lda_centroid"] for r in block3["rows"]], True) + " | "
        + mean_sd([r["driver_auroc"] for r in block3["rows"]], False) + " | "
        + mean_sd([r["window_auroc"] for r in block3["rows"]], False) + " |")
    if ours:
        ours46 = (mean_sd([s["lda_centroid"] for s in seeds], True)
                  if seeds else "pending")
        lines.append(
            f"| **fine-tuned** | **1 of 6** | **{ours46}** | **"
            + mean_sd([r["lda_centroid"] for r in ours], True) + "** | **"
            + mean_sd([r["driver_auroc"] for r in ours], False) + "** | **"
            + mean_sd([r["window_auroc"] for r in ours], False) + "** |")

    paired = [(r, block3_rows[r["partition"]]) for r in ours
              if r["partition"] in block3_rows]
    if paired:
        lda = [a["lda_centroid"] - b["lda_centroid"] for a, b in paired]
        drv = [a["driver_auroc"] - b["driver_auroc"] for a, b in paired]
        lines += [
            "",
            "## Paired against fine-tuned block 3, same partitions",
            "",
            "| | mean difference | partitions improved |",
            "|---|--:|--:|",
            f"| 36-way LDA | {np.mean(lda) * 100:+.1f}pp | "
            f"{sum(d > 0 for d in lda)} of {len(lda)} |",
            f"| driver AUROC | {np.mean(drv):+.3f} | "
            f"{sum(d > 0 for d in drv)} of {len(drv)} |",
        ]

    lines += [
        "",
        f"Partitions run: {len(ours)} of {N_PARTITIONS}; 46-way seeds run: "
        f"{len(seeds)} of {len(PHASE_E_SEEDS)}. Fine-tuning minutes: "
        + ", ".join(f"{r['minutes']:.1f}" for r in ours + seeds) + ".",
        "",
        "## Limitations",
        "",
        "- One training seed per partition; the 46-way seeds vary training, not "
        "the split.",
        "- The open-set scoring was selected on block-3 fine-tuned embeddings "
        "(exp07) and is not re-tuned for block 1.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    path = Path(__file__).parent / f"block1_test_{window:g}s.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"report -> {path}")


def main() -> None:
    """Run partitions and seeds for one window, or summarise."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, required=True)
    parser.add_argument("--partition", type=int, action="append", default=[])
    parser.add_argument("--seed", type=int, action="append", default=[])
    parser.add_argument("--summarise", action="store_true")
    arguments = parser.parse_args()
    RESULT_DIR.mkdir(exist_ok=True)
    if arguments.summarise:
        summarise(arguments.window)
        return
    for partition in arguments.partition:
        run_partition(arguments.window, partition)
    for seed in arguments.seed:
        run_seed(arguments.window, seed)


if __name__ == "__main__":
    main()
