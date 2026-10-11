"""Sweep window length and plot driver-ID accuracy vs. window duration.

For each window length in DURATIONS, build a windowed feature matrix, run
5-fold stratified-on-driver cross-validation with Random Forest, and record
mean accuracy. Produces the feasibility curve: how much driving is needed to
identify a driver.

Outputs:
  - outputs/reports/window_sweep.md          (accuracy + example counts per duration)
  - outputs/figures/window_sweep_curve.png   (accuracy vs. window seconds)

Run from project root:
    python -m src.models.run_window_sweep
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score

from src.models.build_baseline_classifier import prepare_features, run_stratified_cv
from src.features.build_windowed_feature_matrix import build_windowed_feature_matrix
from src.config import DATA_INTERIM, EXCLUDE_DRIVERS, OUT_FIGURES, OUT_REPORTS


DURATIONS_S  = [30, 60, 90, 120, 180, 240, 300]
N_FOLDS      = 5
SEED         = 42
N_ESTIMATORS = 300


def main() -> None:
    results = []
    for win_s in DURATIONS_S:
        matrix = build_windowed_feature_matrix(DATA_INTERIM, EXCLUDE_DRIVERS, win_s)
        X, y, feature_names = prepare_features(matrix)
        n_examples = len(matrix)
        windows_per_driver = matrix.groupby("driver").size().median()

        cv = run_stratified_cv(X, y, n_folds=N_FOLDS, seed=SEED, n_estimators=N_ESTIMATORS)
        acc = accuracy_score(cv["y_true"], cv["y_pred"])
        top2 = float(cv["topk_accs"][2].mean())
        top5 = float(cv["topk_accs"][5].mean())

        results.append({
            "window_s":            win_s,
            "n_examples":          n_examples,
            "windows_per_driver":  int(windows_per_driver),
            "n_features":          len(feature_names),
            "accuracy":            acc,
            "acc_std":             float(cv["fold_accs"].std()),
            "top2":                top2,
            "top5":                top5,
        })
        print(f"  {win_s:>4}s: top1={acc:.4f} top2={top2:.4f} top5={top5:.4f}  "
              f"({n_examples} windows, ~{int(windows_per_driver)}/driver)")

    # Report
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TruckIDMe — Driver-ID Accuracy vs. Window Duration",
        "",
        f"5-fold stratified-on-driver CV, Random Forest ({N_ESTIMATORS} trees), "
        "9 aggregates per CAN signal.",
        "Feasibility: how much driving is needed to identify a driver "
        f"(random baseline = 1/46 = {1/46*100:.1f}%).",
        "",
        "| Window (s) | Top-1 | ± std | Top-2 | Top-5 | Windows | ~per driver |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['window_s']} | {r['accuracy']*100:.1f}% | {r['acc_std']*100:.1f}% | "
            f"{r['top2']*100:.1f}% | {r['top5']*100:.1f}% | "
            f"{r['n_examples']} | {r['windows_per_driver']} |"
        )
    (OUT_REPORTS / "window_sweep.md").write_text("\n".join(lines) + "\n")

    # Curve
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    xs   = [r["window_s"] for r in results]
    ys   = [r["accuracy"] * 100 for r in results]
    es   = [r["acc_std"] * 100 for r in results]
    y2   = [r["top2"] * 100 for r in results]
    y5   = [r["top5"] * 100 for r in results]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.errorbar(xs, ys, yerr=es, marker="o", capsize=4, linewidth=2, label="top-1")
    ax.plot(xs, y2, marker="s", linewidth=2, label="top-2")
    ax.plot(xs, y5, marker="^", linewidth=2, label="top-5")
    ax.axhline(1 / 46 * 100, color="gray", ls="--", label="random (1/46)")
    ax.set_xlabel("Window duration (s)")
    ax.set_ylabel("Driver-ID accuracy (%)")
    ax.set_title("Driver-ID feasibility vs. window duration (46 drivers)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIGURES / "window_sweep_curve.png", dpi=150)
    plt.close(fig)

    print()
    print(f"Report written to {OUT_REPORTS / 'window_sweep.md'}")
    print(f"Curve written to {OUT_FIGURES / 'window_sweep_curve.png'}")


if __name__ == "__main__":
    main()
