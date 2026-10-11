"""Reusable data-quality check: null/empty fraction per column, with colored
images — run after every dimensionality/data-altering stage.

Per call it writes into out_dir:
  - nulls_<stage>_matrix.png  : missingno matrix (rows × cols, where nulls sit)
  - nulls_<stage>_bar.png      : missingno bar (completeness per column)
  - nulls_<stage>.md           : null % per column (table)

Uses missingno when available; falls back to a matplotlib heatmap otherwise.

Usage:
    from src.qc.dataqc import null_report
    null_report(df, stage="after_slow_filter", out_dir=Path("experiments/exp01/qc"))
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

try:
    import missingno as msno
    _HAVE_MSNO = True
except ImportError:
    _HAVE_MSNO = False


def column_null_pct(df: pd.DataFrame) -> pd.Series:
    """Null percentage per column (0-100), in column order."""
    return df.isna().mean() * 100.0


def _fallback_heatmap(df: pd.DataFrame, stage: str, out_dir: Path) -> None:
    """Per-column null-% colored strip (used if missingno is unavailable)."""
    pct = column_null_pct(df)
    fig, ax = plt.subplots(figsize=(5.5, max(4, len(pct) * 0.13)))
    im = ax.imshow(pct.to_numpy().reshape(-1, 1), cmap="Reds", aspect="auto",
                   vmin=0, vmax=max(1.0, float(pct.max())))
    ax.set_yticks(range(len(pct)))
    ax.set_yticklabels([c[:42] for c in pct.index], fontsize=6)
    ax.set_xticks([])
    ax.set_title(f"Null % per column — {stage}")
    plt.colorbar(im, ax=ax, label="null %", fraction=0.05)
    fig.tight_layout()
    fig.savefig(out_dir / f"nulls_{stage}_bycol.png", dpi=140)
    plt.close(fig)


def null_report(df: pd.DataFrame, stage: str, out_dir: Path,
                sample_rows: int = 4000) -> pd.Series:
    """Save colored null visualisations + a stats table for one stage.

    Args:
        df: the DataFrame at this stage.
        stage: short label (filenames + titles).
        out_dir: directory to write the images + markdown into.
        sample_rows: rows to show in the matrix (down-sampled for large frames).

    Returns:
        Series of null% per column.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    pct = column_null_pct(df)
    n_rows, n_cols = df.shape
    overall = df.isna().to_numpy().mean() * 100.0
    n_any = int((pct > 0).sum())
    n_full = int((pct >= 100).sum())

    view = df if n_rows <= sample_rows else df.iloc[:: max(1, n_rows // sample_rows)]

    if _HAVE_MSNO:
        ax = msno.matrix(view, sparkline=False, fontsize=8)
        ax.set_title(f"Null matrix — {stage}  ({n_rows:,}×{n_cols}, "
                     f"overall {overall:.2f}%)", fontsize=10)
        ax.get_figure().savefig(out_dir / f"nulls_{stage}_matrix.png",
                                dpi=130, bbox_inches="tight")
        plt.close("all")

        ax = msno.bar(view, fontsize=8)
        ax.set_title(f"Completeness per column — {stage}", fontsize=10)
        ax.get_figure().savefig(out_dir / f"nulls_{stage}_bar.png",
                                dpi=130, bbox_inches="tight")
        plt.close("all")
    else:
        _fallback_heatmap(df, stage, out_dir)

    lines = [
        f"# Null report — {stage}",
        "",
        f"- Shape: {n_rows:,} rows × {n_cols} cols",
        f"- Overall null: {overall:.3f}%",
        f"- Columns with any null: {n_any} / {n_cols}   (fully null: {n_full})",
        "",
        "| Column | null % |",
        "|---|---:|",
    ]
    nz = pct[pct > 0].sort_values(ascending=False)
    if len(nz):
        lines += [f"| `{c}` | {v:.2f}% |" for c, v in nz.items()]
    else:
        lines.append("| _(no nulls in any column)_ | 0.00% |")
    (out_dir / f"nulls_{stage}.md").write_text("\n".join(lines) + "\n")

    print(f"  [null_report:{stage}] {n_rows:,}×{n_cols}, overall {overall:.2f}%, "
          f"{n_any} cols w/ nulls -> {out_dir}")
    return pct


if __name__ == "__main__":
    from src.config import DATA_PROCESSED
    fm = DATA_PROCESSED / "feature_matrix.csv"
    if fm.exists():
        null_report(pd.read_csv(fm), "feature_matrix", Path("outputs/figures/qc"))
    else:
        print("no feature_matrix.csv to smoke-test")
