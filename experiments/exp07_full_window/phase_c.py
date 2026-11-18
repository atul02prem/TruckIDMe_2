"""Phase C — exhaustive open-set scoring sweep on saved fine-tuned embeddings.

## Why every open-set number so far may be an artefact of one design choice

exp04 reported AUROC ~0.514 across five rules and concluded open-set rejection
fails on this data. But **all five rules score against a class prototype** — the
mean of a driver's training embeddings in PCA space. A single mean per driver is
a crude density model: it assumes each driver occupies one roughly spherical
blob. If a driver's windows form a curve through embedding space — which a
single continuous drive plausibly does — the mean may sit in a region the driver
never actually occupies, and distance to it says little.

**k-NN distance to the nearest training window makes no such assumption**, and
is a standard out-of-distribution baseline. It was
never tried. Neither were density estimators, nor local-density methods, nor the
representation transforms that distance metrics are known to be sensitive to.

So the null may be real, or it may be an artefact of prototype scoring. This
sweep settles it by trying everything that is cheap.

## What is swept

| Factor | Levels |
|---|---|
| Representation | raw, **L2-normalised**, **whitened** |
| PCA components | 25, **50** (exp04's value), 100 |
| Scoring rule | 13 rules, below |

Rules, grouped by what they assume:

| Family | Rules | Assumption |
|---|---|---|
| prototype | `euclidean`, `cosine`, `ratio`, `mahalanobis` | one blob per driver |
| **neighbour** | `knn1`, `knn5`, `knn10` | none — local support only |
| **local density** | `lof` | density relative to local neighbours |
| **global density** | `gmm`, `global_mahalanobis` | knowns form one distribution |
| **boundary** | `isolation_forest`, `ocsvm` | a learned enclosing region |
| classifier | `msp`, `entropy` | a trained classifier's confidence |

`euclidean` through `msp` reproduce exp04 exactly, so the sweep contains its own
control: if those come out at ~0.51 again, the pipeline agrees with exp04 and
any rule that beats them is a genuine improvement rather than a coding
difference.

## Scope of this run

Reads whatever fine-tuned embeddings exist. Phase A's files are **one partition
fitted on inner-train**, so results from those are a **preview** used to decide
whether any rule escapes the ceiling before Phase B's GPU time is spent. Once
Phase B finishes, the same script runs over its five partitions and those
numbers are reportable.

Everything the knowns need — scaler, PCA, prototypes, covariance, density
models, classifiers — is fitted on **known-train windows only**. Unknown drivers
appear once, at scoring.

## Commands

```bash
# preview on Phase A's single-partition embeddings
python -u -m experiments.exp07_full_window.phase_c --preview

# the real thing, once Phase B has written its partitions
python -u -m experiments.exp07_full_window.phase_c
```
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
from sklearn.covariance import EmpiricalCovariance
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from src.config import DATA_INTERIM
from src.models.finetune import OUTPUT_TOKEN
from src.models.open_set import N_PARTITIONS, N_UNKNOWN, SEED
from src.models.splits import known_unknown_partitions, split_by_driver

PCA_LEVELS = (25, 50, 100)
TRANSFORMS = ("raw", "l2norm", "whiten")
RESULTS_PATH = Path(__file__).parent / "phase_c.md"
PREVIEW_PATH = Path(__file__).parent / "phase_c_preview.md"

PROTOTYPE_RULES = ("euclidean", "cosine", "ratio", "mahalanobis")
NEIGHBOUR_RULES = ("knn1", "knn5", "knn10")
DENSITY_RULES = ("gmm", "global_mahalanobis")
BOUNDARY_RULES = ("isolation_forest", "ocsvm")
CLASSIFIER_RULES = ("msp", "entropy")
ALL_RULES = (PROTOTYPE_RULES + NEIGHBOUR_RULES + ("lof",) + DENSITY_RULES
             + BOUNDARY_RULES + CLASSIFIER_RULES)


def apply_transform(train: np.ndarray, every: np.ndarray, name: str
                    ) -> tuple[np.ndarray, np.ndarray]:
    """Apply a representation transform, fitted on training rows only.

    Args:
        train: known-train rows, already PCA-reduced.
        every: all rows, already PCA-reduced.
        name: 'raw', 'l2norm' or 'whiten'.

    Returns:
        (transformed train rows, transformed all rows).
    """
    if name == "l2norm":
        unit = lambda a: a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
        return unit(train), unit(every)
    if name == "whiten":
        whitener = PCA(n_components=train.shape[1], whiten=True,
                       random_state=SEED).fit(train)
        return whitener.transform(train), whitener.transform(every)
    return train, every


def prototypes_of(features: np.ndarray, drivers: np.ndarray
                  ) -> tuple[np.ndarray, np.ndarray]:
    """Per-driver mean embedding.

    Args:
        features: training rows.
        drivers: driver id per row.

    Returns:
        (sorted driver ids, prototype per driver).
    """
    labels = np.unique(drivers)
    return labels, np.stack([features[drivers == d].mean(axis=0)
                             for d in labels])


def all_scores(train: np.ndarray, train_drivers: np.ndarray,
               query: np.ndarray) -> dict[str, np.ndarray]:
    """Every rejection score for a set of query rows, higher meaning stranger.

    Every model is fitted on `train` only.

    Args:
        train: known-train rows.
        train_drivers: driver id per training row.
        query: rows to score.

    Returns:
        {rule name: score per query row}.
    """
    out: dict[str, np.ndarray] = {}
    labels, protos = prototypes_of(train, train_drivers)

    distances = np.linalg.norm(query[:, None, :] - protos[None, :, :], axis=2)
    nearest = np.sort(distances, axis=1)
    out["euclidean"] = nearest[:, 0]
    out["ratio"] = nearest[:, 0] / (nearest[:, 1] + 1e-9)

    unit_q = query / (np.linalg.norm(query, axis=1, keepdims=True) + 1e-9)
    unit_p = protos / (np.linalg.norm(protos, axis=1, keepdims=True) + 1e-9)
    out["cosine"] = 1.0 - (unit_q @ unit_p.T).max(axis=1)

    residuals = train - protos[np.searchsorted(labels, train_drivers)]
    precision = np.linalg.inv(np.cov(residuals, rowvar=False)
                              + np.eye(train.shape[1]) * 1e-3)
    delta = query[:, None, :] - protos[None, :, :]
    out["mahalanobis"] = np.sqrt(
        np.einsum("nkd,de,nke->nk", delta, precision, delta)).min(axis=1)

    neighbours = NearestNeighbors(n_neighbors=10).fit(train)
    knn_distance, _ = neighbours.kneighbors(query)
    out["knn1"] = knn_distance[:, 0]
    out["knn5"] = knn_distance[:, :5].mean(axis=1)
    out["knn10"] = knn_distance.mean(axis=1)

    lof = LocalOutlierFactor(n_neighbors=20, novelty=True).fit(train)
    out["lof"] = -lof.score_samples(query)

    components = min(8, max(1, len(train) // 50))
    gmm = GaussianMixture(n_components=components, covariance_type="diag",
                          random_state=SEED, reg_covar=1e-4).fit(train)
    out["gmm"] = -gmm.score_samples(query)

    global_cov = EmpiricalCovariance().fit(train)
    out["global_mahalanobis"] = global_cov.mahalanobis(query)

    forest = IsolationForest(n_estimators=300, random_state=SEED,
                             n_jobs=-1).fit(train)
    out["isolation_forest"] = -forest.score_samples(query)

    svm = OneClassSVM(kernel="rbf", gamma="scale", nu=0.1).fit(train)
    out["ocsvm"] = -svm.decision_function(query)

    classifier = RandomForestClassifier(n_estimators=300, random_state=SEED,
                                        n_jobs=-1).fit(train, train_drivers)
    proba = classifier.predict_proba(query)
    out["msp"] = 1.0 - proba.max(axis=1)
    out["entropy"] = -(proba * np.log(proba + 1e-12)).sum(axis=1)
    return out


def evaluate(features: np.ndarray, drivers: np.ndarray, starts: np.ndarray,
             known: np.ndarray, unknown: np.ndarray, components: int,
             transform: str) -> dict[str, tuple[float, float]]:
    """Score one partition under one representation setting.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        starts: window start time per window.
        known: enrolled driver ids.
        unknown: never-enrolled driver ids.
        components: PCA components.
        transform: representation transform name.

    Returns:
        {rule: (window AUROC, driver AUROC)}.
    """
    known_positions = np.flatnonzero(np.isin(drivers, known))
    train_local, test_local = split_by_driver(drivers[known_positions],
                                              starts[known_positions])
    train_index = known_positions[train_local]
    test_index = known_positions[test_local]
    unknown_positions = np.flatnonzero(np.isin(drivers, unknown))
    _, unknown_local = split_by_driver(drivers[unknown_positions],
                                       starts[unknown_positions])
    unknown_index = unknown_positions[unknown_local]

    scaler = StandardScaler().fit(features[train_index])
    scaled = scaler.transform(features)
    reducer = PCA(n_components=min(components, len(train_index) - 1,
                                   scaled.shape[1]),
                  random_state=SEED).fit(scaled[train_index])
    reduced = reducer.transform(scaled)
    train, every = apply_transform(reduced[train_index], reduced, transform)

    known_scores = all_scores(train, drivers[train_index], every[test_index])
    unknown_scores = all_scores(train, drivers[train_index],
                                every[unknown_index])

    membership = np.r_[np.zeros(len(test_index)), np.ones(len(unknown_index))]
    truth, unknown_truth = drivers[test_index], drivers[unknown_index]
    out = {}
    for rule in ALL_RULES:
        window = float(roc_auc_score(
            membership, np.r_[known_scores[rule], unknown_scores[rule]]))
        values, memberships = [], []
        for driver in np.unique(truth):
            values.append(np.median(known_scores[rule][truth == driver]))
            memberships.append(0)
        for driver in np.unique(unknown_truth):
            values.append(np.median(
                unknown_scores[rule][unknown_truth == driver]))
            memberships.append(1)
        out[rule] = (window, float(roc_auc_score(memberships, values)))
    return out


def write_report(cells: dict, path: Path, preview: bool, n_part: int) -> None:
    """Write the sweep report.

    Args:
        cells: {(components, transform, rule): (mean window, mean driver)}.
        path: where to write.
        preview: whether these are single-partition preview numbers.
        n_part: how many partitions contributed.
    """
    families = [("prototype (exp04 used only these)", PROTOTYPE_RULES),
                ("neighbour", NEIGHBOUR_RULES), ("local density", ("lof",)),
                ("global density", DENSITY_RULES), ("boundary", BOUNDARY_RULES),
                ("classifier", CLASSIFIER_RULES)]
    best = max(cells, key=lambda k: cells[k][1])
    lines = [
        "# exp07 Phase C — exhaustive open-set scoring sweep",
        "",
        ("**PREVIEW — one partition, encoder fitted on inner-train.** "
         "Used to decide whether any rule escapes the ~0.51 ceiling before "
         "spending GPU time. Not reportable."
         if preview else
         f"**{n_part} partitions**, `full` + `{OUTPUT_TOKEN}`, 30 s windows. "
         "Everything is fitted on known-train only; unknown drivers appear "
         "once, at scoring."),
        "",
        "AUROC, **0.500 is chance**. exp04 reached **0.514** using prototype "
        "rules only. Driver-level takes the median score per driver.",
        "",
        f"**Best cell: `{best[2]}`, PCA {best[0]}, {best[1]} — "
        f"driver AUROC {cells[best][1]:.3f}** (window {cells[best][0]:.3f}).",
        "",
    ]
    for components in PCA_LEVELS:
        lines += [f"## PCA {components}", "",
                  "| Rule | " + " | ".join(f"{t} window / driver"
                                           for t in TRANSFORMS) + " |",
                  "|---|" + "--:|" * len(TRANSFORMS)]
        for family, rules in families:
            lines.append(f"| *{family}* |" + " |" * len(TRANSFORMS))
            for rule in rules:
                cell_texts = []
                for transform in TRANSFORMS:
                    key = (components, transform, rule)
                    if key in cells:
                        window, driver = cells[key]
                        mark = "**" if driver >= 0.60 else ""
                        cell_texts.append(
                            f"{window:.3f} / {mark}{driver:.3f}{mark}")
                    else:
                        cell_texts.append("—")
                lines.append(f"| `{rule}` | " + " | ".join(cell_texts) + " |")
        lines.append("")

    lines += [
        "## How to read this",
        "",
        "- **The prototype family is exp04's control.** If those land near "
        "0.51 again, this pipeline agrees with exp04 and anything above is a "
        "real gain rather than a coding difference.",
        "- **Driver-level is the deployment question** — a decision is taken "
        "per driver, not per 30-second window.",
        "- Bold marks driver AUROC >= 0.60, the threshold `exp04/STAGE2.md` "
        "pre-registered as 'real but weak signal'.",
        "- This is a **maximum over many cells**, so the best value is "
        "optimistically biased. Any rule chosen here must be re-stated on the "
        "remaining partitions before it is reported as a result.",
        "",
        "## Limitations",
        "",
        "- One drive per driver: an unknown driver is also an unknown day, so "
        "any positive AUROC conflates 'new person' with 'new conditions'. "
        "See `DECISIONS.md` C1.",
        "- `ocsvm` and `lof` have hyperparameters (`nu`, `n_neighbors`) left at "
        "sensible defaults rather than swept.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Run the sweep over whichever embeddings are available."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    arguments = parser.parse_args()
    warnings.filterwarnings("ignore")

    if arguments.preview:
        path = DATA_INTERIM / f"embeddings_full_{OUTPUT_TOKEN}_30s.npz"
        cached = np.load(path, allow_pickle=True)
        drivers = cached["driver"]
        known, unknown = known_unknown_partitions(
            drivers, n_unknown=N_UNKNOWN, n_partitions=N_PARTITIONS,
            seed=SEED)[0]
        sources = [(cached, known, unknown)]
        print(f"preview: {path.name} | {cached['E'].shape}")
    else:
        sources = []
        for index in range(1, N_PARTITIONS + 1):
            path = (DATA_INTERIM / f"embeddings_phaseB_{OUTPUT_TOKEN}_30s_"
                                   f"p{index}.npz")
            if path.exists():
                cached = np.load(path, allow_pickle=True)
                sources.append((cached, cached["known"], cached["unknown"]))
        print(f"{len(sources)} Phase B partition(s) found")

    accumulated: dict[tuple, list[tuple[float, float]]] = {}
    for components in PCA_LEVELS:
        for transform in TRANSFORMS:
            for cached, known, unknown in sources:
                scores = evaluate(cached["E"], cached["driver"],
                                  cached["start_time"], known, unknown,
                                  components, transform)
                for rule, value in scores.items():
                    accumulated.setdefault((components, transform, rule),
                                           []).append(value)
            top = max(ALL_RULES,
                      key=lambda r: np.mean([v[1] for v in accumulated[
                          (components, transform, r)]]))
            best_driver = np.mean([v[1] for v in accumulated[
                (components, transform, top)]])
            print(f"  PCA {components:>3d} | {transform:7s} | "
                  f"best {top:18s} driver AUROC {best_driver:.3f}")

    cells = {key: (float(np.mean([v[0] for v in values])),
                   float(np.mean([v[1] for v in values])))
             for key, values in accumulated.items()}
    path = PREVIEW_PATH if arguments.preview else RESULTS_PATH
    write_report(cells, path, arguments.preview, len(sources))
    best = max(cells, key=lambda k: cells[k][1])
    print(f"\nbest: {best[2]} | PCA {best[0]} | {best[1]} | "
          f"driver AUROC {cells[best][1]:.3f} (window {cells[best][0]:.3f})")
    print(f"results -> {path}")


if __name__ == "__main__":
    main()
