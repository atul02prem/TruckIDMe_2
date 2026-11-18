"""Round 3 — group breakdown, operating points, and data efficiency (CPU).

Uses the current headline configuration: exp07 Phase B's fine-tuned embeddings
(layer 2, `mean_token`, 30 s, `np.interp`, five 36/10 partitions) and exp07's
pre-registered open-set scoring (LDA, `l2norm_whiten`, `mean`, `cosine`).
Nothing is retrained. A frozen encoder at the same settings is embedded once
for comparison and cached.

Three analyses:

**A. Awareness groups (G1 control, G2 aware, G3 aware + protocol).** Closed-set
top-1 per group, and open-set AUROC per group — enrolled drivers of a group
against strangers of the same group, pooled over partitions because each
partition holds only 3–4 strangers per group.

**B. Operating points.** AUROC says nothing about a usable threshold. This adds
equal error rate (EER), the share of strangers still accepted when 95% of
enrolled drivers are accepted, and AUPR, at window and driver level.

**C. Data efficiency (RQ4).** Read-outs and prototypes are rebuilt from the
earliest 25 / 50 / 75 / 100% of each enrolled driver's training windows; test
windows are unchanged. For the **frozen** encoder this is a clean answer. For
the **fine-tuned** encoder it is an optimistic upper bound, because the encoder
itself was trained on 100% of those windows — a clean fine-tuned curve needs
refits at each fraction.

Run:
    CUDA_VISIBLE_DEVICES=0 python -u -m experiments.exp08_layer_resampling.round3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler

from experiments.exp06_encoder_readout.run import embed_with_token
from src.config import DATA_INTERIM
from src.features.build_tensors import tensor_path
from src.models.open_set import (N_PARTITIONS, PRE_REGISTERED, project,
                                 prototype_scores, test_indices,
                                 transform_rows)
from src.models.splits import driver_group

WINDOW = 30.0
GROUPS = ("G1", "G2", "G3")
FRACTIONS = (0.25, 0.5, 0.75, 1.0)
LDA_PCA = 200
FROZEN_PATH = DATA_INTERIM / "embeddings_frozen_mean_token_30s.npz"
RESULTS_PATH = Path(__file__).parent / "round3.md"


def load_partitions() -> list:
    """Phase B's five saved partitions.

    Returns:
        Loaded npz archives with E, driver, start_time, known, unknown.
    """
    return [np.load(DATA_INTERIM / f"embeddings_phaseB_mean_token_30s_p{i}.npz",
                    allow_pickle=True) for i in range(1, N_PARTITIONS + 1)]


def frozen_features() -> np.ndarray:
    """Frozen layer-2 `mean_token` embeddings of the 30 s tensor, cached.

    Returns:
        (n_windows, 12800) array, row-aligned with Phase B's files.
    """
    if FROZEN_PATH.exists():
        return np.load(FROZEN_PATH)["E"]
    cached = np.load(tensor_path(WINDOW), allow_pickle=True)
    features, _ = embed_with_token(cached["X"], "mean_token", "cuda")
    np.savez_compressed(FROZEN_PATH, E=features)
    return features


def earliest_fraction(index: np.ndarray, drivers: np.ndarray,
                      starts: np.ndarray, fraction: float) -> np.ndarray:
    """Keep the earliest `fraction` of each driver's windows within `index`.

    Args:
        index: candidate window positions.
        drivers: driver id per window.
        starts: window start time per window.
        fraction: share of each driver's windows to keep.

    Returns:
        The kept positions.
    """
    kept = []
    for driver in np.unique(drivers[index]):
        own = index[drivers[index] == driver]
        own = own[np.argsort(starts[own])]
        kept.append(own[:max(2, int(round(fraction * len(own))))])
    return np.concatenate(kept)


def lda_predictions(features: np.ndarray, drivers: np.ndarray,
                    train: np.ndarray, test: np.ndarray) -> np.ndarray:
    """LDA + nearest-centroid predictions, as exp04's `lda_centroid` read-out.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        train: training positions.
        test: test positions.

    Returns:
        Predicted driver id per test window.
    """
    scaler = StandardScaler().fit(features[train])
    x_train, x_test = scaler.transform(features[train]), \
        scaler.transform(features[test])
    pca = PCA(n_components=min(LDA_PCA, len(train) - 1, x_train.shape[1]),
              random_state=0).fit(x_train)
    lda = LinearDiscriminantAnalysis().fit(pca.transform(x_train),
                                           drivers[train])
    z_train = lda.transform(pca.transform(x_train))
    z_test = lda.transform(pca.transform(x_test))
    labels = np.unique(drivers[train])
    centroids = np.stack([z_train[drivers[train] == d].mean(axis=0)
                          for d in labels])
    nearest = np.linalg.norm(z_test[:, None] - centroids[None], axis=2)
    return labels[nearest.argmin(axis=1)]


def open_scores(features: np.ndarray, drivers: np.ndarray, train: np.ndarray,
                query: np.ndarray) -> np.ndarray:
    """Pre-registered strangeness score for query windows.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        train: enrolled training positions.
        query: positions to score.

    Returns:
        Score per query window, higher meaning stranger.
    """
    projection, transform, prototype, rule = PRE_REGISTERED
    scaled = StandardScaler().fit(features[train]).transform(features)
    p_train, p_all = project(scaled[train], scaled, drivers[train], projection)
    t_train, t_all = transform_rows(p_train, p_all, transform)
    return prototype_scores(t_train, drivers[train], t_all[query],
                            prototype)[rule]


def driver_medians(scores: np.ndarray, ids: np.ndarray) -> tuple[np.ndarray,
                                                                 np.ndarray]:
    """Median score per driver.

    Args:
        scores: window scores.
        ids: driver id per window.

    Returns:
        (driver ids, median score per driver).
    """
    names = np.unique(ids)
    return names, np.array([np.median(scores[ids == d]) for d in names])


def operating_points(known: np.ndarray, unknown: np.ndarray) -> dict:
    """Threshold-level metrics, strangers as the positive class.

    Args:
        known: scores for enrolled drivers.
        unknown: scores for strangers.

    Returns:
        {'auroc', 'aupr', 'eer', 'stranger_accept_at_95'}.
    """
    y = np.r_[np.zeros(len(known)), np.ones(len(unknown))]
    s = np.r_[known, unknown]
    fpr, tpr, _ = roc_curve(y, s)
    eer_at = np.argmin(np.abs(fpr - (1 - tpr)))
    threshold = np.percentile(known, 95)
    return {"auroc": roc_auc_score(y, s), "aupr": average_precision_score(y, s),
            "eer": float((fpr[eer_at] + 1 - tpr[eer_at]) / 2),
            "stranger_accept_at_95": float((unknown <= threshold).mean())}


def main() -> None:
    """Run analyses A, B and C and write round3.md."""
    argparse.ArgumentParser().parse_args()
    warnings.filterwarnings("ignore")
    parts = load_partitions()
    drivers, starts = parts[0]["driver"], parts[0]["start_time"]
    frozen = frozen_features()
    arms = {"full": [p["E"] for p in parts], "frozen": [frozen] * len(parts)}
    print("loaded 5 partitions and frozen embeddings", flush=True)

    group_acc = {a: {g: [] for g in GROUPS} for a in arms}
    group_scores = {a: {g: ([], [], [], []) for g in GROUPS} for a in arms}
    ops = {a: {"window": [], "driver": []} for a in arms}
    curve = {a: {f: ([], []) for f in FRACTIONS} for a in arms}

    for i, part in enumerate(parts):
        known, unknown = part["known"], part["unknown"]
        train, test, stranger = test_indices(drivers, starts, known, unknown)
        for arm, per_part in arms.items():
            features = per_part[i]

            predicted = lda_predictions(features, drivers, train, test)
            for g in GROUPS:
                mask = np.array([driver_group(d) == g for d in drivers[test]])
                group_acc[arm][g].append(float(
                    (predicted[mask] == drivers[test][mask]).mean()))

            k_s = open_scores(features, drivers, train, test)
            u_s = open_scores(features, drivers, train, stranger)
            ops[arm]["window"].append(operating_points(k_s, u_s))
            k_names, k_med = driver_medians(k_s, drivers[test])
            u_names, u_med = driver_medians(u_s, drivers[stranger])
            ops[arm]["driver"].append(operating_points(k_med, u_med))
            for g in GROUPS:
                kg = np.array([driver_group(d) == g for d in drivers[test]])
                ug = np.array([driver_group(d) == g for d in drivers[stranger]])
                kd = np.array([driver_group(d) == g for d in k_names])
                ud = np.array([driver_group(d) == g for d in u_names])
                bucket = group_scores[arm][g]
                bucket[0].append(k_s[kg]); bucket[1].append(u_s[ug])
                bucket[2].append(k_med[kd]); bucket[3].append(u_med[ud])

            for fraction in FRACTIONS:
                reduced = earliest_fraction(train, drivers, starts, fraction)
                acc = float((lda_predictions(features, drivers, reduced, test)
                             == drivers[test]).mean())
                k_r = open_scores(features, drivers, reduced, test)
                u_r = open_scores(features, drivers, reduced, stranger)
                _, km = driver_medians(k_r, drivers[test])
                _, um = driver_medians(u_r, drivers[stranger])
                curve[arm][fraction][0].append(acc)
                curve[arm][fraction][1].append(roc_auc_score(
                    np.r_[np.zeros(len(km)), np.ones(len(um))], np.r_[km, um]))
        print(f"  partition {i + 1} done", flush=True)

    ms = lambda v: f"{np.mean(v):.3f} ± {np.std(v):.3f}"
    pct = lambda v: f"{100 * np.mean(v):.1f}% ± {100 * np.std(v):.1f}"
    lines = [
        "# exp08 Round 3 — groups, operating points, data efficiency",
        "",
        "Headline configuration: exp07 Phase B embeddings (layer 2, "
        "`mean_token`, 30 s, `np.interp`, `full`), five 36/10 partitions, "
        "test split, pre-registered open-set scoring. `frozen` is the same "
        "encoder never fine-tuned. Values are mean ± sd over partitions.",
        "",
        "## A. Awareness groups",
        "",
        "Closed-set top-1 (LDA + centroid, 36-way, chance 2.8%):",
        "",
        "| Group | `full` | `frozen` |", "|---|--:|--:|",
    ]
    for g in GROUPS:
        lines.append(f"| {g} | {pct(group_acc['full'][g])} | "
                     f"{pct(group_acc['frozen'][g])} |")
    lines += ["", "Open-set AUROC within each group (enrolled drivers of the "
              "group vs strangers of the same group), pooled over the five "
              "partitions because each holds only 3–4 strangers per group:", "",
              "| Group | `full` window | `full` driver | `frozen` window | "
              "`frozen` driver | strangers pooled |",
              "|---|--:|--:|--:|--:|--:|"]
    for g in GROUPS:
        cells = []
        for arm in ("full", "frozen"):
            kw, uw, kd, ud = (np.concatenate(x) for x in group_scores[arm][g])
            cells.append(roc_auc_score(np.r_[np.zeros(len(kw)), np.ones(len(uw))],
                                       np.r_[kw, uw]))
            cells.append(roc_auc_score(np.r_[np.zeros(len(kd)), np.ones(len(ud))],
                                       np.r_[kd, ud]))
        lines.append(f"| {g} | " + " | ".join(f"{c:.3f}" for c in cells)
                     + f" | {len(ud)} |")

    lines += ["", "## B. Operating points (strangers = positive class)", "",
              "| Arm | level | AUROC | AUPR | EER | strangers accepted when 95% "
              "of enrolled are accepted |", "|---|---|--:|--:|--:|--:|"]
    for arm in ("full", "frozen"):
        for level in ("window", "driver"):
            v = ops[arm][level]
            lines.append(
                f"| `{arm}` | {level} | {ms([x['auroc'] for x in v])} | "
                f"{ms([x['aupr'] for x in v])} | {ms([x['eer'] for x in v])} | "
                f"{pct([x['stranger_accept_at_95'] for x in v])} |")
    lines += ["", "AUPR's chance level is the stranger share: ~0.20 at window "
              "level, 10/46 ≈ 0.22 at driver level. EER's chance level is 0.50.",
              "", "## C. Data efficiency (RQ4)", "",
              "Read-outs and prototypes rebuilt from the earliest share of each "
              "enrolled driver's training windows; test windows unchanged. "
              "**`frozen` is the clean curve. `full` is an optimistic upper "
              "bound** — its encoder was fine-tuned on 100% of the windows.", "",
              "| Share of training windows | `frozen` top-1 | `frozen` driver "
              "AUROC | `full` top-1 | `full` driver AUROC |",
              "|--:|--:|--:|--:|--:|"]
    for f in FRACTIONS:
        lines.append(f"| {int(f * 100)}% | {pct(curve['frozen'][f][0])} | "
                     f"{ms(curve['frozen'][f][1])} | {pct(curve['full'][f][0])} "
                     f"| {ms(curve['full'][f][1])} |")
    lines += ["", "## Limitations", "",
              "- Group-level open-set numbers rest on 13–17 strangers pooled "
              "across partitions; treat differences between groups as "
              "indicative only.",
              "- The fine-tuned data-efficiency curve is an upper bound (see C).",
              "- One drive per driver; a stranger is also an unseen day. "
              "See `DECISIONS.md` C1."]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
