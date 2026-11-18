"""Round 1 — read-out layer x resampling, all four windows, on inner validation.

## The two knobs

**Read-out layer.** Every fine-tuned run so far read the encoder out at layer 2
of 6. That choice came from a *frozen* selection, and the Mantis paper's own
ablation says an intermediate layer helps frozen feature extraction while
fine-tuning is reasonable at full depth. So the fine-tuned arm has been using a
frozen-arm setting. Levels: 2 and -1 (the final layer).

**Resampling.** `np.interp` point-samples channels faster than the 512-point
grid, which aliases. Bin averaging is the correct downsample
(`build_binavg_tensors.py`). Levels: `interp`, `binavg`.

## Protocol — identical to exp07 Phase A

`mean_token`, `full` fine-tuning, 60 epochs, lr 1e-4, batch 64, seed 42, the
first 36-known/10-unknown partition. The encoder is fitted on **inner-train**
and everything is scored on **inner validation**; no test window is touched, so
whatever is chosen here can be evaluated on test once, cleanly.

Each cell also records a frozen encoder at the same layer and resampling, and
the open-set AUROC of exp07's pre-registered scoring configuration, both at
negligible extra cost.

## Decision rule, fixed before the run

The incumbent is layer 2 + `interp` (exp07). A challenger replaces it only if
its best window beats the incumbent's best window by **more than 2pp** of
inner-validation closed-set accuracy. Otherwise the incumbent stands, exp07's
test numbers are final, and this experiment is reported as a sensitivity check.

One process runs one (layer, resampling) cell over all windows and writes
`cells/<layer>_<resampling>.json`; `summarise.py` merges them.

Run:
    CUDA_VISIBLE_DEVICES=0 python -u -m experiments.exp08_layer_resampling.round1 \
        --layer 2 --resampling interp
"""
from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import torch
from mantis.architecture import MantisV1
from mantis.trainer import MantisTrainer
from sklearn.preprocessing import StandardScaler

from experiments.exp08_layer_resampling.build_binavg_tensors import binavg_path
from src.config import DATA_INTERIM, MANTIS_CHECKPOINT
from src.features.build_tensors import tensor_path
from src.models.finetune import BATCH_SIZE, build_model, EPOCHS, LEARNING_RATE
from src.models.open_set import (auroc_pair, inner_indices, N_PARTITIONS,
                                 N_UNKNOWN, project, prototype_scores, SEED,
                                 transform_rows)
from src.models.readouts import closed_set_heads, HEADS
from src.models.splits import inner_train_index, known_unknown_partitions

WINDOWS = (30.0, 51.2, 90.0, 120.0)
OPEN_SET_CONFIG = ("lda", "l2norm_whiten", "mean", "cosine")   # exp07 Phase C
CELL_DIR = Path(__file__).parent / "cells"


def load_tensor(window_seconds: float, resampling: str):
    """Load one window length's tensor under one resampling method.

    Args:
        window_seconds: window length.
        resampling: 'interp' (exp03's tensor) or 'binavg'.

    Returns:
        The loaded npz archive.
    """
    path = (tensor_path(window_seconds) if resampling == "interp"
            else binavg_path(window_seconds))
    return np.load(path, allow_pickle=True)


def open_set_inner(features: np.ndarray, drivers: np.ndarray,
                   starts: np.ndarray, known: np.ndarray, unknown: np.ndarray
                   ) -> tuple[float, float]:
    """Inner-validation open-set AUROC under the pre-registered scoring.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        starts: window start time per window.
        known: enrolled driver ids.
        unknown: never-enrolled driver ids.

    Returns:
        (window AUROC, driver AUROC).
    """
    projection, transform, prototype, rule = OPEN_SET_CONFIG
    train_index, val_index, unknown_index = inner_indices(drivers, starts,
                                                          known, unknown)
    scaled = StandardScaler().fit(features[train_index]).transform(features)
    train_drivers = drivers[train_index]
    p_train, p_all = project(scaled[train_index], scaled, train_drivers,
                             projection)
    t_train, t_all = transform_rows(p_train, p_all, transform)
    known_scores = prototype_scores(t_train, train_drivers, t_all[val_index],
                                    prototype)[rule]
    unknown_scores = prototype_scores(t_train, train_drivers,
                                      t_all[unknown_index], prototype)[rule]
    return auroc_pair(known_scores, unknown_scores, drivers[val_index],
                      drivers[unknown_index])


