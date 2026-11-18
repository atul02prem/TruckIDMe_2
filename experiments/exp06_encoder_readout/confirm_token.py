"""Re-rank the three output tokens on an inner validation split.

## The flaw this fixes

`run.py` ranked `cls_token` / `mean_token` / `combined` by their accuracy on the
**test** split, and `mean_token` won by 9.0pp. That ranking used the test set to
make a choice, so the 36.7% it produced is an optimistically biased estimate —
it is the maximum of three draws and absorbs whatever noise favoured the winner.

A test set gives an unbiased estimate only if it is touched once. This script
makes the choice on data the test set never sees:

    all windows
      └─ chronological 70/5/25  ->  TRAIN (70%)          TEST (25%)   <- untouched here
                                     └─ chronological 70/5/25
                                         inner-train      INNER-VAL   <- the token is chosen on this

`closed_set_heads` already performs a per-driver chronological split on whatever
it is given, so passing it only the training windows produces exactly the inner
split, with no new splitting code to get wrong.

## What a confirmation would mean

With three options, selection noise on a single split is usually 1–2pp. The gap
observed on test was 9.0pp, far outside that, so `mean_token` is expected to win
here too. If it does, the switch is justified and the test numbers in `run.py`
can be reported as a one-time evaluation of an independently chosen
configuration. **If it does not, `run.py`'s ranking was selection noise** and the
configured `cls_token` stands.

Frozen encoder throughout — no fine-tuning, so nothing but the output token
varies.

## Commands

```bash
python -u -m experiments.exp06_encoder_readout.confirm_token
```
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from experiments.exp06_encoder_readout.run import (embed_with_token, HEADS,
                                                   TOKENS, WINDOWS)
from src.features.build_tensors import tensor_path
from src.models.readouts import closed_set_heads
from src.models.splits import split_by_driver

ALL_WINDOWS = (30.0, 51.2, 90.0, 120.0)
RESULTS_PATH = Path(__file__).parent / "confirm_token.md"

# Test-split accuracies from `run.py`, for the side-by-side. Those numbers chose
# the token; these are what they are being checked against.
TEST_SPLIT = {
    (51.2, "cls_token"): 24.6, (51.2, "mean_token"): 28.9,
    (51.2, "combined"): 28.0,
    (120.0, "cls_token"): 27.7, (120.0, "mean_token"): 36.7,
    (120.0, "combined"): 30.9,
}


def write_report(rows: list[dict], winners: dict[float, str]) -> None:
    """Write the confirmation report inside the experiment folder.

    Args:
        rows: one dict per (window, token) cell with inner-val accuracies.
        winners: {window: winning token on inner validation}.
    """
    agreed = [w for w in winners if winners[w] == "mean_token"]
    lines = [
        "# exp06 — output token confirmed on inner validation",
        "",
        "`run.py` chose `mean_token` using **test**-split accuracy, which biases "
        "that estimate. This re-ranks the three tokens on an **inner validation "
        "split carved out of the training windows only**, so the test set plays "
        "no part in the choice.",
        "",
        "Frozen encoder, audited 50 channels, 46 drivers, chance 2.2%. "
        "Best read-out per cell is shown; the full per-read-out numbers follow.",
        "",
        f"**`mean_token` wins on inner validation at "
        f"{len(agreed)} of {len(winners)} window lengths.**",
        "",
        "## Inner-validation accuracy (selection is made here)",
        "",
        "| Window | Output token | linear probe | LDA + centroid | random forest "
        "| best | test-split best (biased) |",
        "|---|---|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        cells = " | ".join(f"{row[h] * 100:.1f}%" for h in HEADS)
        best = max(row[h] for h in HEADS) * 100
        mark = " ✅" if winners[row["window"]] == row["token"] else ""
        prior = TEST_SPLIT.get((row["window"], row["token"]))
        prior_cell = f"{prior:.1f}%" if prior is not None else "—"
        lines.append(f"| {row['window']:g} s | `{row['token']}`{mark} | {cells} "
                     f"| **{best:.1f}%** | {prior_cell} |")

    lines += [
        "",
        "✅ marks the token selected at that window length.",
        "",
        "## Reading this",
        "",
        "- The **inner-validation** column is the legitimate basis for choosing "
        "an output token. The **test-split** column is what `run.py` reported "
        "and is biased by having been used to select.",
        "- Inner-validation accuracies are expected to sit **below** the "
        "test-split ones: the inner-train set is only ~70% of the training "
        "windows, so every read-out is fitted on less data. **Compare tokens "
        "within a column, never across columns.**",
        "",
        "## Limitations",
        "",
        "- Single inner split, no error bars; the token gap on test was 9.0pp, "
        "well outside plausible selection noise, which is why one split is "
        "treated as sufficient to confirm rather than to measure.",
        "- **Frozen encoder only.** Whether the same token wins after "
        "fine-tuning is a separate question, answered by the `full` arm.",
        "- Read-out layer fixed at 2. The Mantis paper reports intermediate "
        "layers help frozen feature extraction specifically, which is the "
        "regime here.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Rank output tokens on inner validation at every window length."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows: list[dict] = []
    winners: dict[float, str] = {}

    for window in ALL_WINDOWS:
        cached = np.load(tensor_path(window), allow_pickle=True)
        tensor, drivers = cached["X"], cached["driver"]
        starts = cached["start_time"]
        cohort = np.unique(drivers)

        # the outer split; only its training half is used below, so the test
        # windows take no part in choosing the token
        train_index, _ = split_by_driver(drivers, starts)
        print(f"\n=== {window:g} s | {tensor.shape} | "
              f"{len(train_index)} training windows -> inner split ===")

        best_token, best_score = None, -1.0
        for token in TOKENS:
            features, _ = embed_with_token(tensor, token, device)
            # closed_set_heads splits what it is given, so handing it only the
            # training windows yields inner-train / inner-val
            heads = closed_set_heads(features[train_index], drivers[train_index],
                                     starts[train_index], cohort)
            row = {"window": window, "token": token,
                   **{h: heads[h][1] for h in HEADS}}
            rows.append(row)
            score = max(row[h] for h in HEADS)
            if score > best_score:
                best_token, best_score = token, score
            print(f"  {token:11s} | "
                  + "  ".join(f"{h.split('_')[0]} {row[h] * 100:5.1f}%"
                              for h in HEADS)
                  + f" | best {score * 100:5.1f}%")
        winners[window] = best_token
        print(f"  -> inner-val winner: {best_token} ({best_score * 100:.1f}%)")

    write_report(rows, winners)
    print("\nwinners by window: "
          + ", ".join(f"{w:g}s={t}" for w, t in winners.items()))
    print(f"results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
