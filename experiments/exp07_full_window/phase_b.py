"""Phase B — the reportable run: `full` + `mean_token` at 30 s, five partitions.

## What Phase A settled

| | frozen ranking | fine-tuned ranking |
|---|---|---|
| best -> worst | 90 > 120 > 51.2 > **30** | **30** > 90 > 51.2 > 120 |

The frozen best and the frozen worst swap places once the encoder is fine-tuned,
because fine-tuning is limited by training-set size: 30 s supplies 1,462
inner-train windows against 120 s's 341. Phase A chose 30 s on inner validation
by a 2.8pp margin, outside the pre-committed 2pp tiebreak band.

## What this phase does differently from Phase A

Phase A fitted the encoder on **inner-train** so the window could be chosen
without touching test. Here the window is already fixed, so the encoder is
fitted on the **full known-train** set and the test split is evaluated **once**.
These are the numbers that get reported.

Five group-stratified 36-known / 10-unknown partitions, seed 42 — the same
draws exp04 used, so every figure here is directly comparable to exp04's
`cls_token` / 51.2 s results.

## Embeddings are saved per partition

exp04 discarded its fine-tuned weights, which is why its open-set evaluation was
frozen to five scoring rules and could not be extended. Every partition's
embeddings are written out here, so Phase C's scoring sweep — and any rule
invented afterwards — costs no GPU time.

## Pinned

| | |
|---|---|
| Arm | `full`, all 8,590,372 parameters |
| Output token | `mean_token` (inner-validation winner, 4/4 windows, 7.3-12.4pp) |
| Window | 30 s, 512 points -> 17.07 Hz |
| Epochs | 60 |
| Learning rate | 1e-4 (the value the EEG paper used for Mantis) |
| Partitions | 5, seed 42 |

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_b
```
"""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np

from experiments.exp07_full_window.phase_a import fine_tune
from src.config import DATA_INTERIM
from src.features.build_tensors import tensor_path
from src.models.finetune import EPOCHS, OUTPUT_TOKEN
from src.models.open_set import (evaluate_partition, N_PARTITIONS, N_UNKNOWN,
                                 SEED, summarise)
from src.models.readouts import closed_set_heads, HEADS
from src.models.splits import known_train_index, known_unknown_partitions

WINDOW_SECONDS = 30.0        # Phase A's inner-validation winner
RULES = ("euclidean", "cosine", "ratio", "mahalanobis", "msp")
RESULTS_PATH = Path(__file__).parent / "phase_b.md"
CHECKPOINT_PATH = DATA_INTERIM / "exp07_phase_b_checkpoint.pkl"


def embedding_path(partition: int) -> Path:
    """Where one partition's fine-tuned embeddings are saved.

    Args:
        partition: 1-based partition number.

    Returns:
        Path under `data/interim_data/`.
    """
    return (DATA_INTERIM /
            f"embeddings_phaseB_{OUTPUT_TOKEN}_{WINDOW_SECONDS:g}s_p{partition}.npz")


def load_state() -> dict:
    """Resume a partially completed run, or start a fresh one.

    Returns:
        {'open_rows', 'head_rows', 'minutes', 'completed'}.
    """
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open("rb") as handle:
            return pickle.load(handle)
    return {"open_rows": [], "head_rows": [], "minutes": [], "completed": 0}


def save_state(state: dict) -> None:
    """Write the checkpoint atomically.

    Args:
        state: the run state to persist.
    """
    staging = CHECKPOINT_PATH.with_suffix(".tmp")
    with staging.open("wb") as handle:
        pickle.dump(state, handle, protocol=pickle.HIGHEST_PROTOCOL)
    staging.replace(CHECKPOINT_PATH)


