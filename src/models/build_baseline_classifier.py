"""Baseline driver-ID classifier — Random Forest on the per-(driver, sector) feature matrix.

Loads data/processed_data/feature_matrix.csv, runs 5-fold cross-validation
stratified on driver, trains Random Forest, reports accuracy + per-driver F1
+ confusion matrix + top feature importances.

Outputs:
  - outputs/reports/baseline_rf_results.md   (accuracy table, feature importances)
  - outputs/figures/baseline_rf_confusion_matrix.png

Run from project root:
    python -m src.models.build_baseline_classifier
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    top_k_accuracy_score,
)
from sklearn.model_selection import StratifiedKFold

from src.config import DATA_PROCESSED, OUT_FIGURES, OUT_REPORTS


FEATURE_MATRIX_FILE = "feature_matrix.csv"
N_FOLDS             = 5
SEED                = 42
N_ESTIMATORS        = 300
TOP_K_FEATURES      = 20
TOP_KS              = (1, 2, 3, 5)   # top-k accuracies to report

META_COLS = {"driver", "group", "sector_id", "window_id", "n_rows"}


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Separate the (CAN-only) feature columns from the target driver column.

    Args:
        df: feature matrix DataFrame from build_feature_matrix.py.

    Returns:
        (X, y, feature_names): the n_rows x n_features array, the target
        driver labels, and the list of feature column names.
    """
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X = df[feature_cols].to_numpy(dtype=float)
    y = df["driver"].to_numpy()
    return X, y, feature_cols


