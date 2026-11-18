"""Which read-out block for the frozen encoder? All six, on inner validation.

## Why this exists

Round 1 compared block index 2 (the Mantis paper's recommendation, the output
after block 3 of 6) against the final block only, and kept index 2. The frozen
grid (`exp06/rescore_frozen.md`) then reported every block on the **test**
split, and closed-set accuracy fell with depth at every window: the first block
was best (e.g. 44.9% against 39.6% for index 2 at 90 s, 46-way). Choosing a
block from that table would be selecting on test. This runs the same comparison
on inner validation, where a choice is allowed.

## Pre-registered decision rule — fixed before any result

- **Metric:** 46-way closed-set top-1, LDA + centroid, inner validation (the
  training windows split again 70 / 5 / 25 per driver; the test windows are
  never read). This is the metric exp06 chose the token on.
- **Rule:** the frozen arm switches from index 2 to another block only if that
  block beats index 2 by **at least 2pp** (Round 1's margin) at **3 or more of
  the 4 windows**. Otherwise index 2 stays.
- **Open set** (inner driver AUROC, five partitions) is reported alongside and
  does not decide: on the test grid it had no consistent pattern across blocks.
- **Scope:** the frozen arm only. Fine-tuning reads out at the same block it
  trains through, so a block change there is a new fine-tuning run, decided
  separately.

## Configuration

| | |
|---|---|
| encoder | frozen Mantis-8M, `mean_token` |
| blocks | index 0–4 and final (all six) |
| windows | 30 / 51.2 / 90 / 120 s, `np.interp` |
| closed set | 46-way inner validation, and 36-way inner validation on each of the five exp07 partitions |
| open set | inner driver AUROC, exp07's pre-registered scoring, five partitions |
| embeddings | read from `src/features/build_embeddings.py`; nothing is embedded here |

## Commands

```bash
python -u -m experiments.exp08_layer_resampling.layer_profile --window 30 --window 51.2
python -u -m experiments.exp08_layer_resampling.layer_profile --window 90 --window 120
python -u -m experiments.exp08_layer_resampling.layer_profile --summarise
```
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from experiments.exp08_layer_resampling.round1 import score
from src.config import MANTIS_LAYER
from src.features.build_embeddings import (embedding_path, layer_name,
                                           PROFILE_TOKEN)
from src.models.open_set import N_PARTITIONS, N_UNKNOWN, SEED
from src.models.readouts import closed_set_heads, HEADS
from src.models.splits import (known_train_index, known_unknown_partitions,
                               split_by_driver)

WINDOWS = (30.0, 51.2, 90.0, 120.0)
BLOCKS = (0, 1, 2, 3, 4, -1)
MARGIN_PP = 2.0
WINDOWS_NEEDED = 3
CELL_DIR = Path(__file__).parent / "layer_profile_cells"
RESULTS_PATH = Path(__file__).parent / "layer_profile.md"


def closed46_inner(features: np.ndarray, drivers: np.ndarray,
                   starts: np.ndarray) -> dict:
    """46-way closed set on inner validation: all drivers, training windows only.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        starts: window start time per window.

    Returns:
        Top-1 per read-out.
    """
    train_local, _ = split_by_driver(drivers, starts)
    heads = closed_set_heads(features[train_local], drivers[train_local],
                             starts[train_local], np.unique(drivers))
    return {h: heads[h][1] for h in HEADS}


def run_cell(window: float, block: int) -> dict:
    """Score one (window, block) on inner validation.

    Args:
        window: window length in seconds.
        block: read-out block index, -1 for final.

    Returns:
        {"closed46": {...}, "partitions": [...]}.
    """
    saved = np.load(embedding_path(PROFILE_TOKEN, window, block),
                    allow_pickle=False)
    features, drivers, starts = saved["E"], saved["driver"], saved["start_time"]
    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=N_PARTITIONS, seed=SEED)
    rows = []
    for index, (known, unknown) in enumerate(partitions, start=1):
        known_train = known_train_index(drivers, starts, known)
        rows.append({"partition": index,
                     **score(features, drivers, starts, known, unknown,
                             known_train)})
    return {"closed46": closed46_inner(features, drivers, starts),
            "partitions": rows}


def run_windows(windows: list[float]) -> None:
    """Score every block at each given window, caching one file per cell.

    Args:
        windows: window lengths to run.
    """
    CELL_DIR.mkdir(exist_ok=True)
    for window in windows:
        for block in BLOCKS:
            path = CELL_DIR / f"{window:g}s_block{block}.json"
            if path.exists():
                continue
            clock = time.perf_counter()
            cell = run_cell(window, block)
            path.write_text(json.dumps(cell, indent=2))
            auroc = np.mean([r["driver_auroc"] for r in cell["partitions"]])
            print(f"{window:>5g}s {layer_name(block):<22} | inner 46-way LDA "
                  f"{cell['closed46']['lda_centroid'] * 100:5.1f}% | inner "
                  f"driver AUROC {auroc:.3f} | "
                  f"{(time.perf_counter() - clock) / 60:.1f} min", flush=True)


def summarise() -> None:
    """Apply the pre-registered rule and write the report."""
    cells = {}
    for window in WINDOWS:
        for block in BLOCKS:
            path = CELL_DIR / f"{window:g}s_block{block}.json"
            if path.exists():
                cells[(window, block)] = json.loads(path.read_text())

    lines = [
        "# exp08 — read-out block profile, frozen encoder, inner validation",
        "",
        f"Frozen Mantis-8M, `{PROFILE_TOKEN}`, every block. **Inner validation** "
        "only: the training windows split again 70 / 5 / 25 per driver; no test "
        "window is read. Mantis numbers its blocks from 0.",
        "",
        "**Pre-registered rule:** switch from index 2 only if another block beats "
        f"it by ≥ {MARGIN_PP:g}pp in 46-way inner LDA at ≥ {WINDOWS_NEEDED} of 4 "
        "windows. Open set is reported and does not decide.",
        "",
        "## 46-way closed set, LDA + centroid (decides)",
        "",
        "| Block | " + " | ".join(f"{w:g} s" for w in WINDOWS) + " |",
        "|---|" + "--:|" * len(WINDOWS),
    ]
    for block in BLOCKS:
        texts = [f"{cells[(w, block)]['closed46']['lda_centroid'] * 100:.1f}%"
                 if (w, block) in cells else "—" for w in WINDOWS]
        lines.append(f"| {layer_name(block)} | " + " | ".join(texts) + " |")

    lines += [
        "",
        "## Open set, inner driver AUROC, mean ± sd over 5 partitions "
        "(reported only)",
        "",
        "| Block | " + " | ".join(f"{w:g} s" for w in WINDOWS) + " |",
        "|---|" + "--:|" * len(WINDOWS),
    ]
    for block in BLOCKS:
        texts = []
        for w in WINDOWS:
            if (w, block) not in cells:
                texts.append("—")
                continue
            values = [r["driver_auroc"] for r in cells[(w, block)]["partitions"]]
            texts.append(f"{np.mean(values):.3f} ± {np.std(values):.3f}")
        lines.append(f"| {layer_name(block)} | " + " | ".join(texts) + " |")

    lines += ["", "## Decision", ""]
    complete = all((w, b) in cells for w in WINDOWS for b in BLOCKS)
    if not complete:
        lines.append("Not all cells have run; no decision yet.")
    else:
        verdicts = []
        for block in BLOCKS:
            if block == MANTIS_LAYER:
                continue
            wins = [w for w in WINDOWS
                    if (cells[(w, block)]["closed46"]["lda_centroid"]
                        - cells[(w, MANTIS_LAYER)]["closed46"]["lda_centroid"])
                    * 100 >= MARGIN_PP]
            verdicts.append((block, wins))
            lines.append(f"- {layer_name(block)}: beats index 2 by ≥ "
                         f"{MARGIN_PP:g}pp at {len(wins)} of 4 windows"
                         + (f" ({', '.join(f'{w:g} s' for w in wins)})"
                            if wins else ""))
        qualifying = [b for b, wins in verdicts if len(wins) >= WINDOWS_NEEDED]
        if not qualifying:
            lines += ["", "**The rule is not met: index 2 stays for the frozen "
                      "arm.**"]
        else:
            best = max(qualifying, key=lambda b: np.mean(
                [cells[(w, b)]["closed46"]["lda_centroid"] for w in WINDOWS]))
            lines += ["", f"**The rule is met: the frozen arm moves to "
                      f"{layer_name(best)}**, the qualifying block with the "
                      "highest mean across windows."]

    lines += [
        "",
        "## Limitations",
        "",
        "- Inner validation draws on the same 46 drives as test; its windows "
        "are correlated with the outer training windows.",
        "- Frozen arm only; a block change for the fine-tuned arm needs its own "
        "fine-tuning runs.",
        "- `mean_token` only.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print(f"report -> {RESULTS_PATH}")


def main() -> None:
    """Run windows, or summarise."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, action="append")
    parser.add_argument("--summarise", action="store_true")
    arguments = parser.parse_args()
    if arguments.summarise:
        summarise()
    elif arguments.window:
        run_windows(arguments.window)
    else:
        parser.error("give --window or --summarise")


if __name__ == "__main__":
    main()