def write_report(state: dict) -> None:
    """Write the Phase B report inside the experiment folder.

    Args:
        state: run state holding per-partition results.
    """
    head_rows, open_rows = state["head_rows"], state["open_rows"]
    n = len(head_rows)
    summary = summarise(open_rows) if open_rows else {}
    lines = [
        f"# exp07 Phase B — `full` + `{OUTPUT_TOKEN}` at {WINDOW_SECONDS:g} s",
        "",
        f"**{n} of {N_PARTITIONS} partitions.** Mantis-8M fine-tuned end to end "
        f"({EPOCHS} epochs, all 8,590,372 parameters) on each partition's 36 "
        "known drivers' training windows, then evaluated once on the held-out "
        "test windows. Group-stratified 36-known/10-unknown draws, seed 42 — "
        "the same draws exp04 used. Values are mean ± sd across partitions.",
        "",
        "Window and output token were both selected on **inner validation** "
        "(Phase A and `exp06/confirm_token.md`), so the test split played no "
        "part in configuring this run.",
        "",
        "## Closed set — 36-way, chance 2.8%",
        "",
        "| Configuration | linear probe | LDA + centroid | random forest |",
        "|---|--:|--:|--:|",
    ]
    if head_rows:
        cells = []
        for head in HEADS:
            values = [row[head][1] for row in head_rows]
            cells.append(f"**{np.mean(values) * 100:.1f}%** ± "
                         f"{np.std(values) * 100:.1f}%")
        lines.append(f"| `full` + `{OUTPUT_TOKEN}`, {WINDOW_SECONDS:g} s | "
                     + " | ".join(cells) + " |")
    lines += [
        "| `full` + `cls_token`, 51.2 s (exp04) | 30.1% ± 2.3% | 33.2% ± 2.7% "
        "| 31.8% ± 1.5% |",
        "| `frozen` + `cls_token`, 51.2 s (exp04) | 26.2% ± 1.4% | 28.7% ± 2.7% "
        "| 21.2% ± 0.8% |",
        "",
        "## Open set — rejecting the never-enrolled",
        "",
        "Window-level AUROC; **0.500 is chance**. exp04's `full` reached 0.514 "
        "and its random-initialisation arm reached 0.516. Phase C sweeps the "
        "scoring rules properly on the embeddings this run saves.",
        "",
        "| Rule | " + " | ".join(f"`{r}`" for r in RULES) + " |",
        "|---|" + "--:|" * len(RULES),
    ]
    if summary:
        cells = " | ".join(f"{summary[f'auroc:{r}'][0]:.3f} ± "
                           f"{summary[f'auroc:{r}'][1]:.3f}" for r in RULES)
        lines.append(f"| window-level | {cells} |")
        cells = " | ".join(f"{summary[f'driver_auroc:{r}'][0]:.3f} ± "
                           f"{summary[f'driver_auroc:{r}'][1]:.3f}"
                           for r in RULES)
        lines.append(f"| driver-level | {cells} |")

    if state["minutes"]:
        lines += [
            "",
            f"Fine-tuning cost: **{np.mean(state['minutes']):.1f} min** per "
            "partition.",
        ]
    lines += [
        "",
        "## Saved artefacts",
        "",
        f"`data/interim_data/embeddings_phaseB_{OUTPUT_TOKEN}_"
        f"{WINDOW_SECONDS:g}s_p<N>.npz` — one per partition. Phase C reads "
        "these; no refit is needed to add a scoring rule.",
        "",
        "## Limitations",
        "",
        "- **Fixed 60-epoch budget, final epoch, no model selection.** Immune "
        "to selecting on noise, and forgoes the ~1pp a smoothed-accuracy rule "
        "would buy.",
        "- **Read-out layer fixed at 2.** The Mantis paper reports intermediate "
        "layers help *frozen* extraction; layer 6 may suit fine-tuning better. "
        "Untested.",
        "- **Resampling is `np.interp`**, which aliases on downsample. At 30 s "
        "the grid is 17.07 Hz, above the native rate of 30 of 50 channels, so "
        "this is the window length least affected by that fault.",
        "- One drive per driver, so an unknown driver is also an unknown day. "
        "See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Fine-tune and evaluate every partition, checkpointing as it goes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--partitions", type=int, default=N_PARTITIONS)
    arguments = parser.parse_args()
    if arguments.restart and CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()

    cached = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=True)
    tensor, drivers = cached["X"], cached["driver"]
    starts, channels = cached["start_time"], cached["channels"]
    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=arguments.partitions,
                                          seed=SEED)
    state = load_state()
    print(f"{tensor.shape} | {OUTPUT_TOKEN} | {WINDOW_SECONDS:g} s | "
          f"{EPOCHS} epochs | resuming from partition {state['completed'] + 1}")

    for index, (known, unknown) in enumerate(partitions, start=1):
        if index <= state["completed"]:
            continue
        fit_index = known_train_index(drivers, starts, known)
        codes = np.full(len(drivers), -1, dtype=np.int64)
        for code, driver in enumerate(np.unique(drivers[fit_index])):
            codes[drivers == driver] = code

        print(f"\npartition {index}/{len(partitions)} | "
              f"encoder fits on {len(fit_index):,} windows")
        model, minutes = fine_tune(tensor, codes, fit_index, "cuda")
        features = model.transform(tensor, batch_size=256)
        np.savez_compressed(embedding_path(index), E=features, driver=drivers,
                            start_time=starts, channels=channels,
                            known=known, unknown=unknown)

        heads = closed_set_heads(features, drivers, starts, known)
        result = evaluate_partition(features, drivers, starts, known, unknown)
        state["head_rows"].append(heads)
        state["open_rows"].append(result)
        state["minutes"].append(minutes)
        state["completed"] = index
        save_state(state)
        write_report(state)

        best = max(RULES, key=lambda r: result["auroc"][r])
        print(f"  {minutes:.1f} min | "
              + "  ".join(f"{h.split('_')[0]} {heads[h][1] * 100:5.1f}%"
                          for h in HEADS)
              + f" | AUROC {result['auroc'][best]:.3f} ({best})")
        print(f"  checkpointed {index}/{len(partitions)}")

    write_report(state)
    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