def run_stratified_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: int,
    seed: int,
    n_estimators: int,
) -> dict:
    """Run stratified-on-driver K-fold cross-validation with Random Forest.

    Args:
        X: feature matrix.
        y: target driver labels.
        n_folds: number of CV folds.
        seed: random state for reproducibility.
        n_estimators: number of trees per forest.

    Returns:
        Dict with per-fold accuracies, accumulated y_true / y_pred across
        folds (out-of-fold predictions), and the mean feature importances.
    """
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    fold_accs = []
    topk_accs: dict[int, list] = {k: [] for k in TOP_KS}
    y_true_all, y_pred_all = [], []
    importances_per_fold = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_te, y_te = X[test_idx],  y[test_idx]

        # Median imputation on training set, applied to test
        imp = SimpleImputer(strategy="median")
        X_tr_imp = imp.fit_transform(X_tr)
        X_te_imp = imp.transform(X_te)

        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=seed,
            n_jobs=-1,
        )
        clf.fit(X_tr_imp, y_tr)
        y_pred = clf.predict(X_te_imp)
        y_proba = clf.predict_proba(X_te_imp)

        acc = accuracy_score(y_te, y_pred)
        fold_accs.append(acc)
        for k in TOP_KS:
            topk_accs[k].append(
                top_k_accuracy_score(y_te, y_proba, k=k, labels=clf.classes_)
            )
        y_true_all.extend(y_te)
        y_pred_all.extend(y_pred)
        importances_per_fold.append(clf.feature_importances_)

        print(
            f"  Fold {fold}/{n_folds}: "
            f"train={len(train_idx)} test={len(test_idx)}  "
            f"top1={acc:.4f}  top2={topk_accs[2][-1]:.4f}"
        )

    return {
        "fold_accs":          np.array(fold_accs),
        "topk_accs":          {k: np.array(v) for k, v in topk_accs.items()},
        "y_true":             np.array(y_true_all),
        "y_pred":             np.array(y_pred_all),
        "mean_importances":   np.mean(importances_per_fold, axis=0),
    }


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    drivers: list[str],
    out_path: Path,
) -> None:
    """Save the driver-level confusion matrix as a heatmap PNG."""
    cm = confusion_matrix(y_true, y_pred, labels=drivers)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)

    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(drivers)))
    ax.set_yticks(range(len(drivers)))
    ax.set_xticklabels(drivers, rotation=90, fontsize=7)
    ax.set_yticklabels(drivers, fontsize=7)
    ax.set_xlabel("Predicted driver")
    ax.set_ylabel("True driver")
    ax.set_title("Baseline RF — confusion matrix (row-normalized)")
    plt.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def save_report(
    cv_results: dict,
    feature_names: list[str],
    drivers: list[str],
    out_path: Path,
) -> None:
    """Save the baseline-RF results as a markdown report."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fold_accs = cv_results["fold_accs"]
    y_true    = cv_results["y_true"]
    y_pred    = cv_results["y_pred"]

    per_driver_report = classification_report(
        y_true, y_pred, labels=drivers, output_dict=True, zero_division=0,
    )

    lines = [
        "# TruckIDMe — Baseline Random Forest Classifier",
        "",
        f"**Cross-validation:** {len(fold_accs)}-fold, stratified on driver",
        f"**Trees per forest:** {N_ESTIMATORS}",
        f"**Random seed:** {SEED}",
        f"**Features:** {len(feature_names)} CAN-signal aggregates "
        "(mean, median, std, min, max, p10, p90, dmean, dstd)",
        f"**Drivers:** {len(drivers)}",
        "",
        "## Overall accuracy",
        "",
        f"- Per-fold top-1: {', '.join(f'{a:.4f}' for a in fold_accs)}",
        f"- Mean top-1: **{fold_accs.mean():.4f} ± {fold_accs.std():.4f}**",
        f"- Out-of-fold overall top-1: **{accuracy_score(y_true, y_pred):.4f}**",
        "",
        "## Top-k accuracy (mean across folds)",
        "",
        "| k | Accuracy | ± std |",
        "|---:|---:|---:|",
        *[f"| {k} | {cv_results['topk_accs'][k].mean():.4f} | "
          f"{cv_results['topk_accs'][k].std():.4f} |" for k in TOP_KS],
        "",
        "## Per-driver F1 (out-of-fold)",
        "",
        "| Driver | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for d in drivers:
        row = per_driver_report.get(d, {})
        lines.append(
            f"| `{d}` | {row.get('precision', 0):.3f} | "
            f"{row.get('recall', 0):.3f} | "
            f"{row.get('f1-score', 0):.3f} | "
            f"{int(row.get('support', 0))} |"
        )

    lines += [
        "",
        "## Per-group breakdown",
        "",
        "| Group | n drivers | Mean per-driver F1 |",
        "|---|---:|---:|",
    ]
    for group in ["G1", "G2", "G3"]:
        members = [d for d in drivers if d.startswith(group)]
        f1s = [per_driver_report.get(d, {}).get("f1-score", 0) for d in members]
        lines.append(f"| {group} | {len(members)} | {np.mean(f1s):.4f} |")

    lines += [
        "",
        f"## Top {TOP_K_FEATURES} features by RF importance (mean across folds)",
        "",
        "| Rank | Feature | Importance |",
        "|---|---|---:|",
    ]
    importances = cv_results["mean_importances"]
    top_idx = np.argsort(importances)[::-1][:TOP_K_FEATURES]
    for rank, idx in enumerate(top_idx, start=1):
        lines.append(
            f"| {rank} | `{feature_names[idx]}` | {importances[idx]:.5f} |"
        )

    out_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    df = pd.read_csv(DATA_PROCESSED / FEATURE_MATRIX_FILE)
    X, y, feature_names = prepare_features(df)
    drivers = sorted(set(y))

    print(f"Feature matrix shape: {X.shape}")
    print(f"Drivers: {len(drivers)}")
    print(f"Total rows per group: "
          f"{df.groupby('group').size().to_dict()}")
    print()
    print("Running 5-fold stratified cross-validation...")

    cv_results = run_stratified_cv(
        X, y,
        n_folds=N_FOLDS,
        seed=SEED,
        n_estimators=N_ESTIMATORS,
    )

    print()
    print(f"Mean top-1 accuracy: {cv_results['fold_accs'].mean():.4f} "
          f"± {cv_results['fold_accs'].std():.4f}")
    for k in TOP_KS:
        print(f"  top-{k}: {cv_results['topk_accs'][k].mean():.4f} "
              f"± {cv_results['topk_accs'][k].std():.4f}")

    report_path = OUT_REPORTS  / "baseline_rf_results.md"
    save_report(cv_results, feature_names, drivers, report_path)
    print(f"\nReport written to {report_path}")

    cm_path = OUT_FIGURES / "baseline_rf_confusion_matrix.png"
    plot_confusion_matrix(cv_results["y_true"], cv_results["y_pred"], drivers, cm_path)
    print(f"Confusion matrix written to {cm_path}")
