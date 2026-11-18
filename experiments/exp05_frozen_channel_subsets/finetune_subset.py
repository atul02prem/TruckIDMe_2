"""Fine-tune the Mantis encoder on the 11 driver-actuated channels.

## What this adds that `run.py` cannot

`run.py` slices the cached frozen embedding and retrains only the read-out. The
encoder's weights never move, so it answers "does the classifier need all 50
channels?" but not "would the encoder be better if it had only ever seen the 11?"

This script answers the second question by actually fine-tuning: the encoder is
fed an (n_windows, 11, 512) tensor and all 8.1M encoder parameters are updated,
exactly as exp04's `full` arm was, with the channel count as the only change.

Together with exp04 that completes a 2x2:

|            | 50 channels          | 11 channels          |
|------------|----------------------|----------------------|
| frozen     | exp04 `frozen`       | `run.py` `actuated11`|
| fine-tuned | exp04 `full`         | **this script**      |

## Why it is cheap

Mantis encodes one channel at a time, so a training step costs one encoder pass
per channel: 64 x 50 = 3,200 passes per batch at 50 channels, 64 x 11 = 704 at
11. exp04 measured 22.3 min per arm per partition at 50 channels, so 11 channels
should land near 5 min — roughly 25 min for all five partitions.

## Held fixed against exp04

Same five group-stratified 36-known/10-unknown partitions at seed 42, the same
per-driver chronological 70/5/25 split, the same 100-epoch budget, the same
`encoder.py` hyperparameters, the same read-outs and the same open-set scoring.
**The channel set is the only variable**, which is what makes the comparison
against exp04's 33.2% mean anything.

## Commands

```bash
python -u -m experiments.exp05_frozen_channel_subsets.finetune_subset
python -u -m experiments.exp05_frozen_channel_subsets.finetune_subset --arm full --arm scratch
```
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from experiments.exp04_open_set_finetune.run import adapted_embeddings
from experiments.exp05_frozen_channel_subsets.run import (ACTUATED,
                                                          WINDOW_SECONDS)
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, SEED,
                                 evaluate_partition, summarise)
from src.models.splits import known_unknown_partitions
from src.models.readouts import average_heads, closed_set_heads
from src.features.build_tensors import tensor_path

EPOCHS = 100            # pinned to exp04 so the comparison is like-for-like
RULES = ("euclidean", "cosine", "ratio", "mahalanobis", "msp")
RESULTS_PATH = Path(__file__).parent / "finetune_subset.md"

# exp04's 50-channel numbers at 36-way, for the 2x2. Restated here rather than
# parsed out of that report so this file is readable on its own; they are the
# mean +/- sd over the same five partitions.
EXP04_REFERENCE = {
    "frozen": {"linear_probe": 26.2, "lda_centroid": 28.7, "random_forest": 21.2},
    "full": {"linear_probe": 30.1, "lda_centroid": 33.2, "random_forest": 31.8},
}


def channel_index(channels: np.ndarray, wanted: tuple[str, ...]) -> np.ndarray:
    """Positions of the wanted channels in the tensor's channel axis.

    Args:
        channels: channel names in tensor order.
        wanted: channel names to keep.

    Returns:
        Ascending positions into the channel axis.

    Raises:
        ValueError: if any wanted channel is absent.
    """
    names = [str(c) for c in channels]
    missing = [w for w in wanted if w not in names]
    if missing:
        raise ValueError(f"channels not in the tensor: {missing}")
    return np.array(sorted(names.index(w) for w in wanted))


def write_report(open_rows: dict[str, list[dict]],
                 head_rows: dict[str, list[dict]],
                 minutes: dict[str, list[float]], n_channels: int) -> None:
    """Write the results report inside the experiment folder.

    Args:
        open_rows: {arm: per-partition open-set result dicts}.
        head_rows: {arm: per-partition closed-set read-out dicts}.
        minutes: {arm: per-partition fine-tuning minutes}.
        n_channels: how many channels the encoder was fine-tuned on.
    """
    lines = [
        f"# exp05 — Mantis fine-tuned on {n_channels} driver-actuated channels",
        "",
        f"The encoder is fine-tuned on an (n_windows, {n_channels}, 512) tensor "
        f"instead of the 50-channel one, producing {n_channels} x 256 = "
        f"{n_channels * 256:,}-dim embeddings. Five group-stratified 36-known / "
        "10-unknown partitions, seed 42, 100 epochs, per-driver chronological "
        "70/5/25 split — all identical to exp04, so **the channel set is the "
        "only variable**. Values are mean ± sd across partitions.",
        "",
        f"Channels: {', '.join(f'SPN {c}' for c in ACTUATED)}",
        "",
        "## Closed set — 36-way, chance 2.8%",
        "",
        "| Arm | linear probe | LDA + centroid | random forest |",
        "|---|--:|--:|--:|",
    ]
    for arm, rows in head_rows.items():
        averaged = average_heads(rows)
        cells = " | ".join(
            f"**{averaged[h][1][0] * 100:.1f}%** ± {averaged[h][1][1] * 100:.1f}%"
            for h in ("linear_probe", "lda_centroid", "random_forest"))
        lines.append(f"| `{arm}` ({n_channels} ch) | {cells} |")
    for arm, reference in EXP04_REFERENCE.items():
        cells = " | ".join(f"{reference[h]:.1f}%" for h in
                           ("linear_probe", "lda_centroid", "random_forest"))
        lines.append(f"| `{arm}` (50 ch, exp04) | {cells} |")

    lines += [
        "",
        "## Open set — rejecting the never-enrolled",
        "",
        "AUROC by scoring rule; **0.500 is chance**. exp04's 50-channel `full` "
        "reached 0.514 (`mahalanobis`) and its random-initialisation arm reached "
        "0.516, so this column was not expected to move.",
        "",
        "| Arm | " + " | ".join(f"`{r}`" for r in RULES) + " |",
        "|---|" + "--:|" * len(RULES),
    ]
    for arm, rows in open_rows.items():
        summary = summarise(rows)
        cells = " | ".join(f"{summary[f'auroc:{r}'][0]:.3f} ± "
                           f"{summary[f'auroc:{r}'][1]:.3f}" for r in RULES)
        lines.append(f"| `{arm}` | {cells} |")

    lines += [
        "",
        "## Cost",
        "",
        "| Arm | mean minutes per partition |",
        "|---|--:|",
    ]
    for arm, values in minutes.items():
        lines.append(f"| `{arm}` | {np.mean(values):.1f} |")

    lines += [
        "",
        "exp04 measured 22.3 min per arm per partition at 50 channels. The "
        "encoder runs once per channel, so the cost is expected to scale with "
        "the channel count.",
        "",
        "## Limitations",
        "",
        "- **The channel set was not chosen blind.** The driver-actuated SPNs "
        "were selected on mechanistic grounds before seeing any accuracy, but "
        "they are one hypothesis among many; `run.py`'s `random11` control is "
        "what bounds how much of any difference is just dimensionality.",
        "- Fixed 100-epoch budget, final epoch, no model selection, matching "
        "exp04.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Fine-tune each arm on the channel subset across all partitions."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", action="append", choices=("full", "scratch"),
                        default=None)
    parser.add_argument("--partitions", type=int, default=N_PARTITIONS)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    arguments = parser.parse_args()
    arms = tuple(arguments.arm or ("full",))

    cached = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=True)
    keep = channel_index(cached["channels"], ACTUATED)
    windows = np.ascontiguousarray(cached["X"][:, keep, :])
    drivers, starts = cached["driver"], cached["start_time"]
    print(f"{windows.shape} tensor | {len(np.unique(drivers))} drivers | "
          f"arms {arms} | {arguments.epochs} epochs")

    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=arguments.partitions,
                                          seed=SEED)

    open_rows: dict[str, list[dict]] = {a: [] for a in arms}
    head_rows: dict[str, list[dict]] = {a: [] for a in arms}
    minutes: dict[str, list[float]] = {a: [] for a in arms}

    for index, (known, unknown) in enumerate(partitions, start=1):
        print(f"\npartition {index}/{len(partitions)}")
        for arm in arms:
            features, spent = adapted_embeddings(arm, windows, drivers, starts,
                                                 known, arguments.epochs)
            minutes[arm].append(spent)
            heads = closed_set_heads(features, drivers, starts, known)
            head_rows[arm].append(heads)
            result = evaluate_partition(features, drivers, starts, known,
                                        unknown)
            open_rows[arm].append(result)
            best = max(RULES, key=lambda r: result["auroc"][r])
            print(f"  {arm:8s} fitted in {spent:.1f} min -> {features.shape} | "
                  f"probe {heads['linear_probe'][1] * 100:.1f}%  "
                  f"LDA {heads['lda_centroid'][1] * 100:.1f}%  "
                  f"AUROC {result['auroc'][best]:.3f} ({best})")
        write_report(open_rows, head_rows, minutes, n_channels=windows.shape[1])
        print(f"  interim results -> {RESULTS_PATH}")

    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
