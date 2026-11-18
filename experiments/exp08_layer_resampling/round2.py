"""Round 2 — `np.interp` vs bin averaging on test, all four windows, 5 partitions.

## Why

Round 1 (inner validation, one partition) found no closed-set reason to change
resampling, but bin averaging gave the higher open-set AUROC in 13 of 16
window/arm comparisons. One partition's driver AUROC wobbles by about ±0.09, so
that is a lead, not a result. This tests it properly: the five exp07 partitions,
the test split, and both resampling methods at every window, so each comparison
is **paired** — same drivers, same windows, only the resampling differs.

## Fixed configuration (nothing re-tuned)

layer 2, `mean_token`, `full` fine-tuning, 60 epochs, lr 1e-4, batch 64, seed 42.
Open set uses exp07's pre-registered scoring (LDA, `l2norm_whiten`, `mean`,
`cosine`). Closed set is 36-way, probe / LDA / forest.

30 s `np.interp` is exp07 Phase B; its saved embeddings are re-scored here, not
refitted, so that cell is identical to the reported result.

## Decision rule, fixed before the run

The headline window is 30 s (chosen on inner validation in exp07 Phase A). Bin
averaging replaces `np.interp` in the headline **only if, at 30 s**, its mean
driver-level AUROC is higher **and** it is higher in at least 4 of the 5
partitions, **and** closed-set LDA accuracy is not more than 2pp lower.
Other windows are reported, but picking a window from these test numbers would
be selection on test, so they are exploratory.

Each job writes `round2_cells/<resampling>_<window>s.json` after every
partition and resumes from saved embeddings.

Run one job:
    CUDA_VISIBLE_DEVICES=0 python -u -m experiments.exp08_layer_resampling.round2 \
        --window 30 --resampling binavg
Merge:
    python -m experiments.exp08_layer_resampling.round2 --summarise
"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import torch

from experiments.exp08_layer_resampling.round1 import load_tensor
from src.config import DATA_INTERIM
from src.models.finetune import BATCH_SIZE, build_model, EPOCHS, LEARNING_RATE
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, PRE_REGISTERED,
                                 score_config, SEED)
from src.models.readouts import closed_set_heads
from src.models.splits import known_train_index, known_unknown_partitions

WINDOWS = (30.0, 51.2, 90.0, 120.0)
RESAMPLINGS = ("interp", "binavg")
HEADS = ("linear_probe", "lda_centroid", "random_forest")
CELL_DIR = Path(__file__).parent / "round2_cells"
RESULTS_PATH = Path(__file__).parent / "round2.md"
HEADLINE_WINDOW = 30.0
MARGIN_PP = 2.0


def embedding_path(window: float, resampling: str, partition: int) -> Path:
    """Where one partition's fine-tuned embeddings live.

    30 s `np.interp` points at exp07 Phase B's files, so the reported result is
    re-scored rather than re-trained.

    Args:
        window: window length in seconds.
        resampling: 'interp' or 'binavg'.
        partition: 1-based partition number.

    Returns:
        Path under `data/interim_data/`.
    """
    if resampling == "interp" and window == HEADLINE_WINDOW:
        return DATA_INTERIM / f"embeddings_phaseB_mean_token_30s_p{partition}.npz"
    return (DATA_INTERIM /
            f"embeddings_exp08r2_{resampling}_{window:g}s_p{partition}.npz")


def run_job(window: float, resampling: str) -> None:
    """Fine-tune (or reuse) and score every partition for one cell.

    Args:
        window: window length in seconds.
        resampling: 'interp' or 'binavg'.
    """
    cached = load_tensor(window, resampling)
    tensor, drivers = cached["X"], cached["driver"]
    starts, channels = cached["start_time"], cached["channels"]
    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=N_PARTITIONS, seed=SEED)
    CELL_DIR.mkdir(exist_ok=True)
    out_path = CELL_DIR / f"{resampling}_{window:g}s.json"
    rows = []

    for index, (known, unknown) in enumerate(partitions, start=1):
        path = embedding_path(window, resampling, index)
        minutes = 0.0
        if not path.exists():
            fit_index = known_train_index(drivers, starts, known)
            codes = np.full(len(drivers), -1, dtype=np.int64)
            for code, driver in enumerate(np.unique(drivers[fit_index])):
                codes[drivers == driver] = code
            torch.manual_seed(SEED)
            np.random.seed(SEED)
            model = build_model(2)
            clock = time.perf_counter()
            model.fit(tensor[fit_index], codes[fit_index],
                      fine_tuning_type="full", adapter=None,
                      num_epochs=EPOCHS, batch_size=BATCH_SIZE,
                      base_learning_rate=LEARNING_RATE)
            minutes = (time.perf_counter() - clock) / 60
            features = model.transform(tensor, batch_size=256)
            np.savez_compressed(path, E=features, driver=drivers,
                                start_time=starts, channels=channels,
                                known=known, unknown=unknown)
            del model
            torch.cuda.empty_cache()

        saved = np.load(path, allow_pickle=True)
        heads = closed_set_heads(saved["E"], drivers, starts, known)
        window_auroc, driver_auroc = score_config(saved, PRE_REGISTERED)
        rows.append({"partition": index, "minutes": minutes,
                     **{h: heads[h][1] for h in HEADS},
                     "window_auroc": window_auroc,
                     "driver_auroc": driver_auroc})
        out_path.write_text(json.dumps({"window": window,
                                        "resampling": resampling,
                                        "rows": rows}, indent=2))
        print(f"{resampling} {window:g}s p{index}: "
              f"{'reused' if minutes == 0 else f'{minutes:.1f} min'} | "
              f"LDA {heads['lda_centroid'][1] * 100:.1f}% | open-set window "
              f"{window_auroc:.3f} driver {driver_auroc:.3f}", flush=True)


def summarise() -> None:
    """Merge finished cells into round2.md and apply the decision rule."""
    cells = {}
    for path in sorted(CELL_DIR.glob("*.json")):
        cell = json.loads(path.read_text())
        cells[(cell["resampling"], cell["window"])] = cell["rows"]

    stat = lambda rows, key: (np.mean([r[key] for r in rows]),
                              np.std([r[key] for r in rows]))
    lines = [
        "# exp08 Round 2 — `np.interp` vs bin averaging, on test",
        "",
        "layer 2, `mean_token`, `full`, 60 epochs, the five exp07 partitions "
        "(36 known / 10 unknown, seed 42). Every number is on the **test** "
        "split. Open set uses exp07's pre-registered scoring. Values are mean "
        "± sd over partitions; the two resampling methods share partitions, "
        "so comparisons are paired.",
        "",
        "| Window | Resampling | partitions | probe | LDA | forest | "
        "window AUROC | driver AUROC |",
        "|---|---|--:|--:|--:|--:|--:|--:|",
    ]
    for window in WINDOWS:
        for resampling in RESAMPLINGS:
            rows = cells.get((resampling, window))
            if not rows:
                lines.append(f"| {window:g} s | {resampling} | 0 | … | … | … "
                             "| … | … |")
                continue
            heads = " | ".join(
                "{:.1f}% ± {:.1f}".format(*(100 * v for v in stat(rows, h)))
                for h in HEADS)
            lines.append(
                f"| {window:g} s | {resampling} | {len(rows)} | {heads} | "
                "{:.3f} ± {:.3f} | ".format(*stat(rows, "window_auroc"))
                + "**{:.3f}** ± {:.3f} |".format(*stat(rows, "driver_auroc")))

    lines += ["", "## Paired differences (bin averaging − `np.interp`)", "",
              "| Window | LDA | window AUROC | driver AUROC | partitions "
              "where driver AUROC improved |", "|---|--:|--:|--:|--:|"]
    decision = "Pending — the 30 s cells have not both finished."
    for window in WINDOWS:
        a, b = cells.get(("interp", window)), cells.get(("binavg", window))
        if not a or not b or len(a) != len(b):
            continue
        diff = lambda key: np.array([y[key] - x[key] for x, y in zip(a, b)])
        lda, wa, da = diff("lda_centroid") * 100, diff("window_auroc"), \
            diff("driver_auroc")
        wins = int((da > 0).sum())
        lines.append(f"| {window:g} s | {lda.mean():+.1f}pp | "
                     f"{wa.mean():+.3f} | {da.mean():+.3f} | "
                     f"{wins} of {len(da)} |")
        if window == HEADLINE_WINDOW and len(a) == N_PARTITIONS:
            adopt = da.mean() > 0 and wins >= 4 and lda.mean() >= -MARGIN_PP
            decision = (
                f"At 30 s, bin averaging changes driver AUROC by "
                f"{da.mean():+.3f} ({wins} of 5 partitions improved) and LDA "
                f"accuracy by {lda.mean():+.1f}pp. "
                + ("**The rule is met: bin averaging becomes the headline "
                   "resampling.**" if adopt else
                   "**The rule is not met: `np.interp` stays in the "
                   "headline.**"))

    lines += ["", "## Decision", "", decision, "",
              "Other windows are exploratory: choosing a window from test "
              "numbers would be selection on test.", "",
              "## Limitations", "",
              "- One seed; partitions vary the driver draw, not training noise.",
              "- One drive per driver, so a stranger is also an unseen day. "
              "See `DECISIONS.md` C1."]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    """Run one job, or merge results."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=float, choices=WINDOWS)
    parser.add_argument("--resampling", choices=RESAMPLINGS)
    parser.add_argument("--summarise", action="store_true")
    arguments = parser.parse_args()
    warnings.filterwarnings("ignore")
    if arguments.summarise:
        summarise()
    else:
        run_job(arguments.window, arguments.resampling)


if __name__ == "__main__":
    main()
