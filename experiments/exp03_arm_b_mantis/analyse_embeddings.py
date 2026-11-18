"""Step 3 of Arm B: what did Mantis actually encode?

Every window is now a point in 50 x 256 = 12,800 dimensions, placed there by a
frozen encoder that was never told about drivers. Four questions, in order,
because each one gates the next.

**1. Does the space separate drivers at all?** Measured by eta-squared per
embedding dimension with driver as the group, and by actually classifying.

**2. Or does it separate trip phase instead?** The trap: the truck warms up,
traffic thickens, the route changes character, so early-drive windows may cluster
with other early-drive windows regardless of who was driving. That looks like
structure and says nothing about people. The same eta-squared is therefore computed
against **trip phase** and against **awareness group** on identical embeddings. If
phase separates better than driver, question 1's apparent success is an artefact.

**3. Can a driver be named from a window?** Each driver's early windows are averaged
into one prototype; a late window is assigned to its nearest prototype. Enrolment
and query are separated by a discarded gap, so no window is ever matched against
its own neighbour.

**4. Is the dimensionality defeating us?** In very high dimension all pairs of
points become roughly equidistant, which destroys "nearest prototype" as a concept.
PCA compresses to k dimensions, and **k is swept rather than assumed** -- the 50 in
the existing code is an inherited default with no argument behind it. The sweep runs
on an **inner split of the training windows**, never on the test set, matching the
protocol in `encoder_config_selection.md`.

The accuracy-versus-k curve is itself a result. Flat in k means dimensionality was
never the bottleneck and the limitation is the representation. A peak at small k
that falls away confirms the high-dimension distance problem. A monotonic rise to
the ceiling means the information is spread thin and PCA is discarding it.

**Caveat on the sweep.** The inner split draws from the same 46 drives, so its
windows are correlated with the outer training windows. It is the right protocol
for this data, but the chosen k is less independently selected than the window
count suggests.

Reuses `trip_phase`, `centroid_topk`, `plot_tsne` from
`src.models.embedding_separability` and `eta_squared`, `split_by_driver` from
`src.models.splits`; only the paths and the sweep are new.

Run from the repo root in the `truckidme` env:
    /home/ap9107/anaconda3/envs/truckidme/bin/python \\
        -m experiments.exp03_arm_b_mantis.analyse_embeddings
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

from src.config import OUT_FIGURES
from src.features.build_embeddings import embedding_path as frozen_embedding_path
from src.models.embedding_separability import centroid_topk, plot_tsne, trip_phase
from src.models.splits import driver_group, eta_squared, split_by_driver

EXPERIMENT_DIR = Path(__file__).resolve().parent
REPORT_PATH = EXPERIMENT_DIR / "embedding_analysis.md"

WINDOW_LENGTHS: tuple[float, ...] = (30.0, 51.2, 90.0, 120.0)
PCA_CANDIDATES: tuple[int, ...] = (10, 25, 50, 100, 200, 400)
INNER_TRAIN = 0.70        # of the outer training windows, for choosing k
SEED = 42
TSNE_PERPLEXITY = 30


TOKEN = "cls_token"   # the token in use when this analysis was run; see README


def embedding_path(window_seconds: float) -> Path:
    """Where the frozen `cls_token` embeddings for one window length live.

    Reads the committed artefact (`src/features/build_embeddings.py`), verified
    identical to the `embeddings_armB_*` files this analysis first ran on.

    Args:
        window_seconds: window length.

    Returns:
        Path under `data/interim_data/`.
    """
    return frozen_embedding_path(TOKEN, window_seconds)


def inner_split(drivers: np.ndarray, starts: np.ndarray,
                train_index: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split the training windows again, chronologically within each driver.

    Choosing k on the outer test set would leak it. This carves the outer training
    windows into an inner train and inner validation part, keeping the same
    chronological discipline so the inner validation windows are later than the
    inner training ones for every driver.

    Args:
        drivers: driver per window, full arrays.
        starts: window start time per window, full arrays.
        train_index: positions of the outer training windows.

    Returns:
        (inner_train, inner_validation) as positions into the full arrays.
    """
    inner_train, inner_validation = [], []
    for driver in np.unique(drivers[train_index]):
        rows = train_index[drivers[train_index] == driver]
        rows = rows[np.argsort(starts[rows])]
        cut = int(INNER_TRAIN * len(rows))
        inner_train.append(rows[:cut])
        inner_validation.append(rows[cut:])
    return np.concatenate(inner_train), np.concatenate(inner_validation)


def choose_components(scaled: np.ndarray, drivers: np.ndarray,
                      inner_train: np.ndarray,
                      inner_validation: np.ndarray) -> list[dict]:
    """Score each candidate k on the inner validation split.

    Args:
        scaled: standardised embeddings, full array.
        drivers: driver per window.
        inner_train: positions to fit PCA and prototypes on.
        inner_validation: positions to score.

    Returns:
        One record per candidate k: components, variance explained, inner top-1.
    """
    ceiling = min(len(inner_train), scaled.shape[1])
    rows = []
    for k in PCA_CANDIDATES:
        if k > ceiling:
            continue
        pca = PCA(n_components=k, random_state=SEED).fit(scaled[inner_train])
        reduced = pca.transform(scaled)
        scores = centroid_topk(reduced[inner_train], drivers[inner_train],
                               reduced[inner_validation],
                               drivers[inner_validation], ks=(1,))
        rows.append({
            "components": k,
            "variance_explained": float(pca.explained_variance_ratio_.sum()),
            "inner_top1": scores[1],
        })
    return rows


