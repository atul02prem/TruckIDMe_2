"""Open-set scoring: the protocol, the pre-registered scoring, and the earlier rules.

Shared by every experiment that asks whether a driver who was never enrolled can be
refused. Moved here from `src/models/enroll_and_score.py` and exp07's
`phase_c_sweep.py` / `phase_c_final.py`, unchanged, so that experiments import the
scoring from one library instead of from each other.

## The protocol

Each of `N_PARTITIONS` partitions holds out `N_UNKNOWN` drivers as strangers,
stratified by awareness group (`splits.known_unknown_partitions`, seeds `SEED`
onward). The other drivers are enrolled from the first 70% of their windows; the
last 25% of every driver's windows, enrolled or not, is scored.

## The current scoring (DECISIONS.md D12)

`PRE_REGISTERED`: standardise -> LDA projection -> L2-normalise -> whiten -> one
mean prototype per driver -> cosine distance to the nearest prototype. Chosen on
inner validation from the 1,300 configurations the building blocks below can
express, by the median across configurations, and fixed before any test window
was scored. `score_config` applies a configuration to one partition's test split.

## The earlier rules (superseded by D12)

`evaluate_partition` and `summarise`: PCA(50) followed by five distance rules.
They produced the near-chance open-set results of exp04 and are kept so those
results stay reproducible.
"""
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.covariance import EmpiricalCovariance
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import pairwise_distances, roc_auc_score
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from src.models.splits import split_by_driver

# --- The protocol ----------------------------------------------------------

N_UNKNOWN = 10
N_PARTITIONS = 5
SEED = 42

# --- Building blocks of the current scoring (exp07 Phase C) --------------------

PCA_LEVELS = (5, 10, 15, 20, 25, 35, 50, 75, 100)
PROJECTIONS = tuple(f"pca{n}" for n in PCA_LEVELS) + ("lda",)
TRANSFORMS = ("raw", "l2norm", "whiten", "l2norm_whiten", "whiten_l2norm")
PROTOTYPES = ("mean", "median", "kmeans2", "kmeans3")
PROTOTYPE_RULES = ("euclidean", "cosine", "ratio", "mahalanobis")
OTHER_RULES = ("knn1", "knn5", "knn10", "lof", "gmm", "global_mahalanobis",
               "isolation_forest", "ocsvm", "msp", "entropy")


def unit(a: np.ndarray) -> np.ndarray:
    """Scale rows to unit L2 norm.

    Args:
        a: (n, d) array.

    Returns:
        Row-normalised copy.
    """
    return a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)


def project(train: np.ndarray, every: np.ndarray, labels: np.ndarray,
            name: str) -> tuple[np.ndarray, np.ndarray]:
    """Reduce dimensionality, fitting on training rows only.

    Args:
        train: known inner-train rows, standardised.
        every: all rows, standardised.
        labels: driver id per training row, for the supervised projection.
        name: 'pca<N>' or 'lda'.

    Returns:
        (projected train rows, projected all rows).
    """
    if name == "lda":
        model = LinearDiscriminantAnalysis(
            n_components=min(len(np.unique(labels)) - 1, train.shape[1]))
        model.fit(train, labels)
    else:
        model = PCA(n_components=min(int(name[3:]), len(train) - 1,
                                     train.shape[1]),
                    random_state=SEED).fit(train)
    return model.transform(train), model.transform(every)


def transform_rows(train: np.ndarray, every: np.ndarray, name: str
                   ) -> tuple[np.ndarray, np.ndarray]:
    """Apply a representation transform, fitted on training rows only.

    Args:
        train: projected training rows.
        every: projected rows for everything.
        name: one of TRANSFORMS.

    Returns:
        (transformed train, transformed all).
    """
    if name == "raw":
        return train, every
    if name == "l2norm":
        return unit(train), unit(every)
    whitener = lambda tr, ev: (
        lambda w: (w.transform(tr), w.transform(ev)))(
        PCA(n_components=tr.shape[1], whiten=True, random_state=SEED).fit(tr))
    if name == "whiten":
        return whitener(train, every)
    if name == "l2norm_whiten":
        return whitener(unit(train), unit(every))
    white_train, white_every = whitener(train, every)
    return unit(white_train), unit(white_every)


