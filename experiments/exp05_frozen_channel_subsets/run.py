"""Closed-set driver identification at 46-way, across frozen-embedding channel subsets.

## Two questions, one run

**1. What is the 46-way number?** exp04 reports 36-way because its open-set
protocol holds out 10 of the 46 drivers as never-enrolled, so only 36 can be
enrolled. 36-way is the easier problem (chance 2.8% against 2.2% at 46
drivers), so exp04's 33.2% is not a 46-way number. This run reports both
cohorts on identical embeddings.

**2. Do fewer channels do as well?** 50 channels x 256 dims = 12,800 features
fitted on ~1,240 training windows. Cutting channels is the cheapest available
regularisation, and the driver-actuated subset is the one with a mechanistic
story: those are the signals a human physically commands.

## Why this costs minutes rather than hours

Mantis encodes each channel **independently** (`MantisTrainer.transform` loops
over channels and concatenates), so the 12,800-dim embedding is channel-major:
50 contiguous blocks of 256. Selecting a channel subset is therefore **a column
slice of the cached embedding** — the exact same numbers the encoder would
produce if it had only been shown those channels. No re-embedding, no
fine-tuning, no new tensors.

That property only holds for the **frozen** encoder. A fine-tuned encoder's
channels are still processed independently, but its weights were adapted in the
presence of all 50, so slicing its embeddings would not equal training on the
subset. This experiment is frozen-only for that reason, not merely for cost.

## The control that makes it readable

`actuated11` is compared against **`random11`, five independent draws**. If the
driver-actuated set merely matches random subsets of the same size, then any
change is a dimensionality effect and has nothing to do with those signals being
driver-commanded. Without this control an `actuated11` result cannot be
interpreted at all.

`attention15` ranks channels by exp04's learned attention weights. Those weights
were fitted on labelled training data, so that row is **selection-biased and
descriptive only** — it is reported because it is free, and must not be read as
a fair ablation against the others.

## Data lineage (dimensions at each stage)

| Stage | What | Shape |
|---|---|---|
| `embeddings_armB_51.2s.npz` | frozen Mantis embeddings, exp03 | 2267 x 12800 |
| reshape | channel-major blocks recovered | 2267 x 50 x 256 |
| channel subset | slice `k` blocks | 2267 x k x 256 |
| flatten | read-out input | 2267 x (k * 256) |
| cohort | all 46 drivers, or exp04 partition 1's 36 known | subset of rows |
| split | per-driver chronological 70% train / 5% gap / 25% test | ~1.6k train / ~0.6k test |
| read-out | probe / LDA+centroid / forest | 46 or 36 classes |

Everything upstream of the embeddings is exp03's verified Arm B tensor: the
audited 50-SPN channel set, 46 usable drivers (G1S04, G1S10/11/12 excluded),
51.2 s non-overlapping windows resampled to 512 points = exactly 10.00 Hz.

## Commands

```bash
python -u -m experiments.exp05_frozen_channel_subsets.run
python -u -m experiments.exp05_frozen_channel_subsets.run --cohort 46
```
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from src.models.open_set import N_PARTITIONS, N_UNKNOWN
from src.models.splits import known_unknown_partitions
from src.models.readouts import closed_set_heads
from src.features.build_embeddings import embedding_path as frozen_embedding_path

WINDOW_SECONDS = 51.2
HIDDEN_DIM = 256
SEED = 42
N_RANDOM_DRAWS = 5
RESULTS_PATH = Path(__file__).parent / "results.md"
RESULTS_PATH_120 = Path(__file__).parent / "results_120s.md"

# The signals a driver physically commands, as opposed to the engine's response
# to them. Pinned here rather than imported so the set this run used is readable
# in the report that cites it.
ACTUATED = ("91", "117", "118", "512", "523", "524", "574",
            "1087", "1088", "2945", "7319")

# Top 15 channels by exp04's learned attention weight (partition 1). Ranked
# using labelled training data, so this row is descriptive, not a fair ablation.
ATTENTION_TOP = ("513", "2432", "1242", "5398", "514", "92", "512", "103",
                 "3357", "2659", "3226", "184", "91", "3610", "641")

# accuracy relative to the all-channel reference, in percentage points
FLAG_GREEN = 0.0      # at least as good
FLAG_AMBER = -3.0     # within 3pp below


def subset_columns(channels: np.ndarray, wanted: tuple[str, ...]) -> np.ndarray:
    """Column indices of a channel subset within the flat embedding.

    Args:
        channels: channel names in token order, length n_channels.
        wanted: channel names to keep.

    Returns:
        Column indices into the (n_windows, n_channels * HIDDEN_DIM) matrix,
        in ascending channel order.
    """
    names = [str(c) for c in channels]
    missing = [w for w in wanted if w not in names]
    if missing:
        raise ValueError(f"channels not in the embedding: {missing}")
    blocks = sorted(names.index(w) for w in wanted)
    return np.concatenate([np.arange(b * HIDDEN_DIM, (b + 1) * HIDDEN_DIM)
                           for b in blocks])


def build_subsets(channels: np.ndarray) -> dict[str, tuple[str, ...]]:
    """Define every channel subset this run evaluates.

    Args:
        channels: channel names in token order.

    Returns:
        {subset name: channel names}. Five independent random draws of the same
        size as ACTUATED act as the control for it.
    """
    names = tuple(str(c) for c in channels)
    subsets: dict[str, tuple[str, ...]] = {
        "all50": names,
        "actuated11": ACTUATED,
        "attention15": ATTENTION_TOP,
    }
    for draw in range(N_RANDOM_DRAWS):
        rng = np.random.default_rng(SEED + draw)
        subsets[f"random11_{draw}"] = tuple(
            rng.choice(names, size=len(ACTUATED), replace=False))
    return subsets


def cohort_drivers(drivers: np.ndarray, cohort: int) -> np.ndarray:
    """Driver ids making up one cohort.

    Args:
        drivers: driver id per window.
        cohort: 46 for every driver, 36 for exp04 partition 1's known drivers.

    Returns:
        Sorted driver ids.

    Raises:
        ValueError: if the cohort size is not one this experiment defines.
    """
    if cohort == 46:
        return np.unique(drivers)
    if cohort == 36:
        known, _ = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                            n_partitions=N_PARTITIONS,
                                            seed=SEED)[0]
        return known
    raise ValueError(f"cohort must be 46 or 36, got {cohort}")


def flag_for(delta: float) -> str:
    """Emoji flag for an accuracy change against the all-channel reference.

    Args:
        delta: percentage-point difference from `all50`.

    Returns:
        A green, amber or red flag.
    """
    if delta >= FLAG_GREEN:
        return "🟢"
    return "🟡" if delta >= FLAG_AMBER else "🔴"


def evaluate(features: np.ndarray, drivers: np.ndarray, starts: np.ndarray,
             cohort_ids: np.ndarray) -> dict[str, dict[int, float]]:
    """Score one channel subset for one cohort with all three read-outs.

    Args:
        features: sliced embedding for every window.
        drivers: driver id per window.
        starts: window start time per window.
        cohort_ids: the drivers making up this cohort.

    Returns:
        {read-out name: {k: accuracy}}.
    """
    return closed_set_heads(features, drivers, starts, cohort_ids)


def collapse_random(scores: dict[str, dict[str, dict[int, float]]]
                    ) -> dict[str, tuple[float, float]]:
    """Mean and sd of the random-subset draws, per read-out.

    Args:
        scores: {subset name: {read-out: {k: accuracy}}}.

    Returns:
        {read-out: (mean top-1, sd top-1)} across the random draws.
    """
    draws = [name for name in scores if name.startswith("random11_")]
    heads = scores[draws[0]].keys()
    return {head: (float(np.mean([scores[d][head][1] for d in draws])),
                   float(np.std([scores[d][head][1] for d in draws])))
            for head in heads}


def write_report(results: dict[int, dict[str, dict[str, dict[int, float]]]],
                 subsets: dict[str, tuple[str, ...]]) -> None:
    """Write the results report inside the experiment folder.

    Args:
        results: {cohort: {subset name: {read-out: {k: accuracy}}}}.
        subsets: the channel subsets that were evaluated.
    """
    heads = ("linear_probe", "lda_centroid", "random_forest")
    lines = [
        "# exp05 — 46-way closed set across frozen-embedding channel subsets",
        "",
        "Frozen Mantis embeddings (`embeddings_armB_51.2s.npz`), sliced "
        "channel-major. Mantis encodes each channel independently, so a channel "
        "subset is a **column slice** of the cached embedding and costs nothing "
        "to evaluate. Per-driver chronological 70/5/25 split, seed 42.",
        "",
        "**46-way chance is 2.2%; 36-way chance is 2.8%.** exp04's 33.2% is "
        "36-way and must not be compared with the 46-way rows below.",
        "",
    ]

    for cohort in sorted(results, reverse=True):
        scores = results[cohort]
        reference = {h: scores["all50"][h][1] for h in heads}
        random_mean = collapse_random(scores)
        lines += [
            f"## {cohort}-way",
            "",
            "| Channel set | dims | linear probe | LDA + centroid | "
            "random forest | vs `all50` (best) |",
            "|---|--:|--:|--:|--:|:--:|",
        ]
        named = ["all50", "actuated11", "attention15"]
        for name in named:
            cells, best_delta = [], None
            for head in heads:
                value = scores[name][head][1]
                delta = (value - reference[head]) * 100
                best_delta = delta if best_delta is None else max(best_delta,
                                                                  delta)
                cells.append(f"{value * 100:.1f}%")
            dims = len(subsets[name]) * HIDDEN_DIM
            lines.append(f"| `{name}` | {dims:,} | " + " | ".join(cells)
                         + f" | {flag_for(best_delta)} {best_delta:+.1f}pp |")

        cells, best_delta = [], None
        for head in heads:
            mean, sd = random_mean[head]
            delta = (mean - reference[head]) * 100
            best_delta = delta if best_delta is None else max(best_delta, delta)
            cells.append(f"{mean * 100:.1f}% ± {sd * 100:.1f}%")
        lines.append(f"| `random11` (×{N_RANDOM_DRAWS}) | "
                     f"{len(ACTUATED) * HIDDEN_DIM:,} | " + " | ".join(cells)
                     + f" | {flag_for(best_delta)} {best_delta:+.1f}pp |")
        lines.append("")

    lines += [
        "## How to read this",
        "",
        "- **`actuated11` vs `random11` is the only comparison that says "
        "anything about the driver-actuated signals.** If they match, the "
        "actuated set is not special and any change is a dimensionality effect.",
        "- **`attention15` is selection-biased.** Those channels were ranked by "
        "exp04's attention weights, fitted on labelled training data from this "
        "same split. Descriptive only.",
        "- The flag compares each subset's **best** read-out against `all50`'s "
        f"best: 🟢 at least equal, 🟡 within {abs(FLAG_AMBER):.0f}pp below, "
        "🔴 worse than that.",
        "",
        "## Channel sets",
        "",
        f"- `actuated11` ({len(ACTUATED)}): "
        + ", ".join(f"SPN {c}" for c in ACTUATED),
        f"- `attention15` ({len(ATTENTION_TOP)}): "
        + ", ".join(f"SPN {c}" for c in ATTENTION_TOP),
        "",
        "## Limitations",
        "",
        "- **Frozen encoder only.** Slicing a *fine-tuned* encoder's embeddings "
        "would not equal training on the subset, because its weights were "
        "adapted while all 50 channels were present.",
        "- **One drive per driver**, so the chronological split separates early "
        "from late in a single trip, not across sessions. See `DECISIONS.md` C1.",
        "- Single split per cohort, so no error bars except on `random11`, "
        "where the spread is across channel draws rather than across splits.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Evaluate every channel subset for every cohort and write the report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=int, action="append",
                        choices=(46, 36), default=None)
    # Window length changes both context and effective sampling rate, so the
    # subset comparison is runnable at any cached length.
    parser.add_argument("--window", type=float, default=WINDOW_SECONDS)
    arguments = parser.parse_args()
    cohorts = arguments.cohort or [46, 36]

    cached = np.load(frozen_embedding_path("cls_token", arguments.window),
                     allow_pickle=True)
    embeddings, drivers = cached["E"], cached["driver"]
    starts, channels = cached["start_time"], cached["channels"]
    if not np.isfinite(embeddings).all():
        raise ValueError("cached embeddings contain non-finite values")
    print(f"{embeddings.shape} embeddings | {len(np.unique(drivers))} drivers "
          f"| {len(channels)} channels")

    subsets = build_subsets(channels)
    results: dict[int, dict[str, dict[str, dict[int, float]]]] = {}

    for cohort in cohorts:
        ids = cohort_drivers(drivers, cohort)
        print(f"\n{cohort}-way ({len(ids)} drivers, "
              f"chance {100 / len(ids):.1f}%)")
        results[cohort] = {}
        for name, wanted in subsets.items():
            columns = subset_columns(channels, wanted)
            scores = evaluate(embeddings[:, columns], drivers, starts, ids)
            results[cohort][name] = scores
            best = max(scores, key=lambda h: scores[h][1])
            print(f"  {name:14s} {len(columns):>6,} dims | "
                  + "  ".join(f"{h.split('_')[0]} {scores[h][1] * 100:5.1f}%"
                              for h in scores)
                  + f"  | best {best}")

    global RESULTS_PATH
    if arguments.window != WINDOW_SECONDS:
        RESULTS_PATH = RESULTS_PATH_120
    write_report(results, subsets)
    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