def score_test(scaled: np.ndarray, drivers: np.ndarray, train_index: np.ndarray,
               test_index: np.ndarray, components: int) -> dict:
    """Classify the held-out test windows at the chosen k.

    Args:
        scaled: standardised embeddings, full array.
        drivers: driver per window.
        train_index: outer training positions.
        test_index: outer test positions.
        components: PCA dimensionality chosen on the inner split.

    Returns:
        Nearest-centroid top-1/2/5 and 1-NN / 5-NN accuracies.
    """
    pca = PCA(n_components=components, random_state=SEED).fit(scaled[train_index])
    reduced = pca.transform(scaled)
    centroid = centroid_topk(reduced[train_index], drivers[train_index],
                             reduced[test_index], drivers[test_index],
                             ks=(1, 2, 5))
    knn1 = float(KNeighborsClassifier(n_neighbors=1)
                 .fit(reduced[train_index], drivers[train_index])
                 .score(reduced[test_index], drivers[test_index]))
    knn5 = float(KNeighborsClassifier(n_neighbors=5)
                 .fit(reduced[train_index], drivers[train_index])
                 .score(reduced[test_index], drivers[test_index]))
    return {"centroid_top1": centroid[1], "centroid_top2": centroid[2],
            "centroid_top5": centroid[5], "knn1": knn1, "knn5": knn5}


def label_separability(scaled: np.ndarray, drivers: np.ndarray,
                       phase: np.ndarray, train_index: np.ndarray) -> dict:
    """Eta-squared per embedding dimension against three competing labels.

    The decisive comparison of this report. All three are computed on the same
    standardised embeddings and the same training windows, so the only thing that
    changes is what we claim the structure means.

    Args:
        scaled: standardised embeddings, full array.
        drivers: driver per window.
        phase: trip-phase bin per window.
        train_index: outer training positions.

    Returns:
        Mean and max eta-squared for driver, phase and awareness group.
    """
    groups = np.array([driver_group(d) for d in drivers])
    out = {}
    for name, labels in (("driver", drivers), ("phase", phase), ("group", groups)):
        values = eta_squared(scaled[train_index], labels[train_index])
        out[f"eta_{name}_mean"] = float(np.nanmean(values))
        out[f"eta_{name}_max"] = float(np.nanmax(values))
        out[f"eta_{name}_over_10pct"] = int(np.nansum(values > 0.10))
    return out


def analyse(window_seconds: float, make_figures: bool) -> dict:
    """Run every question for one window length.

    Args:
        window_seconds: window length.
        make_figures: whether to write the two t-SNE plots for this length.

    Returns:
        Sweep records, test scores, separability figures and shapes.
    """
    bundle = np.load(embedding_path(window_seconds), allow_pickle=False)
    embeddings, drivers = bundle["E"], bundle["driver"]
    starts = bundle["start_time"]

    train_index, test_index = split_by_driver(drivers, starts)
    scaler = StandardScaler().fit(embeddings[train_index])   # train only
    scaled = scaler.transform(embeddings)
    phase = trip_phase(drivers, starts)

    inner_train, inner_validation = inner_split(drivers, starts, train_index)
    sweep = choose_components(scaled, drivers, inner_train, inner_validation)
    best = max(sweep, key=lambda r: r["inner_top1"])

    result = {
        "window_seconds": window_seconds,
        "windows": int(len(embeddings)),
        "features": int(embeddings.shape[1]),
        "drivers": int(len(np.unique(drivers))),
        "n_train": int(len(train_index)),
        "n_test": int(len(test_index)),
        "chosen_components": best["components"],
        "chosen_inner_top1": best["inner_top1"],
        "sweep": sweep,
    }
    result.update(score_test(scaled, drivers, train_index, test_index,
                             best["components"]))
    result.update(label_separability(scaled, drivers, phase, train_index))

    if make_figures:
        compact = PCA(n_components=min(50, len(train_index), scaled.shape[1]),
                      random_state=SEED).fit(scaled[train_index]).transform(scaled)
        coords = TSNE(n_components=2, perplexity=TSNE_PERPLEXITY, init="pca",
                      random_state=SEED).fit_transform(compact)
        codes = {d: i for i, d in enumerate(sorted(set(drivers)))}
        plot_tsne(coords, np.array([codes[d] for d in drivers]),
                  f"Arm B frozen Mantis, {window_seconds:g}s — by driver",
                  OUT_FIGURES / f"armB_tsne_driver_{window_seconds:g}s.png",
                  discrete_legend="driver index")
        plot_tsne(coords, phase,
                  f"Arm B frozen Mantis, {window_seconds:g}s — by trip phase",
                  OUT_FIGURES / f"armB_tsne_phase_{window_seconds:g}s.png",
                  discrete_legend="trip phase (0 = start, 4 = end)")
        result["figures"] = True
    return result


