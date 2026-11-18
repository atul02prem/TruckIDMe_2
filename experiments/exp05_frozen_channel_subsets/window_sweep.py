"""Context length against temporal resolution, under Mantis's 512-point budget.

## The trade this measures

Mantis takes a fixed 512-point input regardless of how much wall-clock time the
window covers, so window length and sampling rate are **not independent**:

| Window | Points | Effective rate | Relative to native rates |
|---|--:|--:|---|
| 30 s    | 512 | 17.07 Hz | above the native rate of 30 of 50 channels |
| 51.2 s  | 512 | **10.00 Hz** | exactly the modal native rate (20 of 50) |
| 90 s    | 512 | 5.69 Hz | below the native rate of 39 of 50 |
| 120 s   | 512 | 4.27 Hz | below the native rate of 39 of 50; 100 Hz channels are downsampled 23x |

A longer window buys context and pays for it in resolution. There is no setting
that gives both, which makes this a genuine axis of the study rather than a
hyperparameter to tune away.

51.2 s is the only length where the grid lands on a native rate
(512 / 51.2 = 10.00 Hz exactly, the modal rate across the 50 audited channels).
Every other length resamples every channel to a rate nothing was sampled at.

## What is held fixed

All four lengths use the same 46 drivers, the same audited 50 channels, the same
frozen encoder, the same per-driver chronological 70/5/25 split and the same
three read-outs. Only the window length — and therefore the effective rate —
changes. Window **count** changes as a consequence, which is reported because
it is part of the trade: longer windows mean fewer training examples.

## Commands

```bash
python -u -m experiments.exp05_frozen_channel_subsets.window_sweep
```
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from src.config import OUT_FIGURES
from src.models.splits import split_by_driver
from src.models.readouts import closed_set_heads
from src.features.build_embeddings import embedding_path as frozen_embedding_path

WINDOWS = (30.0, 51.2, 90.0, 120.0)
POINTS = 512
HEADS = ("linear_probe", "lda_centroid", "random_forest")
RESULTS_PATH = Path(__file__).parent / "window_sweep.md"
FIGURE_PATH = OUT_FIGURES / "exp05_window_sweep.png"


def effective_rate(window_seconds: float) -> float:
    """Sampling rate Mantis actually sees for a given window length.

    Args:
        window_seconds: window length in seconds.

    Returns:
        Effective rate in Hz, given the fixed 512-point input.
    """
    return POINTS / window_seconds


def plot_sweep(rows: list[dict]) -> None:
    """Draw accuracy against window length, annotated with effective rate.

    Args:
        rows: one dict per window length with keys 'window', 'rate',
            'n_windows' and one entry per read-out.
    """
    lengths = [row["window"] for row in rows]
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    for head, colour in zip(HEADS, ("#4C72B0", "#DD8452", "#55A868")):
        axes[0].plot(lengths, [row[head] * 100 for row in rows], marker="o",
                     label=head, color=colour)
    axes[0].axvline(51.2, color="#C44E52", linestyle="--", linewidth=1,
                    label="51.2 s = 10.00 Hz (modal native rate)")
    axes[0].set_xlabel("window length (s)")
    axes[0].set_ylabel("46-way top-1 accuracy (%)")
    axes[0].set_title("Accuracy vs context length")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)

    best = [max(row[h] for h in HEADS) * 100 for row in rows]
    axes[1].plot([row["rate"] for row in rows], best, marker="o",
                 color="#4C72B0")
    for row, value in zip(rows, best):
        axes[1].annotate(f"{row['window']:g}s\n{row['n_windows']} win",
                         (row["rate"], value), fontsize=8,
                         xytext=(5, -12), textcoords="offset points")
    axes[1].set_xlabel("effective sampling rate (Hz), 512 points / window")
    axes[1].set_ylabel("best read-out top-1 (%)")
    axes[1].set_title("Accuracy vs temporal resolution")
    axes[1].grid(alpha=0.3)

    figure.suptitle("Context length against temporal resolution under a fixed "
                    "512-point budget (46 drivers, frozen Mantis, 50 channels)")
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=150)
    plt.close(figure)


def write_report(rows: list[dict]) -> None:
    """Write the sweep report inside the experiment folder.

    Args:
        rows: one dict per window length, as built by `main`.
    """
    lines = [
        "# exp05 — context length vs temporal resolution",
        "",
        "Mantis takes **512 points regardless of window length**, so context "
        "and resolution cannot be increased together. 46-way closed set, "
        "chance 2.2%, frozen encoder, audited 50 channels, per-driver "
        "chronological 70/5/25 split. Only the window length changes.",
        "",
        "| Window | Effective rate | Windows | train / test | linear probe | "
        "LDA + centroid | random forest |",
        "|---|--:|--:|--:|--:|--:|--:|",
    ]
    for row in rows:
        cells = " | ".join(f"{row[h] * 100:.1f}%" for h in HEADS)
        lines.append(
            f"| {row['window']:g} s | {row['rate']:.2f} Hz | "
            f"{row['n_windows']:,} | {row['n_train']:,} / {row['n_test']:,} | "
            f"{cells} |")

    best_row = max(rows, key=lambda r: max(r[h] for h in HEADS))
    lines += [
        "",
        f"Best: **{best_row['window']:g} s** at "
        f"{max(best_row[h] for h in HEADS) * 100:.1f}%.",
        "",
        "## Why this is an axis, not a hyperparameter",
        "",
        "- **51.2 s is the only length whose grid matches a native rate.** "
        "512 / 51.2 = 10.00 Hz exactly, the modal rate across the audited 50 "
        "channels (20 of 50 are natively 10 Hz). Every other length resamples "
        "every channel to a rate nothing was recorded at.",
        "- **At 120 s the grid is 4.27 Hz**, below the native rate of 39 of the "
        "50 channels; the 100 Hz channels are downsampled 23x. Whatever "
        "accuracy is gained there is gained *despite* discarding most of the "
        "temporal detail.",
        "- **Window count moves too.** Longer windows mean fewer training "
        "examples, and Stage 1 of exp04 established that training-set size is "
        "the binding constraint. So the trade is really three-way: context, "
        "resolution, and sample count.",
        "",
        "## Figure",
        "",
        f"- `{FIGURE_PATH}`",
        "",
        "## Limitations",
        "",
        "- **Single split per length, no error bars.**",
        "- Resampling is linear interpolation onto a uniform grid "
        "(`np.interp`), not bin averaging, so upsampled slow channels carry "
        "interpolated rather than observed values.",
        "- Frozen encoder only; one drive per driver. See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Score every cached window length and write the report."""
    rows = []
    for window in WINDOWS:
        cached = np.load(frozen_embedding_path("cls_token", window),
                         allow_pickle=True)
        embeddings, drivers = cached["E"], cached["driver"]
        starts = cached["start_time"]
        cohort = np.unique(drivers)
        train_index, test_index = split_by_driver(drivers, starts)
        scores = closed_set_heads(embeddings, drivers, starts, cohort)

        row = {"window": window, "rate": effective_rate(window),
               "n_windows": len(embeddings), "n_train": len(train_index),
               "n_test": len(test_index),
               **{h: scores[h][1] for h in HEADS}}
        rows.append(row)
        print(f"  {window:5g} s | {row['rate']:5.2f} Hz | "
              f"{len(embeddings):>5,} windows | "
              + "  ".join(f"{h.split('_')[0]} {row[h] * 100:5.1f}%"
                          for h in HEADS))

    plot_sweep(rows)
    write_report(rows)
    print(f"\nfigure  -> {FIGURE_PATH}")
    print(f"results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
