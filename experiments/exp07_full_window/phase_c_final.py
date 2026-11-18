"""Phase C final — the pre-registered open-set configuration, on test.

## What was fixed in advance

`phase_c_sweep.py` searched 1,300 configurations on **inner validation** and the
choice below was fixed **before any test window was scored**, taken from the
per-knob medians rather than the single best cell, because the maximum of a
large grid is optimistically biased while a median over ~130 cells is not:

| Knob | Chosen | Median driver AUROC | Runner-up |
|---|---|--:|---|
| projection | **LDA** | 0.667 | pca100 0.574 |
| transform | **`l2norm_whiten`** | 0.561 | `whiten_l2norm` 0.539 |
| prototype | **`mean`** | 0.571 | median 0.564 |
| rule | **`cosine`** | 0.610 | `msp` 0.598 |

This script reports that one configuration on the five Phase B test partitions.
It is reported whatever it scores — that is the point of fixing it first.

## Context rows, reported alongside

- **exp04 default** (PCA 50, raw, `mean`): the configuration that produced the
  original "open-set is null" conclusion. Its presence makes the comparison
  internal rather than across papers.
- **best inner-val cell** (`cosine`, pca25, `l2norm_whiten`, `mean`): the
  grid maximum, carried over to show how much of it was selection bias.

## Why driver-level numbers need five partitions

Driver-level AUROC compares 36 known against 10 unknown — 46 points. Simulated
single-partition standard deviation is **0.08–0.10**, so one partition cannot
distinguish 0.56 from 0.75 in either direction. Averaging five roughly halves
it. Window-level uses ~585 known and ~149 unknown windows and is far steadier,
which is why both are reported and window-level is the one to trust for small
differences.

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_c_final
```
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np

from src.config import DATA_INTERIM
from src.models.finetune import OUTPUT_TOKEN
from src.models.open_set import (N_PARTITIONS, PRE_REGISTERED,
                                 PROTOTYPE_RULES, score_config)

WINDOW_SECONDS = 30.0
RESULTS_PATH = Path(__file__).parent / "phase_c_final.md"

CONFIGS = {
    "pre-registered": PRE_REGISTERED,
    "exp04 default": ("pca50", "raw", "mean", "mahalanobis"),
    "exp04 default, cosine": ("pca50", "raw", "mean", "cosine"),
    "best inner-val cell": ("pca25", "l2norm_whiten", "mean", "cosine"),
    "lda + raw + cosine": ("lda", "raw", "mean", "cosine"),
    "lda + l2norm + euclidean": ("lda", "l2norm", "mean", "euclidean"),
}
PROTOTYPE_RULES = ("euclidean", "cosine", "ratio", "mahalanobis")


def write_report(results: dict[str, list[tuple[float, float]]]) -> None:
    """Write the final open-set report.

    Args:
        results: {config name: per-partition (window, driver) AUROC}.
    """
    pre = results["pre-registered"]
    pre_driver = np.mean([v[1] for v in pre])
    lines = [
        "# exp07 Phase C final — open-set on test, pre-registered configuration",
        "",
        f"`full` + `{OUTPUT_TOKEN}`, {WINDOW_SECONDS:g} s windows, "
        f"{N_PARTITIONS} partitions of 36 known / 10 unknown drivers. "
        "Everything is fitted on known-train only; unknown drivers appear once, "
        "at scoring. **0.500 is chance.**",
        "",
        "The configuration on the first row was fixed from inner-validation "
        "**medians** before any test window was scored, and is reported "
        "whatever it achieved. Later rows are context, including the "
        "configuration whose test-split maximum was 0.806 on one partition.",
        "",
        "| Configuration | projection | transform | rule | window AUROC | "
        "driver AUROC |",
        "|---|---|---|---|--:|--:|",
    ]
    for name, values in results.items():
        window = [v[0] for v in values]
        driver = [v[1] for v in values]
        mark = "**" if name == "pre-registered" else ""
        config = CONFIGS[name]
        lines.append(
            f"| {mark}{name}{mark} | {config[0]} | {config[1]} | "
            f"`{config[3]}` | {np.mean(window):.3f} ± {np.std(window):.3f} | "
            f"{mark}{np.mean(driver):.3f}{mark} ± {np.std(driver):.3f} |")

    lines += [
        "",
        "## Reference points",
        "",
        "| | window AUROC | driver AUROC |",
        "|---|--:|--:|",
        "| exp04 `full` (`cls_token`, 51.2 s, PCA 50, raw) | 0.514 | 0.566 |",
        "| exp04 `scratch` (random initialisation) | 0.516 | 0.577 |",
        "| chance | 0.500 | 0.500 |",
        "",
        "## How much to trust each column",
        "",
        "- **Window-level** compares ~585 known against ~149 unknown windows "
        "per partition. Stable; small differences are meaningful.",
        "- **Driver-level** compares 36 known against 10 unknown — 46 points. "
        "Simulated single-partition sd is **0.08–0.10**, so the ± column here "
        "is the honest measure of what one partition can tell you. This is the "
        "deployment-relevant metric but the noisier one.",
        "",
        "## Limitations",
        "",
        "- **One drive per driver**, so an unknown driver is also an unknown "
        "day: any positive AUROC conflates 'new person' with 'new conditions'. "
        "This bounds every number above. See `DECISIONS.md` C1.",
        "- The LDA projection is fitted on the 36 known drivers, so its "
        "directions are chosen to separate *those* drivers. That it still "
        "helps reject unseen ones is the result, not an assumption.",
        "- Resampling is `np.interp`, which aliases on downsample. At 30 s the "
        "grid is 17.07 Hz, the least affected of the four window lengths.",
        "- Fixed 60-epoch budget, final epoch, no model selection.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Evaluate every configuration on all Phase B test partitions."""
    warnings.filterwarnings("ignore")
    sources = []
    for index in range(1, N_PARTITIONS + 1):
        path = (DATA_INTERIM / f"embeddings_phaseB_{OUTPUT_TOKEN}_"
                               f"{WINDOW_SECONDS:g}s_p{index}.npz")
        if path.exists():
            sources.append(np.load(path, allow_pickle=True))
    print(f"{len(sources)} partition(s)")

    results: dict[str, list[tuple[float, float]]] = {}
    for name, config in CONFIGS.items():
        values = [score_config(cached, config) for cached in sources]
        results[name] = values
        window = np.mean([v[0] for v in values])
        driver = np.mean([v[1] for v in values])
        driver_sd = np.std([v[1] for v in values])
        flag = "  <-- PRE-REGISTERED" if name == "pre-registered" else ""
        print(f"  {name:26s} window {window:.3f} | "
              f"driver {driver:.3f} ± {driver_sd:.3f}{flag}")

    write_report(results)
    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
