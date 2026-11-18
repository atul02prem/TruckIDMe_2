"""Rank channels by how much driver identity each one's own embedding carries.

## Why rank at all

exp05's subset results showed that the hypothesis-driven subset (`actuated11`)
is worse than random channel draws of the same size, and that the
attention-derived subset is selection-biased because its ranking was fitted on
labelled data from the evaluation split. Neither tells us which channels
actually carry identity. This does, with the selection kept clean.

## How selection stays leak-free

Each channel occupies its own contiguous 256-dim block of the frozen embedding,
because Mantis encodes channels independently. For each block we compute
`eta_squared` — between-driver variance as a fraction of total — **on
known-train windows only**, and average it over the block's 256 dimensions.
That is a model-free, label-aware statistic computed without touching a single
test window, so ranking by it and then evaluating the top-k on the test split
is honest.

Per-channel *test* accuracy is also reported, but only as a descriptive check
that the ranking means something. It is never used to select.

## The comparison that matters

Top-k by this ranking is compared against:

- `all50` — does selection beat using everything?
- `random11` from `run.py` — does a principled ranking beat chance selection?
- `actuated11` — does it beat the mechanistic hypothesis?

## Commands

```bash
python -u -m experiments.exp05_frozen_channel_subsets.channel_ranking
python -u -m experiments.exp05_frozen_channel_subsets.channel_ranking --window 120
```
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from experiments.exp05_frozen_channel_subsets.run import (ACTUATED,
                                                          HIDDEN_DIM,
                                                          WINDOW_SECONDS,
                                                          subset_columns)
from src.config import OUT_FIGURES
from src.models.splits import eta_squared, split_by_driver
from src.models.readouts import closed_set_heads
from src.features.build_embeddings import embedding_path as frozen_embedding_path

TOP_K = (5, 11, 15, 25, 50)
PROBE_MAX_ITER = 5000
RESULTS_PATH = Path(__file__).parent / "channel_ranking.md"
FIGURE_PATH = OUT_FIGURES / "exp05_channel_ranking.png"
TOP_SHOWN = 20


def channel_eta_squared(embeddings: np.ndarray, drivers: np.ndarray,
                        train_index: np.ndarray, n_channels: int) -> np.ndarray:
    """Mean between-driver eta-squared of each channel's embedding block.

    Computed on training windows only, so it can be used to select channels
    without leaking the test split.

    Args:
        embeddings: (n_windows, n_channels * HIDDEN_DIM).
        drivers: driver id per window.
        train_index: positions of the training windows.
        n_channels: number of channels.

    Returns:
        Mean eta-squared per channel, shape (n_channels,).
    """
    values = eta_squared(embeddings[train_index], drivers[train_index])
    return values.reshape(n_channels, HIDDEN_DIM).mean(axis=1)


def channel_accuracy(embeddings: np.ndarray, drivers: np.ndarray,
                     train_index: np.ndarray, test_index: np.ndarray,
                     n_channels: int) -> np.ndarray:
    """Top-1 accuracy of a probe fitted on each channel's block alone.

    Descriptive only — this uses the test split and must never drive selection.

    Args:
        embeddings: (n_windows, n_channels * HIDDEN_DIM).
        drivers: driver id per window.
        train_index: positions of the training windows.
        test_index: positions of the test windows.
        n_channels: number of channels.

    Returns:
        Accuracy per channel, shape (n_channels,).
    """
    out = np.zeros(n_channels)
    for channel in range(n_channels):
        block = embeddings[:, channel * HIDDEN_DIM:(channel + 1) * HIDDEN_DIM]
        scaler = StandardScaler().fit(block[train_index])
        probe = LogisticRegression(max_iter=PROBE_MAX_ITER).fit(
            scaler.transform(block[train_index]), drivers[train_index])
        out[channel] = probe.score(scaler.transform(block[test_index]),
                                   drivers[test_index])
    return out


def plot_ranking(names: list[str], eta: np.ndarray, accuracy: np.ndarray,
                 window_seconds: float) -> None:
    """Draw the channel ranking and the agreement between the two measures.

    Args:
        names: channel names in token order.
        eta: mean eta-squared per channel (training windows).
        accuracy: single-channel probe accuracy per channel (test windows).
        window_seconds: window length, for the title.
    """
    order = np.argsort(-eta)[:TOP_SHOWN][::-1]
    figure, axes = plt.subplots(1, 2, figsize=(13, 7))

    axes[0].barh(range(len(order)), eta[order], color="#4C72B0")
    axes[0].set_yticks(range(len(order)))
    axes[0].set_yticklabels([f"SPN {names[i]}" for i in order], fontsize=9)
    axes[0].set_xlabel("mean between-driver $\\eta^2$ (train windows)")
    axes[0].set_title(f"Top {TOP_SHOWN} channels by identity content")

    axes[1].scatter(eta, accuracy * 100, s=28, color="#4C72B0", alpha=0.8)
    for i in np.argsort(-eta)[:8]:
        axes[1].annotate(names[i], (eta[i], accuracy[i] * 100), fontsize=8,
                         xytext=(4, 3), textcoords="offset points")
    correlation = float(np.corrcoef(eta, accuracy)[0, 1])
    axes[1].set_xlabel("mean $\\eta^2$ (train, used for selection)")
    axes[1].set_ylabel("single-channel probe top-1 % (test)")
    axes[1].set_title(f"Selection statistic vs held-out accuracy "
                      f"(r = {correlation:.2f})")

    figure.suptitle(f"Per-channel driver identity in frozen Mantis embeddings "
                    f"({window_seconds:g} s windows, 46 drivers)")
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=150)
    plt.close(figure)


def write_report(names: list[str], eta: np.ndarray, accuracy: np.ndarray,
                 scores: dict[int, dict[str, dict[int, float]]],
                 window_seconds: float, n_drivers: int) -> None:
    """Write the ranking report inside the experiment folder.

    Args:
        names: channel names in token order.
        eta: mean eta-squared per channel.
        accuracy: single-channel probe accuracy per channel.
        scores: {k: {read-out: {rank: accuracy}}} for each top-k subset.
        window_seconds: window length.
        n_drivers: cohort size.
    """
    order = np.argsort(-eta)
    heads = ("linear_probe", "lda_centroid", "random_forest")
    reference = {h: scores[50][h][1] for h in heads}
    lines = [
        f"# exp05 — per-channel identity ranking ({window_seconds:g} s windows)",
        "",
        f"{n_drivers}-way closed set, chance {100 / n_drivers:.1f}%. Each "
        "channel occupies its own 256-dim block of the frozen embedding, so a "
        "channel's identity content can be measured on its own.",
        "",
        "**Selection is leak-free.** Channels are ranked by mean between-driver "
        "`eta_squared` over their 256 dims, computed on **training windows "
        "only**. The single-channel probe accuracy below uses the test split "
        "and is reported as a descriptive check — it never drives selection.",
        "",
        "## Top-k by ranking",
        "",
        "| Channel set | dims | linear probe | LDA + centroid | random forest |",
        "|---|--:|--:|--:|--:|",
    ]
    for k in sorted(scores):
        cells = " | ".join(f"{scores[k][h][1] * 100:.1f}%" for h in heads)
        label = "`all50`" if k == 50 else f"`top{k}`"
        lines.append(f"| {label} | {k * HIDDEN_DIM:,} | {cells} |")
    best_k = max(scores, key=lambda k: max(scores[k][h][1] for h in heads))
    lines += [
        "",
        f"Best subset: **{'all50' if best_k == 50 else f'top{best_k}'}** at "
        f"{max(scores[best_k][h][1] for h in heads) * 100:.1f}%, against "
        f"`all50`'s {max(reference.values()) * 100:.1f}%.",
        "",
        "## Channel ranking",
        "",
        "| Rank | Channel | mean $\\eta^2$ (train) | single-channel probe (test) |",
        "|--:|---|--:|--:|",
    ]
    for rank, index in enumerate(order[:TOP_SHOWN], start=1):
        actuated = " ⚙" if names[index] in ACTUATED else ""
        lines.append(f"| {rank} | SPN {names[index]}{actuated} | "
                     f"{eta[index]:.4f} | {accuracy[index] * 100:.1f}% |")
    in_top = [names[i] for i in order[:len(ACTUATED)] if names[i] in ACTUATED]
    lines += [
        "",
        f"⚙ marks a driver-actuated channel. **{len(in_top)} of "
        f"{len(ACTUATED)}** actuated channels appear in the top "
        f"{len(ACTUATED)}: {', '.join(f'SPN {c}' for c in in_top) or 'none'}.",
        "",
        f"Agreement between the selection statistic and held-out single-channel "
        f"accuracy: r = {float(np.corrcoef(eta, accuracy)[0, 1]):.2f}.",
        "",
        f"## Figure",
        "",
        f"- `{FIGURE_PATH}`",
        "",
        "## Limitations",
        "",
        "- **Single split, no error bars.** The random-draw control in "
        "`results.md` is what bounds chance-level subset performance.",
        "- **Channels are ranked individually**, so a channel that is only "
        "useful in combination with another is ranked low. This measures "
        "marginal, not joint, identity content.",
        "- Frozen encoder only; one drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Rank channels, evaluate top-k subsets and write the report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, default=WINDOW_SECONDS)
    arguments = parser.parse_args()

    cached = np.load(frozen_embedding_path("cls_token", arguments.window),
                     allow_pickle=True)
    embeddings, drivers = cached["E"], cached["driver"]
    starts, channels = cached["start_time"], cached["channels"]
    names = [str(c) for c in channels]
    cohort = np.unique(drivers)

    train_index, test_index = split_by_driver(drivers, starts)
    print(f"{embeddings.shape} | {len(cohort)} drivers | "
          f"{len(train_index)} train / {len(test_index)} test windows")

    eta = channel_eta_squared(embeddings, drivers, train_index, len(names))
    print("ranked channels by train-only eta^2; fitting 50 single-channel "
          "probes for the descriptive check")
    accuracy = channel_accuracy(embeddings, drivers, train_index, test_index,
                                len(names))

    order = np.argsort(-eta)
    print(f"\ntop 10: "
          + ", ".join(f"SPN {names[i]}" for i in order[:10]))
    print(f"eta^2 vs test accuracy r = "
          f"{float(np.corrcoef(eta, accuracy)[0, 1]):.2f}\n")

    scores: dict[int, dict[str, dict[int, float]]] = {}
    for k in TOP_K:
        wanted = tuple(names[i] for i in order[:k])
        columns = subset_columns(channels, wanted)
        scores[k] = closed_set_heads(embeddings[:, columns], drivers, starts,
                                     cohort)
        best = max(scores[k], key=lambda h: scores[k][h][1])
        print(f"  top{k:<3d} {len(columns):>6,} dims | "
              + "  ".join(f"{h.split('_')[0]} {scores[k][h][1] * 100:5.1f}%"
                          for h in scores[k])
              + f"  | best {best}")

    plot_ranking(names, eta, accuracy, arguments.window)
    write_report(names, eta, accuracy, scores, arguments.window, len(cohort))
    print(f"\nfigure  -> {FIGURE_PATH}")
    print(f"results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
