"""Expanded open-set sweep, selected on inner validation.

## Why this exists

The Phase C preview found that open-set rejection is not capped at ~0.51: the
limit was the *space* distances were computed in, not the scoring rule.
Prototype rules — the ones exp04 already used — reached driver AUROC 0.714 once
the embedding was L2-normalised and reduced to 25 PCA components.

That preview has two faults this script fixes.

**1. It scored on test windows.** Choosing a configuration there and then
reporting Phase B's test number would repeat the `cls_token` error for a third
time. Everything here is fitted on inner-train and scored on **inner
validation**, so Phase B's test split stays untouched and the configuration
chosen here can be reported honestly.

**2. The winner sat at the edge of the grid.** PCA 25 was the *smallest* value
tried, so the optimum was never bracketed — it may be 10 or 15. The grid now
extends down to 5.

## The four knobs, and what each assumes

| Step | Levels | What varying it tests |
|---|---|---|
| **2. projection** | PCA 5 … 100, plus **LDA** | how many dimensions distances should live in. LDA is supervised — it seeks directions separating the 36 *known* drivers, which may help, or may fold unknowns into known territory and hurt. Both outcomes are informative |
| **3. transform** | raw, l2norm, whiten, and both orders of the two | whether distance should use direction only (`l2norm` discards magnitude, which swings with traffic and grade) or equalised variance (`whiten`) |
| **4. prototype** | mean, median, k-means 2, k-means 3 | whether a driver is one blob. If a driver's 30 s windows split into modes — city crawl, highway cruise — a single mean sits between them, in a region the driver never occupies |
| **5. rule** | 13, across six families | the scoring formula itself |

Step 4 matters for the reason the preview's result was *half* predicted: the
prototype rules won, so centroids were not the problem — but whether **one**
centroid per driver is enough was never tested.

## Reading the output

The best cell of a large grid is optimistically biased, so the report ranks by a
**region** rather than a single cell: each projection and transform is also
summarised by its median across rules, which is far more stable than its
maximum. A setting that is good everywhere is more trustworthy than one cell
that spikes.

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_c_sweep
```
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
from sklearn.preprocessing import StandardScaler

from src.config import DATA_INTERIM
from src.models.finetune import OUTPUT_TOKEN
from src.models.open_set import (auroc_pair, inner_indices, N_PARTITIONS,
                                 N_UNKNOWN, OTHER_RULES, other_scores,
                                 project, PROJECTIONS, PROTOTYPE_RULES,
                                 prototype_scores, PROTOTYPES, SEED,
                                 transform_rows, TRANSFORMS)
from src.models.splits import known_unknown_partitions
from src.models.splits import known_unknown_partitions

RESULTS_PATH = Path(__file__).parent / "phase_c_sweep.md"


def write_report(cells: dict) -> None:
    """Write the sweep report inside the experiment folder.

    Args:
        cells: {(projection, transform, prototype, rule): (window, driver)}.
    """
    best = max(cells, key=lambda k: cells[k][1])
    by_projection = {p: [v[1] for k, v in cells.items() if k[0] == p]
                     for p in PROJECTIONS}
    by_transform = {t: [v[1] for k, v in cells.items() if k[1] == t]
                    for t in TRANSFORMS}
    by_prototype = {p: [v[1] for k, v in cells.items() if k[2] == p]
                    for p in PROTOTYPES}
    by_rule = {r: [v[1] for k, v in cells.items() if k[3] == r]
               for r in PROTOTYPE_RULES + OTHER_RULES}

    lines = [
        "# exp07 Phase C — expanded open-set sweep, selected on inner validation",
        "",
        f"`full` + `{OUTPUT_TOKEN}`, 30 s windows, one partition. Every model "
        "is fitted on **inner-train** and scored on **inner validation**; the "
        "test period is excluded for known *and* unknown drivers, so nothing "
        "chosen here can bias Phase B's test numbers.",
        "",
        "AUROC, **0.500 is chance**. exp04's best driver-level was **0.566**.",
        "",
        f"**Best cell: `{best[3]}` · {best[0]} · {best[1]} · {best[2]} "
        f"prototypes — driver AUROC {cells[best][1]:.3f}** "
        f"(window {cells[best][0]:.3f}).",
        "",
        "A maximum over "
        f"{len(cells):,} cells is optimistically biased, so the marginals "
        "below matter more than the single winner: **median** across all cells "
        "containing a level is a far more stable signal than its maximum.",
        "",
        "## Which projection (step 2)",
        "",
        "| Projection | median driver AUROC | best |",
        "|---|--:|--:|",
    ]
    for name in PROJECTIONS:
        values = by_projection[name]
        lines.append(f"| `{name}` | {np.median(values):.3f} | "
                     f"{max(values):.3f} |")

    for title, table, keys in [
            ("Which transform (step 3)", by_transform, TRANSFORMS),
            ("Which prototype (step 4)", by_prototype, PROTOTYPES),
            ("Which rule (step 5)", by_rule, PROTOTYPE_RULES + OTHER_RULES)]:
        lines += ["", f"## {title}", "",
                  "| Level | median driver AUROC | best |", "|---|--:|--:|"]
        for name in keys:
            values = table[name]
            if values:
                lines.append(f"| `{name}` | {np.median(values):.3f} | "
                             f"{max(values):.3f} |")

    top = sorted(cells, key=lambda k: -cells[k][1])[:15]
    lines += ["", "## Top 15 cells", "",
              "| Rule | Projection | Transform | Prototype | window | driver |",
              "|---|---|---|---|--:|--:|"]
    for key in top:
        window, driver = cells[key]
        lines.append(f"| `{key[3]}` | {key[0]} | {key[1]} | {key[2]} | "
                     f"{window:.3f} | **{driver:.3f}** |")

    lines += [
        "",
        "## Limitations",
        "",
        "- **One partition.** Marginals are averaged over many cells, which "
        "stabilises them, but the partition itself is a single draw.",
        "- The chosen configuration must be **re-stated on Phase B's five test "
        "partitions** before it counts as a result.",
        "- `ocsvm`, `lof` and `gmm` hyperparameters are left at defaults.",
        "- One drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Run the expanded sweep on inner validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, default=30.0)
    arguments = parser.parse_args()
    warnings.filterwarnings("ignore")

    path = DATA_INTERIM / f"embeddings_full_{OUTPUT_TOKEN}_{arguments.window:g}s.npz"
    cached = np.load(path, allow_pickle=True)
    features, drivers = cached["E"], cached["driver"]
    starts = cached["start_time"]
    known, unknown = known_unknown_partitions(
        drivers, n_unknown=N_UNKNOWN, n_partitions=N_PARTITIONS, seed=SEED)[0]

    train_index, val_index, unknown_index = inner_indices(drivers, starts,
                                                          known, unknown)
    print(f"{path.name} | {features.shape}")
    print(f"inner-train {len(train_index):,} | inner-val {len(val_index):,} "
          f"| unknown inner-val {len(unknown_index):,}")

    scaler = StandardScaler().fit(features[train_index])
    scaled = scaler.transform(features)
    train_drivers = drivers[train_index]
    cells: dict[tuple, tuple[float, float]] = {}

    for projection in PROJECTIONS:
        p_train, p_all = project(scaled[train_index], scaled, train_drivers,
                                 projection)
        for transform in TRANSFORMS:
            t_train, t_all = transform_rows(p_train, p_all, transform)
            known_q, unknown_q = t_all[val_index], t_all[unknown_index]

            scores = other_scores(t_train, train_drivers, known_q)
            scores_u = other_scores(t_train, train_drivers, unknown_q)
            for rule in OTHER_RULES:
                cells[(projection, transform, "—", rule)] = auroc_pair(
                    scores[rule], scores_u[rule], drivers[val_index],
                    drivers[unknown_index])

            for prototype in PROTOTYPES:
                pk = prototype_scores(t_train, train_drivers, known_q,
                                      prototype)
                pu = prototype_scores(t_train, train_drivers, unknown_q,
                                      prototype)
                for rule in PROTOTYPE_RULES:
                    cells[(projection, transform, prototype, rule)] = (
                        auroc_pair(pk[rule], pu[rule], drivers[val_index],
                                   drivers[unknown_index]))

        best = max((k for k in cells if k[0] == projection),
                   key=lambda k: cells[k][1])
        print(f"  {projection:7s} | best {cells[best][1]:.3f} "
              f"({best[3]}, {best[1]}, {best[2]})")

    write_report(cells)
    best = max(cells, key=lambda k: cells[k][1])
    print(f"\n{len(cells):,} cells")
    print(f"best: {best[3]} | {best[0]} | {best[1]} | {best[2]} | "
          f"driver AUROC {cells[best][1]:.3f}")
    print(f"results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
