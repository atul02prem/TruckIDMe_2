"""Phase A — does the frozen window ranking survive fine-tuning?

## The question

exp06 ranked window lengths on a **frozen** encoder and 90 s won. That ranking
cannot simply be carried over to the fine-tuned arm, because the two arms want
opposite things:

| Arm | prefers | why |
|---|---|---|
| frozen | **long** windows | more averaging per window gives a cleaner embedding for a centroid/LDA read-out |
| full | **short** windows | far more training examples — 2,691 windows at 30 s against 654 at 120 s, for 8.6M parameters |

exp04 Stage 1 established that training-set size is the binding constraint for
fine-tuning (100% train accuracy by epoch 40, ~+70pp generalisation gap), so the
frozen optimum may be close to the worst choice for `full`. exp05 already showed
the optimum moves when only the *read-out* changes — the linear probe peaked at
51.2 s while LDA rose monotonically to 120 s. Fine-tuning is a far larger change
than swapping a read-out.

Carrying the frozen answer forward would repeat the `cls_token` error: a choice
validated under one configuration and silently reused in another.

## Selection is made on inner validation, not test

Ranking windows by test accuracy would make the eventual test number a maximum
over four draws. So the encoder is fine-tuned on **inner-train only**:

    known drivers' windows
      └─ chronological 70/5/25  ->  KNOWN-TRAIN (70%)        TEST  <- untouched
                                      └─ chronological 70/5/25
                                          inner-train         INNER-VAL
                                          (encoder fits here)  (window chosen here)

`closed_set_heads` applies the same per-driver chronological split to whatever
it receives, so handing it the known-train subset reproduces exactly the inner
split the encoder was fitted on — the read-outs train on inner-train and score
on inner-val, and no test window is touched anywhere in this script.

## Pinned

| | |
|---|---|
| Arm | `full` — all 8,590,372 parameters updated from the pre-trained checkpoint |
| Output token | **`mean_token`** — confirmed on inner validation at 4/4 window lengths, margins 7.3–12.4pp |
| Epochs | 60 |
| Partitions | **1** (the first 36-known/10-unknown draw, seed 42) |
| Windows | 30 / 51.2 / 90 / 120 s |

One partition means the ranking carries single-split uncertainty. Stated before
seeing any number: **if the top two windows land within 2pp, the tiebreak is
the larger training set**, not a re-run.

## Embeddings are saved

exp04 discarded its fine-tuned weights, which is why the energy-score and
adapted-read-out questions could not be answered without a 3.7 h refit. Every
embedding produced here is written to `data/interim_data/`, so Phase C's
scoring sweep — and any rule invented later — costs nothing.

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_a
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

from src.config import DATA_INTERIM, MANTIS_CHECKPOINT, MANTIS_LAYER
from src.features.build_tensors import tensor_path
from src.models.finetune import BATCH_SIZE, EPOCHS, LEARNING_RATE, OUTPUT_TOKEN
from src.models.open_set import N_PARTITIONS, N_UNKNOWN, SEED
from src.models.readouts import closed_set_heads, HEADS
from src.models.splits import (inner_train_index, known_train_index,
                               known_unknown_partitions, split_by_driver)

WINDOWS = (30.0, 51.2, 90.0, 120.0)
TIEBREAK_PP = 2.0
RESULTS_PATH = Path(__file__).parent / "phase_a.md"


def embedding_out_path(window_seconds: float) -> Path:
    """Where this phase saves one window length's fine-tuned embeddings.

    Args:
        window_seconds: window length.

    Returns:
        Path under `data/interim_data/`.
    """
    return DATA_INTERIM / f"embeddings_full_{OUTPUT_TOKEN}_{window_seconds:g}s.npz"


def fine_tune(windows: np.ndarray, labels: np.ndarray, fit_index: np.ndarray,
              device: str) -> tuple[MantisTrainer, float]:
    """Fine-tune the whole encoder on one set of windows.

    Args:
        windows: (n_windows, n_channels, 512) tensor.
        labels: integer driver label per window, valid on fit_index.
        fit_index: positions the encoder is fitted on.
        device: torch device string.

    Returns:
        (fitted trainer, minutes taken).
    """
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    network = MantisV1(device=device, return_transf_layer=MANTIS_LAYER,
                       output_token=OUTPUT_TOKEN).from_pretrained(MANTIS_CHECKPOINT)
    model = MantisTrainer(device=device, network=network)
    clock = time.perf_counter()
    model.fit(windows[fit_index], labels[fit_index], fine_tuning_type="full",
              adapter=None, num_epochs=EPOCHS, batch_size=BATCH_SIZE,
              base_learning_rate=LEARNING_RATE)
    return model, (time.perf_counter() - clock) / 60


def write_report(rows: list[dict], winner: float, tiebroken: bool) -> None:
    """Write the Phase A report inside the experiment folder.

    Args:
        rows: one dict per window length.
        winner: the chosen window length.
        tiebroken: whether the choice came from the training-set-size tiebreak.
    """
    lines = [
        "# exp07 Phase A — window length for the fine-tuned arm",
        "",
        f"`full` fine-tuning with **`{OUTPUT_TOKEN}`**, {EPOCHS} epochs, one "
        "36-known/10-unknown partition (seed 42). The encoder is fitted on "
        "**inner-train only** and every number below is **inner-validation** — "
        "no test window is touched, so the window can be chosen here without "
        "biasing the eventual test result.",
        "",
        "Chance is 2.8% (36 enrolled drivers).",
        "",
        "| Window | Encoder fit on | linear probe | LDA + centroid | "
        "random forest | best | fit min |",
        "|---|--:|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        cells = " | ".join(f"{row[h] * 100:.1f}%" for h in HEADS)
        best = max(row[h] for h in HEADS) * 100
        mark = " ✅" if row["window"] == winner else ""
        lines.append(f"| {row['window']:g} s{mark} | {row['n_fit']:,} | "
                     f"{cells} | **{best:.1f}%** | {row['minutes']:.1f} |")

    ordered = sorted(rows, key=lambda r: -max(r[h] for h in HEADS))
    gap = (max(ordered[0][h] for h in HEADS)
           - max(ordered[1][h] for h in HEADS)) * 100
    lines += [
        "",
        f"Top two separated by **{gap:.1f}pp**"
        + (f" — inside the {TIEBREAK_PP:g}pp tiebreak band, so the window with "
           "the larger training set was taken, as pre-committed."
           if tiebroken else
           f", outside the {TIEBREAK_PP:g}pp tiebreak band.")
        + f" **Chosen: {winner:g} s.**",
        "",
        "## Frozen comparison",
        "",
        "The frozen ranking on inner validation (`exp06/confirm_token.md`, "
        "46-way so not directly comparable in level, only in order) was "
        "90 s > 120 s > 51.2 s > 30 s. Whether the fine-tuned arm agrees is "
        "the question this phase exists to answer — the two arms were expected "
        "to disagree, because fine-tuning is limited by training-set size and "
        "frozen read-outs are not.",
        "",
        "## Saved artefacts",
        "",
        "Fine-tuned embeddings are written to `data/interim_data/` as "
        f"`embeddings_full_{OUTPUT_TOKEN}_<window>s.npz`, so Phase C's scoring "
        "sweep and any later scoring rule cost no GPU time. exp04 discarded "
        "its weights and paid for it.",
        "",
        "## Limitations",
        "",
        "- **One partition.** The ranking carries single-split uncertainty; "
        f"the {TIEBREAK_PP:g}pp tiebreak rule was fixed before the run.",
        "- **Encoder fitted on inner-train (~70% of known-train)**, so these "
        "accuracies sit below what Phase B will produce from the full "
        "training set. Compare windows within this table, not against others.",
        "- Read-out layer fixed at 2. The Mantis paper reports intermediate "
        "layers help *frozen* extraction specifically, so layer 6 may suit the "
        "fine-tuned arm better — untested.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Fine-tune at every window length and rank them on inner validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, action="append", default=None)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    arguments = parser.parse_args()
    windows_wanted = arguments.window or list(WINDOWS)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows: list[dict] = []

    for window in windows_wanted:
        cached = np.load(tensor_path(window), allow_pickle=True)
        tensor, drivers = cached["X"], cached["driver"]
        starts, channels = cached["start_time"], cached["channels"]
        known, unknown = known_unknown_partitions(
            drivers, n_unknown=N_UNKNOWN, n_partitions=N_PARTITIONS,
            seed=SEED)[0]

        fit_index, known_train = inner_train_index(drivers, starts, known)
        codes = np.full(len(drivers), -1, dtype=np.int64)
        for code, driver in enumerate(np.unique(drivers[fit_index])):
            codes[drivers == driver] = code

        print(f"\n=== {window:g} s | {tensor.shape} | "
              f"encoder fits on {len(fit_index):,} inner-train windows ===")
        model, minutes = fine_tune(tensor, codes, fit_index, device)
        features = model.transform(tensor, batch_size=256)

        np.savez_compressed(embedding_out_path(window), E=features,
                            driver=drivers, start_time=starts,
                            channels=channels)

        heads = closed_set_heads(features[known_train], drivers[known_train],
                                 starts[known_train], known)
        row = {"window": window, "n_fit": len(fit_index), "minutes": minutes,
               **{h: heads[h][1] for h in HEADS}}
        rows.append(row)
        print(f"  fitted in {minutes:.1f} min -> {features.shape} | "
              + "  ".join(f"{h.split('_')[0]} {row[h] * 100:5.1f}%"
                          for h in HEADS)
              + f" | best {max(row[h] for h in HEADS) * 100:.1f}%")
        print(f"  embeddings -> {embedding_out_path(window).name}")

    ordered = sorted(rows, key=lambda r: -max(r[h] for h in HEADS))
    gap = (max(ordered[0][h] for h in HEADS)
           - max(ordered[1][h] for h in HEADS)) * 100
    tiebroken = gap < TIEBREAK_PP
    winner = (max(ordered[:2], key=lambda r: r["n_fit"])["window"]
              if tiebroken else ordered[0]["window"])

    write_report(rows, winner, tiebroken)
    print(f"\ntop two differ by {gap:.1f}pp"
          + (" -> tiebreak on training-set size" if tiebroken else ""))
    print(f"chosen window: {winner:g} s")
    print(f"results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
