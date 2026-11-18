"""Does the output token matter once the encoder is fine-tuned?

exp06 chose `mean_token` on the **frozen** encoder (`confirm_token.md`, inner
validation, all four windows). The fine-tuned arm inherited that choice without
its own comparison. Fine-tuning retrains every layer, including the CLS slot, so
the frozen ranking need not carry over. This run measures it.

## Pre-registered, before any result

**The headline stays `mean_token` whatever this run shows.** The comparison is
scored on the test split, and switching token after seeing test numbers would be
selecting on test. This run reports whether the token matters for the fine-tuned
arm; it does not choose one.

## Configuration — identical to exp07 Phase B except the token

| | |
|---|---|
| tokens | `cls_token`, `combined` (fine-tuned here); `mean_token` re-scored from Phase B's saved embeddings |
| window | 30 s, `np.interp` |
| arm | `full`, 60 epochs, lr 1e-4, batch 64, seed 42, read-out layer 2 |
| partitions | the five exp07 partitions (36 known / 10 unknown, seed 42) |
| closed set | linear probe, LDA + centroid, random forest, 36-way |
| open set | exp07's pre-registered scoring (LDA, L2-normalise then whiten, mean prototype, cosine) |

`combined` is 512 dims per channel (25,600 features); Mantis doubles
`hidden_dim` for it, so the fine-tuning head is sized correctly.

## Commands

```bash
CUDA_VISIBLE_DEVICES=0 python -u -m experiments.exp06_encoder_readout.full_token --token cls_token
CUDA_VISIBLE_DEVICES=1 python -u -m experiments.exp06_encoder_readout.full_token --token combined
python -u -m experiments.exp06_encoder_readout.full_token --token mean_token   # re-score only
python -u -m experiments.exp06_encoder_readout.full_token --summarise
```
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from src.config import DATA_INTERIM
from src.features.build_tensors import tensor_path
from src.models.finetune import BATCH_SIZE, build_model, EPOCHS, LEARNING_RATE
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, PRE_REGISTERED,
                                 score_config, SEED)
from src.models.readouts import closed_set_heads
from src.models.splits import known_train_index, known_unknown_partitions

WINDOW_SECONDS = 30.0
READOUT_LAYER = 2
TOKENS = ("cls_token", "mean_token", "combined")
HEADLINE_TOKEN = "mean_token"
HEADS = ("linear_probe", "lda_centroid", "random_forest")
CELL_DIR = Path(__file__).parent / "full_token_cells"
RESULTS_PATH = Path(__file__).parent / "full_token.md"


def embedding_path(token: str, partition: int) -> Path:
    """Where one token's fine-tuned embeddings for one partition live.

    `mean_token` points at exp07 Phase B's files, so the headline is re-scored
    rather than re-trained.

    Args:
        token: output token.
        partition: 1-based partition number.

    Returns:
        Path under `data/interim_data/`.
    """
    if token == HEADLINE_TOKEN:
        return DATA_INTERIM / f"embeddings_phaseB_mean_token_30s_p{partition}.npz"
    return DATA_INTERIM / f"embeddings_exp06full_{token}_30s_p{partition}.npz"


def fine_tune(tensor: np.ndarray, drivers: np.ndarray, fit_index: np.ndarray,
              token: str) -> tuple[np.ndarray, float]:
    """Fine-tune Mantis on the known drivers' training windows and embed all.

    Args:
        tensor: (n_windows, n_channels, 512) input.
        drivers: driver id per window.
        fit_index: training window positions of the known drivers.
        token: output token.

    Returns:
        (embeddings for every window, minutes taken).
    """
    codes = np.full(len(drivers), -1, dtype=np.int64)
    for code, driver in enumerate(np.unique(drivers[fit_index])):
        codes[drivers == driver] = code
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    model = build_model(READOUT_LAYER, token=token)
    clock = time.perf_counter()
    model.fit(tensor[fit_index], codes[fit_index], fine_tuning_type="full",
              adapter=None, num_epochs=EPOCHS, batch_size=BATCH_SIZE,
              base_learning_rate=LEARNING_RATE)
    minutes = (time.perf_counter() - clock) / 60
    features = model.transform(tensor, batch_size=256)
    del model
    torch.cuda.empty_cache()
    return features, minutes


def run_token(token: str) -> None:
    """Fine-tune (or reuse) and score every partition for one token.

    Args:
        token: output token.
    """
    cached = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=True)
    tensor, drivers = cached["X"], cached["driver"]
    starts, channels = cached["start_time"], cached["channels"]
    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=N_PARTITIONS, seed=SEED)
    CELL_DIR.mkdir(exist_ok=True)
    out_path = CELL_DIR / f"{token}.json"
    rows = []

    for index, (known, unknown) in enumerate(partitions, start=1):
        path = embedding_path(token, index)
        minutes = 0.0
        if not path.exists():
            fit_index = known_train_index(drivers, starts, known)
            features, minutes = fine_tune(tensor, drivers, fit_index, token)
            np.savez_compressed(path, E=features, driver=drivers,
                                start_time=starts, channels=channels,
                                known=known, unknown=unknown)

        saved = np.load(path, allow_pickle=True)
        heads = closed_set_heads(saved["E"], drivers, starts, known)
        window_auroc, driver_auroc = score_config(saved, PRE_REGISTERED)
        rows.append({"partition": index, "minutes": minutes,
                     "features": int(saved["E"].shape[1]),
                     **{h: heads[h][1] for h in HEADS},
                     "window_auroc": window_auroc,
                     "driver_auroc": driver_auroc})
        out_path.write_text(json.dumps({"token": token, "rows": rows}, indent=2))
        print(f"{token} p{index}: "
              f"{'reused' if minutes == 0 else f'{minutes:.1f} min'} | "
              f"{saved['E'].shape[1]} features | "
              f"LDA {heads['lda_centroid'][1] * 100:.1f}% | open-set window "
              f"{window_auroc:.3f} driver {driver_auroc:.3f}", flush=True)


def mean_sd(values: list[float], percent: bool) -> str:
    """Format a mean ± sd over partitions.

    Args:
        values: one value per partition.
        percent: format as a percentage.

    Returns:
        Formatted string.
    """
    if percent:
        return f"{np.mean(values) * 100:.1f}% ± {np.std(values) * 100:.1f}"
    return f"{np.mean(values):.3f} ± {np.std(values):.3f}"


def summarise() -> None:
    """Merge the three tokens into the report, paired against `mean_token`."""
    results = {}
    for token in TOKENS:
        path = CELL_DIR / f"{token}.json"
        if path.exists():
            results[token] = json.loads(path.read_text())["rows"]
    if HEADLINE_TOKEN not in results:
        raise FileNotFoundError(f"run --token {HEADLINE_TOKEN} first")

    lines = [
        "# exp06 — output token on the fine-tuned encoder",
        "",
        "`full` fine-tuning, 30 s, `np.interp`, layer 2, the five exp07 "
        "partitions (36 known / 10 unknown). Every number is on the **test** "
        "split; mean ± sd over partitions. Open set uses exp07's pre-registered "
        "scoring.",
        "",
        "**Pre-registered:** the headline stays `mean_token` whatever this shows. "
        "This run reports whether the token matters after fine-tuning; it does "
        "not choose one.",
        "",
        "| Token | Features | partitions | probe | LDA | forest | window AUROC "
        "| driver AUROC |",
        "|---|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for token, rows in results.items():
        lines.append(
            f"| `{token}` | {rows[0]['features']:,} | {len(rows)} | "
            + " | ".join(mean_sd([r[h] for r in rows], True) for h in HEADS)
            + f" | {mean_sd([r['window_auroc'] for r in rows], False)}"
            + f" | {mean_sd([r['driver_auroc'] for r in rows], False)} |")

    base = {r["partition"]: r for r in results[HEADLINE_TOKEN]}
    lines += [
        "",
        "## Paired differences against `mean_token`",
        "",
        "| Token | LDA | driver AUROC | partitions where LDA improved "
        "| partitions where driver AUROC improved |",
        "|---|--:|--:|--:|--:|",
    ]
    for token, rows in results.items():
        if token == HEADLINE_TOKEN:
            continue
        paired = [(r, base[r["partition"]]) for r in rows
                  if r["partition"] in base]
        lda = [r["lda_centroid"] - b["lda_centroid"] for r, b in paired]
        drv = [r["driver_auroc"] - b["driver_auroc"] for r, b in paired]
        lines.append(
            f"| `{token}` | {np.mean(lda) * 100:+.1f}pp | {np.mean(drv):+.3f} | "
            f"{sum(d > 0 for d in lda)} of {len(paired)} | "
            f"{sum(d > 0 for d in drv)} of {len(paired)} |")

    lines += [
        "",
        "## Limitations",
        "",
        "- One seed; partitions vary the driver draw, not training noise.",
        "- 30 s only, the fine-tuned arm's window from exp07 Phase A.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print(f"report -> {RESULTS_PATH}")


def main() -> None:
    """Run one token, or merge all into the report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", choices=TOKENS)
    parser.add_argument("--summarise", action="store_true")
    arguments = parser.parse_args()
    if arguments.summarise:
        summarise()
    elif arguments.token:
        run_token(arguments.token)
    else:
        parser.error("give --token or --summarise")


if __name__ == "__main__":
    main()
