"""RQ1 — do frozen embeddings separate drivers at all?

Closed-set, 46-way, under the per-driver chronological split: nearest-centroid
and 1-NN on standardised embeddings. Nothing is trained beyond fitting a scaler
and averaging training embeddings, so this measures what the pre-trained
representation already encodes.

It also runs the leakage diagnostic that the published CAN literature omits:
eta-squared per embedding dimension against the driver label *and* against
position in the drive. If the embedding tracks trip phase more strongly than
driver, a good accuracy number is not evidence of behavioural identification.

Run from the repo root in the `truckidme` env:
    python -m src.models.embedding_separability
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

from src.config import DATA_INTERIM, OUT_FIGURES, OUT_REPORTS, WINDOW_SECONDS
from src.models.splits import driver_group, eta_squared, split_by_driver

EMBEDDINGS_PATH = DATA_INTERIM / f"embeddings_{WINDOW_SECONDS}s.npz"
REPORT_PATH = OUT_REPORTS / "embedding_separability.md"
TSNE_DRIVER_PATH = OUT_FIGURES / "embedding_tsne_by_driver.png"
TSNE_PHASE_PATH = OUT_FIGURES / "embedding_tsne_by_trip_phase.png"
SEED = 42
N_PHASE_BINS = 5


def trip_phase(drivers: np.ndarray, start_times: np.ndarray) -> np.ndarray:
    """Bin each window by how far into that driver's drive it occurs.

    Args:
        drivers: driver id per window.
        start_times: window start time per window.

    Returns:
        Phase bin per window, 0 (earliest) to N_PHASE_BINS - 1 (latest).
    """
    phase = np.zeros(len(drivers), dtype=int)
    for driver in np.unique(drivers):
        positions = np.flatnonzero(drivers == driver)
        order = np.argsort(start_times[positions])
        ranks = np.empty(len(order))
        ranks[order] = np.arange(len(order)) / max(len(order) - 1, 1)
        phase[positions] = np.clip((ranks * N_PHASE_BINS).astype(int), 0, N_PHASE_BINS - 1)
    return phase


def centroid_topk(train_z: np.ndarray, train_y: np.ndarray, test_z: np.ndarray,
                  test_y: np.ndarray, ks: tuple[int, ...]) -> dict[int, float]:
    """Nearest-centroid top-k accuracy.

    Args:
        train_z: training embeddings.
        train_y: training driver ids.
        test_z: test embeddings.
        test_y: test driver ids.
        ks: the k values to report.

    Returns:
        {k: accuracy} where accuracy is the share of test windows whose true
        driver is among the k nearest centroids.
    """
    labels = np.unique(train_y)
    centroids = np.stack([train_z[train_y == label].mean(axis=0) for label in labels])
    distances = pairwise_distances(test_z, centroids, n_jobs=-1)
    ranking = labels[np.argsort(distances, axis=1)]
    return {k: float(np.mean([truth in row[:k] for truth, row in zip(test_y, ranking)]))
            for k in ks}


def plot_tsne(coords: np.ndarray, colours: np.ndarray, title: str, path: Path,
              *, discrete_legend: str | None = None) -> Path:
    """Save a t-SNE scatter plot.

    Args:
        coords: (n_samples, 2) t-SNE coordinates.
        colours: value per sample used for colour.
        title: plot title.
        path: output path.
        discrete_legend: colour-bar label, or None to omit the bar.

    Returns:
        The written path.
    """
    figure, axes = plt.subplots(figsize=(7.5, 6.5))
    scatter = axes.scatter(coords[:, 0], coords[:, 1], c=colours, s=6,
                           cmap="turbo", alpha=0.75, linewidths=0)
    axes.set_title(title)
    axes.set_xlabel("t-SNE 1")
    axes.set_ylabel("t-SNE 2")
    if discrete_legend:
        figure.colorbar(scatter, ax=axes, label=discrete_legend)
    figure.tight_layout()
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def main() -> None:
    """Measure separability, run the leakage diagnostic, and report."""
    bundle = np.load(EMBEDDINGS_PATH, allow_pickle=False)
    embeddings, drivers, starts = bundle["Z"], bundle["driver"], bundle["start_time"]
    print(f"embeddings {embeddings.shape} across {len(np.unique(drivers))} drivers")

    train_index, test_index = split_by_driver(drivers, starts)
    scaler = StandardScaler().fit(embeddings[train_index])     # train only
    scaled = scaler.transform(embeddings)

    centroid = centroid_topk(scaled[train_index], drivers[train_index],
                             scaled[test_index], drivers[test_index], ks=(1, 2, 5))
    knn = KNeighborsClassifier(n_neighbors=1).fit(scaled[train_index], drivers[train_index])
    knn1 = float(knn.score(scaled[test_index], drivers[test_index]))
    knn5 = float(KNeighborsClassifier(n_neighbors=5)
                 .fit(scaled[train_index], drivers[train_index])
                 .score(scaled[test_index], drivers[test_index]))

    phase = trip_phase(drivers, starts)
    eta_driver = eta_squared(scaled[train_index], drivers[train_index])
    eta_phase = eta_squared(scaled[train_index], phase[train_index])
    eta_group = eta_squared(scaled[train_index],
                            np.array([driver_group(d) for d in drivers[train_index]]))

    print(f"running t-SNE ({len(scaled)} points)")
    compact = PCA(n_components=min(50, scaled.shape[0], scaled.shape[1]),
                  random_state=SEED).fit(scaled[train_index]).transform(scaled)
    coords = TSNE(n_components=2, perplexity=30, init="pca",
                  random_state=SEED).fit_transform(compact)
    driver_codes = np.unique(drivers, return_inverse=True)[1]
    plot_tsne(coords, driver_codes,
              f"Mantis embeddings by driver ({WINDOW_SECONDS}s windows, frozen encoder)",
              TSNE_DRIVER_PATH, discrete_legend="driver index")
    plot_tsne(coords, phase,
              "Same embeddings by position in the drive (leakage check)",
              TSNE_PHASE_PATH, discrete_legend="trip phase (0 = start, 4 = end)")

    floor = 1.0 / len(np.unique(drivers))
    verdict = ("behavioural signal dominates" if eta_driver.mean() > 2 * eta_phase.mean()
               else "trip phase rivals driver identity — treat accuracy with suspicion")
    lines = [
        f"# RQ1 — separability of frozen Mantis embeddings ({WINDOW_SECONDS}s windows)",
        "",
        "Closed-set, 46-way, per-driver chronological split (train first 70%, 5% gap "
        f"discarded, test last 25%). Random floor = {floor:.1%}. No training beyond a "
        "scaler fitted on the training windows only.",
        "",
        "## Headline",
        "",
        "| Method | Top-1 | Top-2 | Top-5 | vs random |",
        "|---|---:|---:|---:|---:|",
        f"| Nearest centroid | **{centroid[1]:.1%}** | {centroid[2]:.1%} | "
        f"{centroid[5]:.1%} | {centroid[1] / floor:.1f}x |",
        f"| 1-NN | {knn1:.1%} | — | — | {knn1 / floor:.1f}x |",
        f"| 5-NN | {knn5:.1%} | — | — | {knn5 / floor:.1f}x |",
        "",
        f"- train windows: {len(train_index)} · test windows: {len(test_index)}",
        f"- embedding dimensions: {embeddings.shape[1]} (8 channels x 256)",
        "",
        "## Leakage diagnostic — what do the embeddings actually encode?",
        "",
        "eta-squared per embedding dimension, computed on training windows only. "
        "Driver is the label we want; trip phase is the confound we fear.",
        "",
        "| Label | mean eta^2 | median | max | dims > 0.5 |",
        "|---|---:|---:|---:|---:|",
        f"| Driver identity (46 classes) | {eta_driver.mean():.3f} | "
        f"{np.median(eta_driver):.3f} | {eta_driver.max():.3f} | "
        f"{int((eta_driver > 0.5).sum())} |",
        f"| Trip phase ({N_PHASE_BINS} bins) | {eta_phase.mean():.3f} | "
        f"{np.median(eta_phase):.3f} | {eta_phase.max():.3f} | "
        f"{int((eta_phase > 0.5).sum())} |",
        f"| Awareness group (G1/G2/G3) | {eta_group.mean():.3f} | "
        f"{np.median(eta_group):.3f} | {eta_group.max():.3f} | "
        f"{int((eta_group > 0.5).sum())} |",
        "",
        f"**Verdict:** {verdict}",
        "",
        "Note that a high driver eta^2 is *not* proof of behavioural identification: "
        "with one drive per driver, driver identity and trip conditions are "
        "confounded by construction (see DECISIONS.md C1). This diagnostic can only "
        "show whether the embedding is dominated by *within-drive position*, which "
        "would be a second, independent problem.",
        "",
        "## Figures",
        "",
        f"- `{TSNE_DRIVER_PATH.relative_to(OUT_FIGURES.parent.parent)}` — coloured by driver",
        f"- `{TSNE_PHASE_PATH.relative_to(OUT_FIGURES.parent.parent)}` — same points, "
        "coloured by position in the drive",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")

    print(f"\ncentroid top-1 {centroid[1]:.1%} | top-5 {centroid[5]:.1%} | "
          f"1-NN {knn1:.1%} (floor {floor:.1%})")
    print(f"eta^2 driver {eta_driver.mean():.3f} vs phase {eta_phase.mean():.3f}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