def score(features: np.ndarray, drivers: np.ndarray, starts: np.ndarray,
          known: np.ndarray, unknown: np.ndarray, known_train: np.ndarray
          ) -> dict:
    """Closed- and open-set inner-validation scores for one embedding.

    Args:
        features: all window embeddings.
        drivers: driver id per window.
        starts: window start time per window.
        known: enrolled driver ids.
        unknown: never-enrolled driver ids.
        known_train: positions of the known drivers' training windows.

    Returns:
        {read-out: top-1, 'window_auroc', 'driver_auroc'}.
    """
    heads = closed_set_heads(features[known_train], drivers[known_train],
                             starts[known_train], known)
    window_auroc, driver_auroc = open_set_inner(features, drivers, starts,
                                                known, unknown)
    return {**{h: heads[h][1] for h in HEADS},
            "window_auroc": window_auroc, "driver_auroc": driver_auroc}


def main() -> None:
    """Run one (layer, resampling) cell over every window length."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--layer", type=int, required=True, choices=(0, 2, -1))
    parser.add_argument("--resampling", required=True,
                        choices=("interp", "binavg"))
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--window", type=float, action="append", default=None)
    arguments = parser.parse_args()
    warnings.filterwarnings("ignore")

    layer_name = "final" if arguments.layer == -1 else f"layer{arguments.layer}"
    cell_name = f"{layer_name}_{arguments.resampling}"
    CELL_DIR.mkdir(exist_ok=True)
    rows = []

    for window in arguments.window or WINDOWS:
        cached = load_tensor(window, arguments.resampling)
        tensor, drivers = cached["X"], cached["driver"]
        starts, channels = cached["start_time"], cached["channels"]
        known, unknown = known_unknown_partitions(
            drivers, n_unknown=N_UNKNOWN, n_partitions=N_PARTITIONS,
            seed=SEED)[0]
        fit_index, known_train = inner_train_index(drivers, starts, known)
        codes = np.full(len(drivers), -1, dtype=np.int64)
        for code, driver in enumerate(np.unique(drivers[fit_index])):
            codes[drivers == driver] = code

        print(f"\n=== {cell_name} | {window:g} s | {tensor.shape} | "
              f"fit on {len(fit_index):,} inner-train windows ===")

        frozen = build_model(arguments.layer).transform(tensor, batch_size=256)
        frozen_scores = score(frozen, drivers, starts, known, unknown,
                              known_train)

        torch.manual_seed(SEED)
        np.random.seed(SEED)
        model = build_model(arguments.layer)
        clock = time.perf_counter()
        model.fit(tensor[fit_index], codes[fit_index], fine_tuning_type="full",
                  adapter=None, num_epochs=arguments.epochs,
                  batch_size=BATCH_SIZE, base_learning_rate=LEARNING_RATE)
        minutes = (time.perf_counter() - clock) / 60
        features = model.transform(tensor, batch_size=256)
        np.savez_compressed(
            DATA_INTERIM / f"embeddings_exp08_{cell_name}_{window:g}s.npz",
            E=features, driver=drivers, start_time=starts, channels=channels)
        full_scores = score(features, drivers, starts, known, unknown,
                            known_train)

        rows.append({"window": window, "n_fit": int(len(fit_index)),
                     "minutes": minutes, "frozen": frozen_scores,
                     "full": full_scores})
        for arm, values in (("frozen", frozen_scores), ("full", full_scores)):
            print(f"  {arm:6s} | "
                  + "  ".join(f"{h.split('_')[0]} {values[h] * 100:5.1f}%"
                              for h in HEADS)
                  + f" | open-set window {values['window_auroc']:.3f} "
                    f"driver {values['driver_auroc']:.3f}")
        print(f"  fitted in {minutes:.1f} min")

        # Merge with rows already saved, so two processes splitting the windows
        # of one cell across GPUs do not overwrite each other.
        cell_path = CELL_DIR / f"{cell_name}.json"
        done = {row["window"] for row in rows}
        saved = (json.loads(cell_path.read_text())["rows"]
                 if cell_path.exists() else [])
        merged = sorted([r for r in saved if r["window"] not in done] + rows,
                        key=lambda r: r["window"])
        cell_path.write_text(json.dumps(
            {"layer": arguments.layer, "resampling": arguments.resampling,
             "epochs": arguments.epochs, "rows": merged}, indent=2))

    print(f"\ncell -> {CELL_DIR / f'{cell_name}.json'}")


if __name__ == "__main__":
    main()
