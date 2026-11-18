"""Phase D — frozen vs fine-tuned, and how per-driver scores should be pooled.

## Two gaps this closes

**1. There is no frozen baseline under the current configuration.** Every
frozen number in this project came from the old `cls_token` setup. Phase C's
0.689 is on the fine-tuned encoder, so we cannot presently say how much of it
the fine-tuning bought. This embeds the same 30 s tensor with a **frozen**
`mean_token` encoder and scores it identically.

**2. The pooling rule was inherited, not chosen.** Driver-level AUROC takes the
**median** of a driver's window scores, a choice carried over from
`enroll_and_score.py` and never tested. The argument for it is robustness:
distances are non-negative with a long right tail, and a drive contains odd
windows — stopped at a light, a sharp turn — that drag a mean. The argument
against is that the median deliberately discards the tail, and the stranger
signal may live exactly there ("a few very unusual windows").

Both are cheap, and neither needs the GPU beyond one frozen embedding pass.

## Pooling rules compared

| Rule | What it assumes |
|---|---|
| `median` | the typical window is what identifies a drive (current default) |
| `mean` | every window contributes; outliers are signal, not noise |
| `trimmed` | middle 80% — a compromise |
| `min` | the single best match anywhere in the drive is what matters |
| `q75`, `q90` | the *tail* carries the signal |
| `max` | the single strangest window decides |
| `vote` | fraction of windows exceeding a threshold calibrated on known-train |

## Scoring configuration

The pre-registered one from Phase C: **LDA projection, `l2norm_whiten`,
`mean` prototypes, `cosine` distance** — fixed before any test window was
scored and not re-tuned here. Only the arm and the pooling rule vary.

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_d
```
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from experiments.exp06_encoder_readout.run import embed_with_token
from src.config import DATA_INTERIM
from src.features.build_tensors import tensor_path
from src.models.finetune import OUTPUT_TOKEN
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, project,
                                 prototype_scores, SEED, test_indices,
                                 transform_rows)
from src.models.splits import known_unknown_partitions

WINDOW_SECONDS = 30.0
CONFIG = ("lda", "l2norm_whiten", "mean", "cosine")   # Phase C, pre-registered
POOLINGS = ("median", "mean", "trimmed", "min", "q75", "q90", "max", "vote")
VOTE_PERCENTILE = 90
RESULTS_PATH = Path(__file__).parent / "phase_d.md"


def pool(scores: np.ndarray, rule: str, threshold: float) -> float:
    """Reduce one driver's window scores to a single number.

    Args:
        scores: strangeness scores for one driver's windows.
        rule: one of POOLINGS.
        threshold: cut-off for the `vote` rule, from known-train scores.

    Returns:
        The pooled score, higher meaning stranger.
    """
    if rule == "median":
        return float(np.median(scores))
    if rule == "mean":
        return float(np.mean(scores))
    if rule == "trimmed":
        low, high = np.percentile(scores, [10, 90])
        kept = scores[(scores >= low) & (scores <= high)]
        return float(kept.mean() if len(kept) else scores.mean())
    if rule == "min":
        return float(scores.min())
    if rule == "max":
        return float(scores.max())
    if rule == "vote":
        return float((scores > threshold).mean())
    return float(np.percentile(scores, int(rule[1:])))


def driver_auroc(known: np.ndarray, unknown: np.ndarray,
                 known_drivers: np.ndarray, unknown_drivers: np.ndarray,
                 rule: str, threshold: float) -> float:
    """Driver-level AUROC under one pooling rule.

    Args:
        known: window scores for enrolled drivers' test windows.
        unknown: window scores for stranger windows.
        known_drivers: driver id per known window.
        unknown_drivers: driver id per unknown window.
        rule: pooling rule.
        threshold: cut-off for the `vote` rule.

    Returns:
        AUROC over one pooled score per driver.
    """
    values, memberships = [], []
    for driver in np.unique(known_drivers):
        values.append(pool(known[known_drivers == driver], rule, threshold))
        memberships.append(0)
    for driver in np.unique(unknown_drivers):
        values.append(pool(unknown[unknown_drivers == driver], rule,
                           threshold))
        memberships.append(1)
    return float(roc_auc_score(memberships, values))


def window_scores(features: np.ndarray, drivers: np.ndarray,
                  starts: np.ndarray, known: np.ndarray, unknown: np.ndarray
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
                             float]:
    """Strangeness scores under the pre-registered configuration.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        starts: window start time per window.
        known: enrolled driver ids.
        unknown: never-enrolled driver ids.

    Returns:
        (known test scores, unknown test scores, known test driver ids,
        unknown test driver ids, vote threshold from known-train).
    """
    projection, transform, prototype, rule = CONFIG
    train_index, known_index, unknown_index = test_indices(
        drivers, starts, known, unknown)

    scaler = StandardScaler().fit(features[train_index])
    scaled = scaler.transform(features)
    train_drivers = drivers[train_index]
    p_train, p_all = project(scaled[train_index], scaled, train_drivers,
                             projection)
    t_train, t_all = transform_rows(p_train, p_all, transform)

    score_of = lambda rows: prototype_scores(t_train, train_drivers, rows,
                                             prototype)[rule]
    threshold = float(np.percentile(score_of(t_train), VOTE_PERCENTILE))
    return (score_of(t_all[known_index]), score_of(t_all[unknown_index]),
            drivers[known_index], drivers[unknown_index], threshold)


def write_report(results: dict[str, dict[str, list[float]]],
                 windows: dict[str, list[float]]) -> None:
    """Write the Phase D report inside the experiment folder.

    Args:
        results: {arm: {pooling rule: per-partition driver AUROC}}.
        windows: {arm: per-partition window-level AUROC}.
    """
    lines = [
        "# exp07 Phase D — frozen vs fine-tuned, and the pooling rule",
        "",
        f"{WINDOW_SECONDS:g} s windows, `{OUTPUT_TOKEN}`, "
        f"{N_PARTITIONS} partitions of 36 known / 10 unknown drivers. "
        "Scoring is Phase C's **pre-registered** configuration — LDA "
        "projection, `l2norm_whiten`, `mean` prototypes, `cosine` distance — "
        "held fixed. Only the arm and the pooling rule vary. "
        "**0.500 is chance.**",
        "",
        "## Window-level AUROC (no pooling)",
        "",
        "| Arm | window AUROC |",
        "|---|--:|",
    ]
    for arm, values in windows.items():
        lines.append(f"| `{arm}` | {np.mean(values):.3f} ± "
                     f"{np.std(values):.3f} |")

    lines += [
        "",
        "## Driver-level AUROC by pooling rule",
        "",
        "Each driver's window scores reduced to one number, then AUROC over "
        "36 enrolled against 10 strangers.",
        "",
        "| Pooling | `frozen` | `full` | full − frozen |",
        "|---|--:|--:|--:|",
    ]
    for rule in POOLINGS:
        frozen = np.mean(results["frozen"][rule])
        full = np.mean(results["full"][rule])
        frozen_sd = np.std(results["frozen"][rule])
        full_sd = np.std(results["full"][rule])
        mark = "**" if rule == "median" else ""
        lines.append(f"| {mark}`{rule}`{mark} | {frozen:.3f} ± {frozen_sd:.3f} "
                     f"| {mark}{full:.3f}{mark} ± {full_sd:.3f} "
                     f"| {full - frozen:+.3f} |")

    best_rule = max(POOLINGS, key=lambda r: np.mean(results["full"][r]))
    lines += [
        "",
        f"**`median` is the inherited default**, shown in bold. Best observed "
        f"for `full`: `{best_rule}` at "
        f"{np.mean(results['full'][best_rule]):.3f}.",
        "",
        "## Reading this",
        "",
        "- **`full` − `frozen` is what fine-tuning bought** on open-set "
        "rejection, with the scoring configuration held fixed. It is the only "
        "comparison here that separates the encoder from the read-out.",
        "- **The pooling column is exploratory.** `median` was pre-registered "
        "by inheritance; if another rule wins, that is a finding to confirm "
        "elsewhere, not a number to swap into the headline.",
        "- Driver-level compares 36 against 10 — 46 points — so a single "
        "partition's value carries roughly ±0.09. The ± columns are across "
        "five partitions and are roughly half that.",
        "",
        "## Limitations",
        "",
        "- One drive per driver: a stranger is also an unseen *day*, so part "
        "of any separation is new conditions rather than a new person. "
        "See `DECISIONS.md` C1.",
        "- The frozen arm reuses one embedding for all five partitions (the "
        "encoder never sees labels), whereas `full` was fine-tuned separately "
        "per partition. That is correct, but it means the frozen arm's "
        "variation comes only from the partition draw.",
        "- Scoring configuration was chosen for the fine-tuned arm on inner "
        "validation; it may not be optimal for frozen.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Score both arms under every pooling rule."""
    warnings.filterwarnings("ignore")
    cached = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=True)
    tensor, drivers, starts = cached["X"], cached["driver"], cached["start_time"]
    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=N_PARTITIONS, seed=SEED)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"embedding {tensor.shape} with a frozen {OUTPUT_TOKEN} encoder")
    frozen_features, seconds = embed_with_token(tensor, OUTPUT_TOKEN, device)
    print(f"  done in {seconds:.1f}s -> {frozen_features.shape}")

    results = {arm: {rule: [] for rule in POOLINGS}
               for arm in ("frozen", "full")}
    windows: dict[str, list[float]] = {"frozen": [], "full": []}

    for index, (known, unknown) in enumerate(partitions, start=1):
        full_path = (DATA_INTERIM / f"embeddings_phaseB_{OUTPUT_TOKEN}_"
                                    f"{WINDOW_SECONDS:g}s_p{index}.npz")
        arms = {"frozen": frozen_features,
                "full": np.load(full_path, allow_pickle=True)["E"]}
        for arm, features in arms.items():
            known_s, unknown_s, known_d, unknown_d, threshold = window_scores(
                features, drivers, starts, known, unknown)
            membership = np.r_[np.zeros(len(known_s)), np.ones(len(unknown_s))]
            windows[arm].append(float(roc_auc_score(
                membership, np.r_[known_s, unknown_s])))
            for rule in POOLINGS:
                results[arm][rule].append(driver_auroc(
                    known_s, unknown_s, known_d, unknown_d, rule, threshold))
        print(f"  partition {index}: frozen window "
              f"{windows['frozen'][-1]:.3f} / median "
              f"{results['frozen']['median'][-1]:.3f} | full window "
              f"{windows['full'][-1]:.3f} / median "
              f"{results['full']['median'][-1]:.3f}")

    write_report(results, windows)
    print("\narm      window   median   best pooling")
    for arm in ("frozen", "full"):
        best = max(POOLINGS, key=lambda r: np.mean(results[arm][r]))
        print(f"{arm:8s} {np.mean(windows[arm]):.3f}    "
              f"{np.mean(results[arm]['median']):.3f}    "
              f"{best} {np.mean(results[arm][best]):.3f}")
    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
