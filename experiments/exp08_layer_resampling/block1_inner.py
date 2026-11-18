"""Should the fine-tuned arm read out after block 1? The inner-validation decision.

The frozen layer profile (`layer_profile.md`) moved the frozen arm to block 1
(index 0). The same question for the fine-tuned arm was run with Round 1's script
and protocol (`round1.py --layer 0`: inner validation, partition 1, all four
windows) and compared with Round 1's block-3 cell. This script reads those two
cells and applies the rule; it trains nothing.

## Pre-registered rule — fixed before the block-1 run

The fine-tuned arm moves to block 1 only if block 1 beats block 3 by at least
2pp (best of the three read-outs, 36-way inner validation) at 3 or more of the 4
windows. The same rule moved the frozen arm.

If it is met, `block1_test.py` reports block 1 on test. If not, block 3 stays and
`block1_test.py` is not run.

## Commands

```bash
python -u -m experiments.exp08_layer_resampling.round1 --layer 0 --resampling interp
python -u -m experiments.exp08_layer_resampling.block1_inner
```
"""
from __future__ import annotations

import json
from pathlib import Path

from src.models.readouts import HEADS

CELL_DIR = Path(__file__).parent / "cells"
RESULTS_PATH = Path(__file__).parent / "block1_inner.md"
WINDOWS = (30.0, 51.2, 90.0, 120.0)
MARGIN_PP = 2.0
WINDOWS_NEEDED = 3


def load_rows(cell: str) -> dict[float, dict]:
    """Rows of one Round 1 cell, keyed by window.

    Args:
        cell: cell name, e.g. 'layer0_interp'.

    Returns:
        window -> row with 'frozen' and 'full' scores.
    """
    rows = json.loads((CELL_DIR / f"{cell}.json").read_text())["rows"]
    return {row["window"]: row for row in rows}


def best(scores: dict) -> float:
    """Best closed-set top-1 across the three read-outs.

    Args:
        scores: one arm's scores for one window.

    Returns:
        The highest top-1.
    """
    return max(scores[h] for h in HEADS)


def main() -> None:
    """Compare block 1 against block 3 for both arms and apply the rule."""
    block1, block3 = load_rows("layer0_interp"), load_rows("layer2_interp")
    lines = [
        "# exp08 — fine-tuned read-out block: 1 vs 3, inner validation",
        "",
        "Round 1's protocol: inner validation (the training windows split again), "
        "one 36/10 partition, `mean_token`, `np.interp`, 60 epochs. Closed set is "
        "the best of probe / LDA / forest, 36-way; open set is inner driver AUROC "
        "under exp07's pre-registered scoring. No test window is read.",
        "",
        "**Rule, fixed before the block-1 run:** move the fine-tuned arm to block 1 "
        f"only if it beats block 3 by ≥ {MARGIN_PP:g}pp at ≥ {WINDOWS_NEEDED} of 4 "
        "windows.",
        "",
        "## Fine-tuned arm (decides)",
        "",
        "| Window | training windows | block 3 | block 1 | difference | "
        "driver AUROC, block 3 → block 1 |",
        "|--:|--:|--:|--:|--:|--:|",
    ]
    wins = []
    for window in WINDOWS:
        b3, b1 = block3[window], block1[window]
        diff = (best(b1["full"]) - best(b3["full"])) * 100
        if diff >= MARGIN_PP:
            wins.append(window)
        lines.append(
            f"| {window:g} s | {b1['n_fit']:,} | {best(b3['full']) * 100:.1f}% | "
            f"{best(b1['full']) * 100:.1f}% | {diff:+.1f}pp | "
            f"{b3['full']['driver_auroc']:.3f} → {b1['full']['driver_auroc']:.3f} |")

    lines += [
        "",
        "## Frozen versus fine-tuned at the same block and window",
        "",
        "What fine-tuning adds, read on the same split (closed set, best read-out):",
        "",
        "| Window | training windows | block 3: frozen → fine-tuned | "
        "block 1: frozen → fine-tuned |",
        "|--:|--:|--:|--:|",
    ]
    for window in WINDOWS:
        b3, b1 = block3[window], block1[window]
        lines.append(
            f"| {window:g} s | {b1['n_fit']:,} | "
            f"{best(b3['frozen']) * 100:.1f}% → {best(b3['full']) * 100:.1f}% "
            f"({(best(b3['full']) - best(b3['frozen'])) * 100:+.1f}pp) | "
            f"{best(b1['frozen']) * 100:.1f}% → {best(b1['full']) * 100:.1f}% "
            f"({(best(b1['full']) - best(b1['frozen'])) * 100:+.1f}pp) |")

    met = len(wins) >= WINDOWS_NEEDED
    lines += [
        "",
        "## Decision",
        "",
        f"Block 1 beats block 3 by ≥ {MARGIN_PP:g}pp at {len(wins)} of 4 windows"
        + (f" ({', '.join(f'{w:g} s' for w in wins)})" if wins else "") + ".",
        "",
        ("**The rule is met: the fine-tuned arm moves to block 1.**" if met else
         "**The rule is not met: the fine-tuned arm stays at block 3, 30 s.** "
         "`block1_test.py` was written in advance and is not run."),
        "",
        "Fine-tuning helps most where training windows are most plentiful (30 s at "
        "block 3) and can hurt where they are fewest (90–120 s), consistent with "
        "updating all parameters on too little data. Not tested further here.",
        "",
        "## Limitations",
        "",
        "- One partition, as in Round 1; one partition varies by roughly ±3pp "
        "closed set.",
        "- One seed.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print(f"block 1 wins at {len(wins)} of 4 windows -> "
          f"{'met' if met else 'not met'}; report -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