def build_prototypes(train: np.ndarray, drivers: np.ndarray, kind: str
                     ) -> tuple[np.ndarray, list[np.ndarray]]:
    """One or more reference points per driver.

    Args:
        train: training rows.
        drivers: driver id per training row.
        kind: 'mean', 'median', 'kmeans2' or 'kmeans3'.

    Returns:
        (sorted driver ids, per-driver array of prototypes).
    """
    labels = np.unique(drivers)
    out = []
    for driver in labels:
        rows = train[drivers == driver]
        if kind == "mean":
            out.append(rows.mean(axis=0, keepdims=True))
        elif kind == "median":
            out.append(np.median(rows, axis=0, keepdims=True))
        else:
            k = min(int(kind[-1]), len(rows))
            out.append(KMeans(n_clusters=k, n_init=5,
                              random_state=SEED).fit(rows).cluster_centers_)
    return labels, out


def driver_distances(protos: list[np.ndarray], query: np.ndarray) -> np.ndarray:
    """Distance from each query row to each driver's nearest prototype.

    Args:
        protos: per-driver prototype arrays.
        query: rows to score.

    Returns:
        (n_queries, n_drivers) distances.
    """
    return np.stack([np.linalg.norm(query[:, None, :] - p[None, :, :],
                                    axis=2).min(axis=1) for p in protos],
                    axis=1)


def prototype_scores(train: np.ndarray, train_drivers: np.ndarray,
                     query: np.ndarray, kind: str) -> dict[str, np.ndarray]:
    """The four prototype-based rejection scores.

    Args:
        train: training rows.
        train_drivers: driver id per training row.
        query: rows to score.
        kind: prototype type.

    Returns:
        {rule: score per query row}, higher meaning stranger.
    """
    labels, protos = build_prototypes(train, train_drivers, kind)
    distances = driver_distances(protos, query)
    nearest = np.sort(distances, axis=1)

    stacked = np.vstack(protos)
    owner = np.concatenate([[i] * len(p) for i, p in enumerate(protos)])
    cosines = unit(query) @ unit(stacked).T
    per_driver = np.stack([cosines[:, owner == i].max(axis=1)
                           for i in range(len(labels))], axis=1)

    assigned = driver_distances(protos, train).argmin(axis=1)
    nearest_proto = np.stack([protos[a][np.linalg.norm(
        train[i] - protos[a], axis=1).argmin()]
        for i, a in enumerate(assigned)])
    residuals = train - nearest_proto
    precision = np.linalg.inv(np.cov(residuals, rowvar=False)
                              + np.eye(train.shape[1]) * 1e-3)
    delta = query[:, None, :] - stacked[None, :, :]
    maha = np.sqrt(np.einsum("nkd,de,nke->nk", delta, precision, delta))

    return {"euclidean": nearest[:, 0],
            "cosine": 1.0 - per_driver.max(axis=1),
            "ratio": nearest[:, 0] / (nearest[:, 1] + 1e-9),
            "mahalanobis": maha.min(axis=1)}


