"""Figures for exp04 Stage 2.

Four views, each answering a question the tables answer less legibly:

1. **ROC curves** — the headline open-set figure. One panel per representation,
   one curve per partition, the diagonal marking chance. Spread across curves is
   as informative as the mean: five curves hugging the diagonal is a null that no
   single averaged number conveys as plainly.
2. **AUROC comparison** — every representation side by side with its spread
   across partitions, so `full` vs `scratch` and `+ level` vs plain are read as
   one picture rather than assembled from a wide table.
3. **Closed-set read-outs** — the same representations under three classifiers.
   A large spread between read-outs on one representation means the limitation
   was the read-out; a flat profile means it was the representation.
4. **Embedding geometry** — t-SNE of the frozen, adapted and randomly-initialised
   spaces, with never-enrolled drivers drawn as crosses. This is the figure that
   shows *why* an AUROC came out where it did: if the unknown drivers fall inside
   the enrolled clusters, no scoring rule can separate them, and no amount of
   threshold tuning will.

All axes are labelled in the terms of the task rather than of the metric, so a
reader who has not memorised the protocol can still read them.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import roc_curve

from src.config import OUT_FIGURES

SEED = 42
TSNE_PERPLEXITY = 30
TSNE_PCA_COMPONENTS = 50


def figure_path(name: str) -> Path:
    """Where one exp04 figure is written.

    Args:
        name: short slug, e.g. 'roc'.

    Returns:
        Path under the shared figures directory, prefixed with the experiment.
    """
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    return OUT_FIGURES / f"exp04_{name}.png"


def plot_roc(rows_by_representation: dict[str, list[dict]], rule: str) -> Path:
    """ROC per partition, one panel per representation.

    Args:
        rows_by_representation: representation name to per-partition result dicts
            as returned by `evaluate_partition`.
        rule: which scoring rule to draw.

    Returns:
        The written path.
    """
    names = list(rows_by_representation)
    figure, axes = plt.subplots(1, len(names), figsize=(4.6 * len(names), 4.8),
                                squeeze=False, sharey=True)
    for column, name in enumerate(names):
        axis = axes[0][column]
        for index, row in enumerate(rows_by_representation[name], start=1):
            known = row["known_score"][rule]
            unknown = row["unknown_score"][rule]
            membership = np.r_[np.zeros(len(known)), np.ones(len(unknown))]
            false_rate, true_rate, _ = roc_curve(membership, np.r_[known, unknown])
            axis.plot(false_rate, true_rate, lw=1.4, alpha=0.8,
                      label=f"partition {index} — AUC {row['auroc'][rule]:.3f}")
        axis.plot([0, 1], [0, 1], "k--", lw=1, label="chance")
        axis.set_title(name)
        axis.set_xlabel("enrolled driver wrongly rejected")
        if column == 0:
            axis.set_ylabel("unenrolled driver correctly rejected")
        axis.legend(fontsize=7, loc="lower right")
        axis.grid(alpha=0.25)
    figure.suptitle(f"Detecting a driver who was never enrolled — `{rule}` score",
                    fontsize=12)
    figure.tight_layout()
    path = figure_path("roc")
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_auroc_comparison(summaries: dict[str, dict], rules: tuple[str, ...]
                          ) -> Path:
    """Mean open-set AUROC with spread, every representation side by side.

    Args:
        summaries: representation name to `summarise` output.
        rules: scoring rules to show.

    Returns:
        The written path.
    """
    names = list(summaries)
    positions = np.arange(len(names))
    width = 0.8 / len(rules)

    figure, axis = plt.subplots(figsize=(1.9 * len(names) + 3, 5.2))
    for index, rule in enumerate(rules):
        means = [summaries[n][f"auroc:{rule}"][0] for n in names]
        spreads = [summaries[n][f"auroc:{rule}"][1] for n in names]
        axis.bar(positions + index * width - 0.4 + width / 2, means, width,
                 yerr=spreads, capsize=3, label=f"`{rule}`", alpha=0.88)
    axis.axhline(0.5, color="k", ls="--", lw=1.2, label="chance (0.500)")
    axis.set_xticks(positions)
    axis.set_xticklabels(names, rotation=20, ha="right")
    axis.set_ylabel("open-set AUROC")
    axis.set_ylim(0.3, 1.0)
    axis.set_title("Can the representation reject an unenrolled driver?\n"
                   "mean ± sd across partitions")
    axis.legend(fontsize=8, ncol=2)
    axis.grid(alpha=0.25, axis="y")
    figure.tight_layout()
    path = figure_path("auroc_comparison")
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_closed_set(heads: dict[str, dict], chance: float) -> Path:
    """Closed-set top-1 per representation under each read-out.

    Args:
        heads: representation name to `average_heads` output.
        chance: random-guess accuracy.

    Returns:
        The written path.
    """
    names = list(heads)
    read_outs = ("linear_probe", "lda_centroid", "random_forest")
    positions = np.arange(len(names))
    width = 0.8 / len(read_outs)

    figure, axis = plt.subplots(figsize=(1.9 * len(names) + 3, 5.2))
    for index, read_out in enumerate(read_outs):
        means = [heads[n][read_out][1][0] for n in names]
        spreads = [heads[n][read_out][1][1] for n in names]
        axis.bar(positions + index * width - 0.4 + width / 2, means, width,
                 yerr=spreads, capsize=3, label=read_out, alpha=0.88)
    axis.axhline(chance, color="k", ls="--", lw=1.2,
                 label=f"chance ({chance:.1%})")
    axis.set_xticks(positions)
    axis.set_xticklabels(names, rotation=20, ha="right")
    axis.set_ylabel("top-1 accuracy, enrolled drivers")
    axis.set_title("Naming the enrolled driver — same representation, "
                   "three read-outs\nmean ± sd across partitions")
    axis.legend(fontsize=8)
    axis.grid(alpha=0.25, axis="y")
    figure.tight_layout()
    path = figure_path("closed_set")
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_embedding_geometry(representations: dict[str, np.ndarray],
                            drivers: np.ndarray, known: np.ndarray) -> Path:
    """t-SNE of each embedding space, marking the never-enrolled drivers.

    Shows whether adaptation actually reshaped the space into driver clusters,
    and whether unenrolled drivers fall inside them — which is what decides
    whether any rejection rule could work.

    Args:
        representations: name to (n_windows, n_features) embeddings, all from
            the same partition.
        drivers: driver id per window.
        known: driver ids treated as enrolled in that partition.

    Returns:
        The written path.
    """
    names = list(representations)
    enrolled = np.isin(drivers, known)
    codes = np.unique(drivers, return_inverse=True)[1]

    figure, axes = plt.subplots(1, len(names), figsize=(5.2 * len(names), 5.0),
                                squeeze=False)
    for column, name in enumerate(names):
        features = representations[name]
        compact = PCA(n_components=min(TSNE_PCA_COMPONENTS, *features.shape),
                      random_state=SEED).fit_transform(features)
        coords = TSNE(n_components=2, perplexity=TSNE_PERPLEXITY, init="pca",
                      random_state=SEED).fit_transform(compact)
        axis = axes[0][column]
        axis.scatter(coords[enrolled, 0], coords[enrolled, 1], c=codes[enrolled],
                     cmap="turbo", s=7, alpha=0.7, linewidths=0,
                     label="enrolled (36)")
        axis.scatter(coords[~enrolled, 0], coords[~enrolled, 1], c="k",
                     marker="x", s=16, alpha=0.75, linewidths=0.7,
                     label="never enrolled (10)")
        axis.set_title(name)
        axis.set_xticks([])
        axis.set_yticks([])
        axis.legend(fontsize=8, loc="upper right")
    figure.suptitle("Embedding geometry — colour is driver identity; crosses "
                    "were never enrolled", fontsize=12)
    figure.tight_layout()
    path = figure_path("embedding_geometry")
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
