"""The frozen grid: every window x output token x read-out layer, closed and open set.

## Why this exists

The frozen encoder's three axes — window length, output token, read-out layer —
were each settled on inner validation in a different experiment (exp06
`confirm_token.md`, exp08 `round1.md`), and the open-set results for most
combinations were measured with the scoring exp07 later showed to be the
bottleneck. This script puts all 24 combinations in one table, with the two
numbers that matter, under one protocol.

It reports; it chooses nothing. The choices stand where they were made on inner
validation: `mean_token` (exp06), read-out index 2 (exp08 Round 1).

## What is measured

| | |
|---|---|
| encoder | frozen Mantis-8M |
| read-out layer | index 2 (after block 3 of 6, the project's) and final (after block 6) |
| tokens | `cls_token`, `mean_token`, `combined` |
| windows | 30 / 51.2 / 90 / 120 s, `np.interp` |
| closed set, main table | **46-way**, all drivers enrolled, LDA + centroid |
| open set, main table | driver AUROC, exp07's pre-registered scoring, five 36/10 partitions |
| detail tables | 36-way probe / LDA / forest and window AUROC on the same partitions |
| layer profile | all 6 blocks, `mean_token`, at 30 s (the headline's window) and 90 / 120 s (the frozen encoder's preferred) |

Frozen embeddings do not depend on the partition. They are read from the
committed artefact (`src/features/build_embeddings.py`, checked by
`QC/verify_embeddings.py`); this script embeds nothing itself. The frozen
encoder and LDA are deterministic, so the 46-way number has no error bar.

## Commands

```bash
python -u -m experiments.exp06_encoder_readout.rescore_frozen   # CPU only
```
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from src.config import MANTIS_LAYER
from src.features.build_embeddings import (embedding_path, layer_name, LAYERS,
                                           PROFILE_LAYERS, PROFILE_TOKEN,
                                           PROFILE_WINDOWS)
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, PRE_REGISTERED,
                                 score_config, SEED)
from src.models.readouts import closed_set_heads
from src.models.splits import known_unknown_partitions

WINDOWS = (30.0, 51.2, 90.0, 120.0)
TOKENS = ("cls_token", "mean_token", "combined")
HEADLINE_TOKEN = "mean_token"
HEADS = ("linear_probe", "lda_centroid", "random_forest")
CELLS_PATH = Path(__file__).parent / "rescore_frozen_cells.json"
RESULTS_PATH = Path(__file__).parent / "rescore_frozen.md"


def cell_key(token: str, window: float, layer: int) -> str:
    """Cache key for one cell.

    Args:
        token: output token.
        window: window length in seconds.
        layer: read-out block index.

    Returns:
        e.g. 'mean_token|30|2'.
    """
    return f"{token}|{window:g}|{layer}"


def load_cells() -> dict:
    """Load cached cells, upgrading the earlier layer-less format.

    The first run cached `token|window` keys holding a list of partition rows,
    all at the project's read-out layer. They are re-keyed with that layer so
    their open-set results are reused rather than recomputed.

    Returns:
        key -> {"partitions": [...], optionally "closed46": {...}}.
    """
    if not CELLS_PATH.exists():
        return {}
    cached = json.loads(CELLS_PATH.read_text())
    cells = {}
    for key, value in cached.items():
        if isinstance(value, list):
            token, window = key.split("|")
            cells[cell_key(token, float(window), MANTIS_LAYER)] = {
                "partitions": value}
        else:
            cells[key] = value
    return cells


def load_frozen(token: str, window: float, layer: int) -> dict:
    """Read one cell's frozen embeddings from the artefact.

    Args:
        token: output token.
        window: window length in seconds.
        layer: read-out block index.

    Returns:
        Dict with E, driver, start_time.
    """
    saved = np.load(embedding_path(token, window, layer), allow_pickle=False)
    return {key: saved[key] for key in ("E", "driver", "start_time")}


def score_partitions(data: dict) -> list[dict]:
    """36-way closed set and open set on each of the five partitions.

    Args:
        data: E, driver, start_time.

    Returns:
        One row per partition.
    """
    drivers, starts = data["driver"], data["start_time"]
    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=N_PARTITIONS, seed=SEED)
    rows = []
    for index, (known, unknown) in enumerate(partitions, start=1):
        heads = closed_set_heads(data["E"], drivers, starts, known)
        window_auroc, driver_auroc = score_config(
            {**data, "known": known, "unknown": unknown}, PRE_REGISTERED)
        rows.append({"partition": index,
                     "features": int(data["E"].shape[1]),
                     **{h: heads[h][1] for h in HEADS},
                     "window_auroc": window_auroc,
                     "driver_auroc": driver_auroc})
    return rows


def score_closed46(data: dict) -> dict:
    """Closed set with all 46 drivers enrolled.

    Args:
        data: E, driver, start_time.

    Returns:
        Top-1 accuracy per read-out.
    """
    cohort = np.unique(data["driver"])
    heads = closed_set_heads(data["E"], data["driver"], data["start_time"],
                             cohort)
    return {h: heads[h][1] for h in HEADS}


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


def ordered_keys(cells: dict) -> list[tuple[int, float, str]]:
    """Every (layer, window, token) present, in table order.

    Args:
        cells: cached cells.

    Returns:
        (layer, window, token) tuples.
    """
    return [(layer, window, token) for layer in LAYERS for window in WINDOWS
            for token in TOKENS if cell_key(token, window, layer) in cells]


def write_report(cells: dict) -> None:
    """Write the grid report: one simple table, then the detail.

    Args:
        cells: key -> {"partitions": [...], "closed46": {...}}.
    """
    lines = [
        "# The frozen grid — window × token × read-out layer",
        "",
        "Frozen Mantis-8M, `np.interp`, every number on the **test** split. "
        "This table **reports**; it chooses nothing. The choices were made on "
        "inner validation: `mean_token` (exp06 `confirm_token.md`) and read-out "
        "index 2 (exp08 `round1.md`).",
        "",
        "Mantis numbers its 6 transformer blocks from 0: **index 2** is the "
        "output after block 3, **final** after block 6.",
        "",
        "## Main table",
        "",
        "- **Closed set:** 46-way, all drivers enrolled, LDA + centroid. Chance "
        "2.2%. Deterministic, so no error bar.",
        "- **Open set:** driver AUROC, 36 enrolled / 10 strangers, mean ± sd "
        "over five partitions. Chance 0.500.",
        "",
        "| Layer | Window | Token | Closed set, 46-way | Open set, driver AUROC |",
        "|---|--:|---|--:|--:|",
    ]
    for layer, window, token in ordered_keys(cells):
        cell = cells[cell_key(token, window, layer)]
        closed = cell.get("closed46")
        closed_text = (f"{closed['lda_centroid'] * 100:.1f}%"
                       if closed else "—")
        rows = cell["partitions"]
        lines.append(
            f"| {layer_name(layer)} | {window:g} s | `{token}` | {closed_text} | "
            f"{mean_sd([r['driver_auroc'] for r in rows], False)} |")

    profile_layers = sorted(PROFILE_LAYERS + (MANTIS_LAYER,)) + [-1]
    lines += [
        "",
        f"## Layer profile — `{PROFILE_TOKEN}`, every block",
        "",
        "Where in the network driver information sits. 30 s is the headline's "
        "window; 90 s and 120 s are where the frozen encoder does best. Each "
        "cell: 46-way closed set / open-set driver AUROC.",
        "",
        "| Layer | " + " | ".join(f"{w:g} s" for w in PROFILE_WINDOWS) + " |",
        "|---|" + "--:|" * len(PROFILE_WINDOWS),
    ]
    for layer in profile_layers:
        texts = []
        for window in PROFILE_WINDOWS:
            cell = cells.get(cell_key(PROFILE_TOKEN, window, layer))
            if not cell or "closed46" not in cell:
                texts.append("pending")
                continue
            auroc = np.mean([r["driver_auroc"] for r in cell["partitions"]])
            texts.append(f"{cell['closed46']['lda_centroid'] * 100:.1f}% / "
                         f"{auroc:.3f}")
        lines.append(f"| {layer_name(layer)} | " + " | ".join(texts) + " |")

    lines += [
        "",
        "## Detail — 36-way closed set and window AUROC, same partitions",
        "",
        "| Layer | Window | Token | Features | probe | LDA | forest | "
        "window AUROC | driver AUROC |",
        "|---|--:|---|--:|--:|--:|--:|--:|--:|",
    ]
    for layer, window, token in ordered_keys(cells):
        rows = cells[cell_key(token, window, layer)]["partitions"]
        lines.append(
            f"| {layer_name(layer)} | {window:g} s | `{token}` | "
            f"{rows[0]['features']:,} | "
            + " | ".join(mean_sd([r[h] for r in rows], True) for h in HEADS)
            + f" | {mean_sd([r['window_auroc'] for r in rows], False)}"
            + f" | {mean_sd([r['driver_auroc'] for r in rows], False)} |")

    lines += [
        "",
        "## Detail — 46-way closed set, all three read-outs",
        "",
        "| Layer | Window | Token | probe | LDA | forest |",
        "|---|--:|---|--:|--:|--:|",
    ]
    for layer, window, token in ordered_keys(cells):
        closed = cells[cell_key(token, window, layer)].get("closed46")
        if closed:
            lines.append(
                f"| {layer_name(layer)} | {window:g} s | `{token}` | "
                + " | ".join(f"{closed[h] * 100:.1f}%" for h in HEADS) + " |")

    lines += [
        "",
        "## Limitations",
        "",
        "- Test-split numbers, reported, not used for selection.",
        "- Driver AUROC rests on 46 drivers per partition; one partition varies "
        "by about ±0.09, so differences under ~0.05 are not meaningful.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def all_cells() -> list[tuple[int, float, str]]:
    """Every (layer, window, token) to score: the grid, then the layer profile.

    Returns:
        (layer, window, token) tuples.
    """
    grid = [(layer, window, token) for layer in LAYERS for window in WINDOWS
            for token in TOKENS]
    profile = [(layer, window, PROFILE_TOKEN) for window in PROFILE_WINDOWS
               for layer in PROFILE_LAYERS]
    return grid + profile


def main() -> None:
    """Score every cell not yet cached, then write the report."""
    cells = load_cells()
    for layer, window, token in all_cells():
        key = cell_key(token, window, layer)
        cell = cells.get(key, {})
        if "partitions" in cell and "closed46" in cell:
            continue
        clock = time.perf_counter()
        data = load_frozen(token, window, layer)
        if "partitions" not in cell:
            cell["partitions"] = score_partitions(data)
        if "closed46" not in cell:
            cell["closed46"] = score_closed46(data)
        cells[key] = cell
        CELLS_PATH.write_text(json.dumps(cells, indent=2))
        print(f"L{layer:<3} {window:>5g}s {token:<11} | 46-way LDA "
              f"{cell['closed46']['lda_centroid'] * 100:5.1f}% | driver "
              f"AUROC {np.mean([r['driver_auroc'] for r in cell['partitions']]):.3f}"
              f" | {(time.perf_counter() - clock) / 60:.1f} min",
              flush=True)
        write_report(cells)
    write_report(cells)
    print(f"report -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
