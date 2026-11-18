"""Merge Round 1's cells into one report and apply the pre-committed rule.

Reads `cells/*.json` written by `round1.py` and writes `round1.md`. Safe to run
while cells are still in progress: it reports whatever has finished.

Run:
    python -m experiments.exp08_layer_resampling.summarise
"""
from __future__ import annotations

import json
from pathlib import Path

HEADS = ("linear_probe", "lda_centroid", "random_forest")
CELLS = ("layer2_interp", "layer2_binavg", "final_interp", "final_binavg")
INCUMBENT = "layer2_interp"
MARGIN_PP = 2.0
CELL_DIR = Path(__file__).parent / "cells"
RESULTS_PATH = Path(__file__).parent / "round1.md"


def best_head(scores: dict) -> float:
    """Best closed-set accuracy across the three read-outs.

    Args:
        scores: one arm's score dict from a cell row.

    Returns:
        The highest top-1 accuracy, as a fraction.
    """
    return max(scores[h] for h in HEADS)


def main() -> None:
    """Write the merged Round 1 report."""
    cells = {name: json.loads((CELL_DIR / f"{name}.json").read_text())
             for name in CELLS if (CELL_DIR / f"{name}.json").exists()}
    lines = [
        "# exp08 Round 1 — read-out layer x resampling, inner validation",
        "",
        "`mean_token`, 60 epochs, one 36-known/10-unknown partition (seed 42). "
        "Encoders are fitted on **inner-train**; every number is **inner "
        "validation**, so nothing here touches the test split. Closed set is "
        "36-way (chance 2.8%), best of probe / LDA / forest. Open set is "
        "exp07's pre-registered scoring (LDA, `l2norm_whiten`, `mean`, "
        "`cosine`), driver-level AUROC.",
        "",
        f"**{len(cells)} of {len(CELLS)} cells finished.**",
        "",
    ]
    for arm in ("full", "frozen"):
        for metric, label in (("closed", "closed-set top-1"),
                              ("driver_auroc", "open-set driver AUROC")):
            lines += [f"## `{arm}` — {label}", "",
                      "| Cell | 30 s | 51.2 s | 90 s | 120 s | best |",
                      "|---|--:|--:|--:|--:|--:|"]
            for name, cell in cells.items():
                values = [best_head(row[arm]) * 100 if metric == "closed"
                          else row[arm][metric] for row in cell["rows"]]
                fmt = "{:.1f}%" if metric == "closed" else "{:.3f}"
                padded = [fmt.format(v) for v in values] + ["…"] * (4 - len(values))
                lines.append(f"| `{name}` | " + " | ".join(padded)
                             + f" | **{fmt.format(max(values))}** |")
            lines.append("")

    lines += ["## Decision", ""]
    finished = {n: c for n, c in cells.items() if len(c["rows"]) == 4}
    if INCUMBENT in finished and len(finished) == len(CELLS):
        best = {n: max(best_head(r["full"]) for r in c["rows"]) * 100
                for n, c in finished.items()}
        winner = max(best, key=best.get)
        gap = best[winner] - best[INCUMBENT]
        if winner != INCUMBENT and gap > MARGIN_PP:
            lines.append(
                f"`{winner}` beats the incumbent `{INCUMBENT}` by **{gap:.1f}pp** "
                f"({best[winner]:.1f}% vs {best[INCUMBENT]:.1f}%), more than the "
                f"pre-committed {MARGIN_PP:g}pp margin. **The configuration "
                "changes; exp07's test runs must be repeated at the new one.**")
        else:
            lines.append(
                f"No challenger beats the incumbent `{INCUMBENT}` "
                f"({best[INCUMBENT]:.1f}%) by more than the pre-committed "
                f"{MARGIN_PP:g}pp margin (best: `{winner}` at "
                f"{best[winner]:.1f}%). **The incumbent stands and exp07's test "
                "numbers are final.**")
    else:
        lines.append("Pending — not every cell has finished all four windows.")

    lines += [
        "",
        "## Limitations",
        "",
        "- One partition and one seed per cell; differences under ~2pp are "
        "within single-split noise, which is why the margin exists.",
        "- Inner-validation accuracies are fitted on ~70% of the training "
        "windows and are not comparable to test numbers.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