def other_scores(train: np.ndarray, train_drivers: np.ndarray,
                 query: np.ndarray) -> dict[str, np.ndarray]:
    """Rejection scores that do not use prototypes.

    Args:
        train: training rows.
        train_drivers: driver id per training row.
        query: rows to score.

    Returns:
        {rule: score per query row}, higher meaning stranger.
    """
    out: dict[str, np.ndarray] = {}
    knn = NearestNeighbors(n_neighbors=10).fit(train)
    distance, _ = knn.kneighbors(query)
    out["knn1"] = distance[:, 0]
    out["knn5"] = distance[:, :5].mean(axis=1)
    out["knn10"] = distance.mean(axis=1)
    out["lof"] = -LocalOutlierFactor(
        n_neighbors=20, novelty=True).fit(train).score_samples(query)
    out["gmm"] = -GaussianMixture(
        n_components=min(8, max(1, len(train) // 50)), covariance_type="diag",
        random_state=SEED, reg_covar=1e-4).fit(train).score_samples(query)
    out["global_mahalanobis"] = EmpiricalCovariance().fit(train).mahalanobis(
        query)
    out["isolation_forest"] = -IsolationForest(
        n_estimators=200, random_state=SEED, n_jobs=-1).fit(
        train).score_samples(query)
    out["ocsvm"] = -OneClassSVM(kernel="rbf", gamma="scale", nu=0.1).fit(
        train).decision_function(query)
    proba = RandomForestClassifier(n_estimators=200, random_state=SEED,
                                   n_jobs=-1).fit(
        train, train_drivers).predict_proba(query)
    out["msp"] = 1.0 - proba.max(axis=1)
    out["entropy"] = -(proba * np.log(proba + 1e-12)).sum(axis=1)
    return out


def inner_indices(drivers: np.ndarray, starts: np.ndarray, known: np.ndarray,
                  unknown: np.ndarray) -> tuple[np.ndarray, np.ndarray,
                                                np.ndarray]:
    """Inner-train, inner-val and matched unknown positions.

    The true test period is excluded for every driver, known and unknown, so
    nothing selected using these indices can bias a later test evaluation.

    Args:
        drivers: driver id per window.
        starts: window start time per window.
        known: enrolled driver ids.
        unknown: never-enrolled driver ids.

    Returns:
        (inner_train, inner_val, unknown_inner_val) positions.
    """
    known_positions = np.flatnonzero(np.isin(drivers, known))
    train_local, _ = split_by_driver(drivers[known_positions],
                                     starts[known_positions])
    known_train = known_positions[train_local]
    tr_local, val_local = split_by_driver(drivers[known_train],
                                          starts[known_train])

    unknown_positions = np.flatnonzero(np.isin(drivers, unknown))
    u_train_local, _ = split_by_driver(drivers[unknown_positions],
                                       starts[unknown_positions])
    unknown_train = unknown_positions[u_train_local]
    _, u_val_local = split_by_driver(drivers[unknown_train],
                                     starts[unknown_train])
    return (known_train[tr_local], known_train[val_local],
            unknown_train[u_val_local])


def auroc_pair(known: np.ndarray, unknown: np.ndarray,
               known_drivers: np.ndarray, unknown_drivers: np.ndarray
               ) -> tuple[float, float]:
    """Window-level and driver-level AUROC for one score.

    Args:
        known: scores for known-driver queries.
        unknown: scores for unknown-driver queries.
        known_drivers: driver id per known query.
        unknown_drivers: driver id per unknown query.

    Returns:
        (window AUROC, driver AUROC).
    """
    membership = np.r_[np.zeros(len(known)), np.ones(len(unknown))]
    window = float(roc_auc_score(membership, np.r_[known, unknown]))
    values, memberships = [], []
    for driver in np.unique(known_drivers):
        values.append(np.median(known[known_drivers == driver]))
        memberships.append(0)
    for driver in np.unique(unknown_drivers):
        values.append(np.median(unknown[unknown_drivers == driver]))
        memberships.append(1)
    return window, float(roc_auc_score(memberships, values))


# --- The pre-registered configuration and its test-split scoring (D12) -------

PRE_REGISTERED = ("lda", "l2norm_whiten", "mean", "cosine")


def test_indices(drivers: np.ndarray, starts: np.ndarray, known: np.ndarray,
                 unknown: np.ndarray) -> tuple[np.ndarray, np.ndarray,
                                               np.ndarray]:
    """Known-train, known-test and unknown-test positions.

    Args:
        drivers: driver id per window.
        starts: window start time per window.
        known: enrolled driver ids.
        unknown: never-enrolled driver ids.

    Returns:
        (train, known test, unknown test) positions.
    """
    known_positions = np.flatnonzero(np.isin(drivers, known))
    train_local, test_local = split_by_driver(drivers[known_positions],
                                              starts[known_positions])
    unknown_positions = np.flatnonzero(np.isin(drivers, unknown))
    _, unknown_local = split_by_driver(drivers[unknown_positions],
                                       starts[unknown_positions])
    return (known_positions[train_local], known_positions[test_local],
            unknown_positions[unknown_local])


def score_config(cached, config: tuple[str, str, str, str]
                 ) -> tuple[float, float]:
    """Evaluate one configuration on one partition's test split.

    Args:
        cached: loaded partition npz with E, driver, start_time, known, unknown.
        config: (projection, transform, prototype, rule).

    Returns:
        (window AUROC, driver AUROC).
    """
    projection, transform, prototype, rule = config
    features, drivers = cached["E"], cached["driver"]
    starts = cached["start_time"]
    train_index, known_index, unknown_index = test_indices(
        drivers, starts, cached["known"], cached["unknown"])

    scaler = StandardScaler().fit(features[train_index])
    scaled = scaler.transform(features)
    train_drivers = drivers[train_index]
    p_train, p_all = project(scaled[train_index], scaled, train_drivers,
                             projection)
    t_train, t_all = transform_rows(p_train, p_all, transform)

    if rule in PROTOTYPE_RULES:
        known_scores = prototype_scores(t_train, train_drivers,
                                        t_all[known_index], prototype)[rule]
        unknown_scores = prototype_scores(t_train, train_drivers,
                                          t_all[unknown_index],
                                          prototype)[rule]
    else:
        known_scores = other_scores(t_train, train_drivers,
                                    t_all[known_index])[rule]
        unknown_scores = other_scores(t_train, train_drivers,
                                      t_all[unknown_index])[rule]

    return auroc_pair(known_scores, unknown_scores, drivers[known_index],
                      drivers[unknown_index])


# --- The earlier rules, superseded by D12; exp04 was scored with these -------

CALIBRATION_PERCENTILE = 95
PCA_COMPONENTS = 50
SCORE_RULES = ("euclidean", "cosine", "ratio", "mahalanobis", "msp")


def prototypes_of(features: np.ndarray, drivers: np.ndarray
                  ) -> tuple[np.ndarray, np.ndarray]:
    """Mean feature vector per driver.

    Args:
        features: (n_windows, n_features) for enrollment windows.
        drivers: driver id per window.

    Returns:
        (labels, prototype_matrix) aligned row-wise.
    """
    labels = np.unique(drivers)
    return labels, np.stack([features[drivers == label].mean(axis=0)
                             for label in labels])


def distances_to(prototypes: np.ndarray, features: np.ndarray) -> np.ndarray:
    """Euclidean distance from every window to every prototype.

    Args:
        prototypes: (n_drivers, n_features).
        features: (n_windows, n_features).

    Returns:
        (n_windows, n_drivers) distance matrix.
    """
    return pairwise_distances(features, prototypes, n_jobs=-1)


def evaluate_partition(features: np.ndarray, drivers: np.ndarray, starts: np.ndarray,
                       known: np.ndarray, unknown: np.ndarray) -> dict:
    """Score one known/unknown partition.

    Args:
        features: all window features.
        drivers: driver id per window.
        starts: window start time per window.
        known: driver ids treated as enrolled.
        unknown: driver ids never enrolled.

    Returns:
        Closed-set accuracies, open-set AUROC, and threshold behaviour.
    """
    known_mask = np.isin(drivers, known)
    known_positions = np.flatnonzero(known_mask)
    train_local, test_local = split_by_driver(drivers[known_positions],
                                              starts[known_positions])
    train_index = known_positions[train_local]
    test_index = known_positions[test_local]

    # unknown drivers contribute their late windows, matching the query distribution
    unknown_positions = np.flatnonzero(np.isin(drivers, unknown))
    _, unknown_local = split_by_driver(drivers[unknown_positions],
                                       starts[unknown_positions])
    unknown_index = unknown_positions[unknown_local]

    scaler = StandardScaler().fit(features[train_index])      # known-train only
    scaled = scaler.transform(features)

    # PCA fitted on known-train only: 2048 raw dims with ~1.3k training windows
    # make every Euclidean distance nearly identical (the curse of dimensionality).
    reducer = PCA(n_components=min(PCA_COMPONENTS, scaled[train_index].shape[0],
                                   scaled.shape[1]),
                  random_state=SEED).fit(scaled[train_index])
    reduced = reducer.transform(scaled)

    labels, prototypes = prototypes_of(reduced[train_index], drivers[train_index])
    train_features = reduced[train_index]
    known_features = reduced[test_index]
    unknown_features = reduced[unknown_index]

    known_distances = distances_to(prototypes, known_features)
    ranking = labels[np.argsort(known_distances, axis=1)]
    truth = drivers[test_index]
    closed = {k: float(np.mean([t in row[:k] for t, row in zip(truth, ranking)]))
              for k in (1, 2, 5)}

    # a shared within-driver covariance, estimated from known-train residuals
    residuals = train_features - prototypes[
        np.searchsorted(labels, drivers[train_index])]
    covariance = np.cov(residuals, rowvar=False) + np.eye(residuals.shape[1]) * 1e-3
    precision = np.linalg.inv(covariance)

    # a classifier for the max-softmax-probability rule, trained on known drivers only
    forest = RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)
    forest.fit(train_features, drivers[train_index])

    def scores_for(features: np.ndarray) -> dict[str, np.ndarray]:
        """All five rejection scores for a set of query windows."""
        distances = distances_to(prototypes, features)
        nearest = np.sort(distances, axis=1)
        unit_f = features / (np.linalg.norm(features, axis=1, keepdims=True) + 1e-9)
        unit_p = prototypes / (np.linalg.norm(prototypes, axis=1, keepdims=True) + 1e-9)
        delta = features[:, None, :] - prototypes[None, :, :]
        mahalanobis = np.sqrt(np.einsum("nkd,de,nke->nk", delta, precision, delta))
        return {
            "euclidean": nearest[:, 0],
            "cosine": 1.0 - (unit_f @ unit_p.T).max(axis=1),
            "ratio": nearest[:, 0] / (nearest[:, 1] + 1e-9),
            "mahalanobis": mahalanobis.min(axis=1),
            "msp": 1.0 - forest.predict_proba(features).max(axis=1),
        }

    known_scores = scores_for(known_features)
    unknown_scores = scores_for(unknown_features)
    train_scores = scores_for(train_features)

    auroc, threshold, known_accept, unknown_accept, driver_auroc = {}, {}, {}, {}, {}
    membership = np.r_[np.zeros(len(known_features)), np.ones(len(unknown_features))]
    for rule in SCORE_RULES:
        auroc[rule] = float(roc_auc_score(
            membership, np.r_[known_scores[rule], unknown_scores[rule]]))
        threshold[rule] = float(np.percentile(train_scores[rule],
                                              CALIBRATION_PERCENTILE))
        known_accept[rule] = float((known_scores[rule] <= threshold[rule]).mean())
        unknown_accept[rule] = float((unknown_scores[rule] <= threshold[rule]).mean())

        # driver-level: one median score per driver
        values, memberships = [], []
        for driver in np.unique(truth):
            values.append(np.median(known_scores[rule][truth == driver]))
            memberships.append(0)
        unknown_truth = drivers[unknown_index]
        for driver in np.unique(unknown_truth):
            values.append(np.median(unknown_scores[rule][unknown_truth == driver]))
            memberships.append(1)
        driver_auroc[rule] = float(roc_auc_score(memberships, values))

    return {"closed": closed, "auroc": auroc, "driver_auroc": driver_auroc,
            "threshold": threshold, "known_accept": known_accept,
            "unknown_accept": unknown_accept, "known_score": known_scores,
            "unknown_score": unknown_scores, "n_known_test": len(test_index),
            "n_unknown_test": len(unknown_index)}


def summarise(rows: list[dict]) -> dict[str, tuple[float, float]]:
    """Mean and standard deviation of each scalar metric across partitions.

    Args:
        rows: per-partition result dicts.

    Returns:
        {metric: (mean, std)}.
    """
    out = {}
    for key in ("auroc", "driver_auroc", "known_accept", "unknown_accept"):
        for rule in SCORE_RULES:
            values = [row[key][rule] for row in rows]
            out[f"{key}:{rule}"] = (float(np.mean(values)), float(np.std(values)))
    for k in (1, 2, 5):
        values = [row["closed"][k] for row in rows]
        out[f"top{k}"] = (float(np.mean(values)), float(np.std(values)))
    return out