def build_report(rows: list[dict], chance: float) -> str:
    """Render the analysis.

    Args:
        rows: one record per window length.
        chance: random-guess accuracy.

    Returns:
        Markdown report.
    """
    lines = [
        "# Arm B embedding analysis — what did the frozen encoder encode?",
        "",
        f"**50 channels, {rows[0]['features']} embedding features, "
        f"{rows[0]['drivers']} drivers, random floor {chance:.2%}.** Frozen Mantis, "
        "no training. Standardisation and PCA are fitted on training windows only; "
        "the split is chronological within each driver with a discarded gap.",
        "",
        "## 1–3. Can a driver be named from a window?",
        "",
        "Nearest prototype: each driver's early windows averaged into one point, "
        "each late window assigned to the closest.",
        "",
        "| Window | Train | Test | k | Centroid top-1 | top-5 | 1-NN | 5-NN |",
        "|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['window_seconds']:g}s | {row['n_train']} | {row['n_test']} | "
            f"{row['chosen_components']} | **{row['centroid_top1']:.1%}** | "
            f"{row['centroid_top5']:.1%} | {row['knn1']:.1%} | {row['knn5']:.1%} |")

    lines += [
        "",
        "## 2. Driver, or trip phase? — the decisive comparison",
        "",
        "η² per embedding dimension against three competing labels, on identical "
        "embeddings and identical training windows. **If phase separates better "
        "than driver, the encoder is reading drive progression rather than "
        "identity**, and the accuracies above are an artefact.",
        "",
        "| Window | η² driver (mean / max) | η² phase (mean / max) | "
        "η² group (mean / max) | dims > 0.10: driver / phase |",
        "|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['window_seconds']:g}s "
            f"| {row['eta_driver_mean']:.4f} / {row['eta_driver_max']:.3f} "
            f"| {row['eta_phase_mean']:.4f} / {row['eta_phase_max']:.3f} "
            f"| {row['eta_group_mean']:.4f} / {row['eta_group_max']:.3f} "
            f"| {row['eta_driver_over_10pct']} / {row['eta_phase_over_10pct']} |")

    lines += [
        "",
        "## 4. Is the dimensionality defeating us? — the k sweep",
        "",
        "Scored on an **inner** chronological split of the training windows, so the "
        "test windows above were never used to choose k. The 50 in the inherited "
        "code was a default with no argument behind it.",
        "",
        "| Window | k | Variance explained | Inner top-1 |",
        "|--:|--:|--:|--:|",
    ]
    for row in rows:
        for record in row["sweep"]:
            mark = " ✅" if record["components"] == row["chosen_components"] else ""
            lines.append(
                f"| {row['window_seconds']:g}s | {record['components']}{mark} "
                f"| {record['variance_explained']:.1%} "
                f"| {record['inner_top1']:.1%} |")

    lines += [
        "",
        "### How to read the curve",
        "",
        "- **flat in k** — dimensionality was never the bottleneck; the limitation "
        "is the representation itself",
        "- **peak at small k, falling after** — confirms that distances degenerate "
        "in high dimension, which is what nearest-prototype depends on",
        "- **monotonic rise to the ceiling** — information is spread thin across "
        "dimensions and PCA is discarding it",
        "",
        "**Caveat.** The inner split draws from the same 46 drives, so its windows "
        "are correlated with the outer training windows. It is the right protocol "
        "for this data, but k is less independently chosen than the window count "
        "suggests.",
        "",
        "## Figures",
        "",
        "Two t-SNE projections of the **same points**, coloured two ways — if the "
        "clusters follow phase rather than driver, that is visible in one glance:",
        "",
        "- `outputs/figures/armB_tsne_driver_*.png`",
        "- `outputs/figures/armB_tsne_phase_*.png`",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Analyse every window length's embeddings and write the report."""
    missing = [w for w in WINDOW_LENGTHS if not embedding_path(w).exists()]
    if missing:
        raise FileNotFoundError(
            f"run embed.py first; missing: {', '.join(f'{w:g}s' for w in missing)}")

    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    rows = []
    for window_seconds in WINDOW_LENGTHS:
        row = analyse(window_seconds, make_figures=True)
        rows.append(row)
        print(f"  {row['window_seconds']:>6g}s  k={row['chosen_components']:>3}  "
              f"centroid top1={row['centroid_top1']:.1%}  "
              f"1NN={row['knn1']:.1%}  "
              f"η² driver={row['eta_driver_mean']:.4f}  "
              f"phase={row['eta_phase_mean']:.4f}")

    chance = 1 / rows[0]["drivers"]
    REPORT_PATH.write_text(build_report(rows, chance))

    worse = [r for r in rows if r["eta_phase_mean"] >= r["eta_driver_mean"]]
    names = ", ".join(f"{r['window_seconds']:g}s" for r in worse)
    print(f"\nwindow lengths where phase separates at least as well as driver: "
          f"{len(worse)}/{len(rows)}" + (f"  ({names})" if worse else ""))
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
