"""Convergence check for Stage-1 leakage elimination.

For every feature in the current feature matrix, compute:
  - RF importance (single full-fit Random Forest)
  - η² = between-driver variance / total variance (does this feature separate
    drivers?)

then rank by importance and flag any high-importance feature that is also
high-η² — i.e. a leak the audit has not yet caught. If the top features are all
low-η², Stage-1 leakage elimination has converged.

Unlike verify_feature_... on raw signals, this measures η² on the exact feature
values the classifier consumes (per-(driver, sector) aggregates).

Outputs: outputs/reports/feature_leakage_audit.md

Run from project root:
    python -m src.qc.verify_feature_leakage
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from src.config import DATA_PROCESSED, OUT_REPORTS


FEATURE_MATRIX_FILE = "feature_matrix.csv"
META_COLS           = {"driver", "group", "sector_id", "n_rows"}
SEED                = 42
N_ESTIMATORS        = 300
LEAK_ETA_THRESHOLD  = 0.9
TOP_N               = 40


def eta_squared_by_driver(values: np.ndarray, drivers: np.ndarray) -> float:
    """η² of one feature: fraction of its variance explained by driver identity.

    Args:
        values: feature values across all (driver, sector) rows.
        drivers: driver label per row, aligned with values.

    Returns:
        η² in [0, 1], or NaN if <2 groups or zero total variance.
    """
    mask = ~np.isnan(values)
    v, d = values[mask], drivers[mask]
    if v.size == 0:
        return float("nan")
    groups = [v[d == g] for g in np.unique(d)]
    groups = [g for g in groups if g.size > 0]
    if len(groups) < 2:
        return float("nan")
    grand = v.mean()
    ss_total = float(((v - grand) ** 2).sum())
    if ss_total == 0.0:
        return float("nan")
    ss_between = float(sum(g.size * (g.mean() - grand) ** 2 for g in groups))
    return ss_between / ss_total


def main() -> None:
    df = pd.read_csv(DATA_PROCESSED / FEATURE_MATRIX_FILE)
    feature_cols = [c for c in df.columns if c not in META_COLS]
    X = df[feature_cols].to_numpy(dtype=float)
    y = df["driver"].to_numpy()

    # RF importances from a single full fit (median-imputed).
    X_imp = SimpleImputer(strategy="median").fit_transform(X)
    clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=SEED, n_jobs=-1)
    clf.fit(X_imp, y)
    importances = clf.feature_importances_

    # η² per feature on the raw (un-imputed) values.
    etas = np.array([eta_squared_by_driver(X[:, i], y) for i in range(len(feature_cols))])

    table = pd.DataFrame({
        "feature":    feature_cols,
        "importance": importances,
        "eta2":       etas,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    # Any feature that is both important and high-η² is an uncaught leak.
    leaks = table[(table["eta2"] >= LEAK_ETA_THRESHOLD)].sort_values(
        "importance", ascending=False
    )

    print(f"Features: {len(feature_cols)}   Drivers: {len(np.unique(y))}")
    print(f"Max η² across all features: {np.nanmax(etas):.3f}")
    print(f"Features with η² ≥ {LEAK_ETA_THRESHOLD}: {(etas >= LEAK_ETA_THRESHOLD).sum()}")
    print()
    print(f"Top {TOP_N} features by importance (with η²):")
    print(table.head(TOP_N).to_string(index=False,
          formatters={"importance": "{:.5f}".format, "eta2": "{:.3f}".format}))
    print()
    if len(leaks) == 0:
        print("CONVERGED: no feature has η² ≥ 0.9 — no uncaught leaks.")
    else:
        print(f"UNCAUGHT LEAKS ({len(leaks)}): features with η² ≥ {LEAK_ETA_THRESHOLD}:")
        print(leaks.to_string(index=False,
              formatters={"importance": "{:.5f}".format, "eta2": "{:.3f}".format}))

    # Report
    out_path = OUT_REPORTS / "feature_leakage_audit.md"
    lines = [
        "# TruckIDMe — Feature Leakage Audit (Stage-1 convergence check)",
        "",
        f"**Features:** {len(feature_cols)}   **Drivers:** {len(np.unique(y))}",
        f"**Leak threshold:** η² ≥ {LEAK_ETA_THRESHOLD}",
        f"**Features at/above threshold:** {(etas >= LEAK_ETA_THRESHOLD).sum()}",
        f"**Max η² across all features:** {np.nanmax(etas):.3f}",
        "",
        "η² here is computed on the exact per-(driver, sector) feature values the",
        "classifier consumes. A feature that is both high-importance and high-η²",
        "is a leak the audit has not yet removed.",
        "",
        ("**Verdict: CONVERGED — no feature has η² ≥ 0.9.**"
         if len(leaks) == 0 else
         f"**Verdict: {len(leaks)} uncaught leak feature(s) — see below.**"),
        "",
        f"## Top {TOP_N} features by RF importance (with η²)",
        "",
        "| Rank | Feature | Importance | η² |",
        "|---|---|---:|---:|",
    ]
    for i, r in enumerate(table.head(TOP_N).itertuples(index=False), 1):
        e = f"{r.eta2:.3f}" if not np.isnan(r.eta2) else "—"
        lines.append(f"| {i} | `{r.feature}` | {r.importance:.5f} | {e} |")
    out_path.write_text("\n".join(lines) + "\n")
    print(f"\nReport written to {out_path}")


if __name__ == "__main__":
    main()
