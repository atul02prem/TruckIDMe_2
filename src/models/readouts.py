"""Closed-set read-outs: name which enrolled driver a window belongs to.

Three read-outs on the same representation, fitted on the enrolled drivers'
training windows and scored on their test windows:

| Read-out | What it assumes |
|---|---|
| `linear_probe` | the standard protocol for evaluating a learned representation |
| `lda_centroid` | PCA, then LDA, then nearest driver mean: a supervised metric |
| `random_forest` | no metric at all |

A large spread between them means a weak number came from the read-out rather
than the representation. Moved here unchanged from exp04's `run.py` so that
experiments import the read-outs from one library instead of from exp04.
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.models.open_set import SEED
from src.models.splits import split_by_driver

HEADS: tuple[str, ...] = ("linear_probe", "lda_centroid", "random_forest")
HEAD_KS: tuple[int, ...] = (1, 2)

# For LDA only. A 12,800-dimensional scatter matrix is not formable, so the
# supervised projection is preceded by an unsupervised one; 200 components keep
# far more than the 50 that `evaluate_partition` uses for distances, while
# staying below the training-window count.
LDA_PCA_COMPONENTS = 200

# The linear probe is the standard read-out for a learned representation, so it
# must be allowed to converge rather than be cut off by an iteration cap.
PROBE_MAX_ITER = 10000


def rank_accuracy(scores: np.ndarray, classes: np.ndarray, truth: np.ndarray,
                  ks: tuple[int, ...]) -> dict[int, float]:
    """Top-k accuracy from a higher-is-better score matrix.

    Args:
        scores: (n_queries, n_classes), larger means more likely.
        classes: class labels aligned with the score columns.
        truth: true label per query.
        ks: the k values to report.

    Returns:
        {k: accuracy}.
    """
    ranking = classes[np.argsort(-scores, axis=1)]
    return {k: float(np.mean([t in row[:k] for t, row in zip(truth, ranking)]))
            for k in ks}


def closed_set_heads(features: np.ndarray, drivers: np.ndarray,
                     starts: np.ndarray, known: np.ndarray
                     ) -> dict[str, dict[int, float]]:
    """Score one representation three ways on one partition's known drivers.

    Separates "is the representation weak" from "is Euclidean distance in 12,800
    dimensions weak", which a PCA sweep cannot do.

    Args:
        features: all window features.
        drivers: driver id per window.
        starts: window start time per window.
        known: driver ids treated as enrolled.

    Returns:
        {head name: {k: accuracy}}.
    """
    positions = np.flatnonzero(np.isin(drivers, known))
    train_local, test_local = split_by_driver(drivers[positions], starts[positions])
    train_index, test_index = positions[train_local], positions[test_local]

    scaler = StandardScaler().fit(features[train_index])      # known-train only
    train_x = scaler.transform(features[train_index])
    test_x = scaler.transform(features[test_index])
    train_y, test_y = drivers[train_index], drivers[test_index]

    out: dict[str, dict[int, float]] = {}

    # 12,800 features and 36 classes is 460k coefficients fitted on ~870 samples,
    # so lbfgs needs a generous iteration budget; a probe that stopped early
    # would understate the representation it is meant to measure.
    probe = LogisticRegression(max_iter=PROBE_MAX_ITER).fit(train_x, train_y)
    out["linear_probe"] = rank_accuracy(probe.predict_proba(test_x),
                                        probe.classes_, test_y, HEAD_KS)

    forest = RandomForestClassifier(n_estimators=500, random_state=SEED,
                                    n_jobs=-1).fit(train_x, train_y)
    out["random_forest"] = rank_accuracy(forest.predict_proba(test_x),
                                         forest.classes_, test_y, HEAD_KS)

    compact = PCA(n_components=min(LDA_PCA_COMPONENTS, train_x.shape[0] - 1,
                                   train_x.shape[1]),
                  random_state=SEED).fit(train_x)
    lda = LinearDiscriminantAnalysis().fit(compact.transform(train_x), train_y)
    train_z = lda.transform(compact.transform(train_x))
    test_z = lda.transform(compact.transform(test_x))
    labels = np.unique(train_y)
    centroids = np.stack([train_z[train_y == label].mean(axis=0)
                          for label in labels])
    distances = np.linalg.norm(test_z[:, None, :] - centroids[None, :, :], axis=2)
    out["lda_centroid"] = rank_accuracy(-distances, labels, test_y, HEAD_KS)

    return out


def average_heads(rows: list[dict[str, dict[int, float]]]
                  ) -> dict[str, dict[int, tuple[float, float]]]:
    """Mean and standard deviation of each head's accuracy across partitions.

    Args:
        rows: one `closed_set_heads` result per partition.

    Returns:
        {head name: {k: (mean, std)}}.
    """
    return {head: {k: (float(np.mean([row[head][k] for row in rows])),
                       float(np.std([row[head][k] for row in rows])))
                   for k in HEAD_KS}
            for head in rows[0]}
