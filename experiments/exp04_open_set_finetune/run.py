"""exp04 — open-set driver identification with an adapted encoder.

The primary question of the capstone, asked directly: **can a time-series
foundation model say "I do not know you"?** exp03 showed the *frozen* encoder
separates drivers only weakly. This asks whether adaptation changes that, and
isolates how much of any change comes from the pre-training rather than from the
architecture.

Three things are new here, each fixing a specific flaw in exp03.

**1. The encoder is fine-tuned on the known drivers only.** exp03's frozen arm
could not be adapted, and a fine-tuned 46-class head cannot reject anyone. Both
problems dissolve by fitting on a partition's **36 known drivers**: the head has
36 classes, the 10 unknown drivers are never seen by the encoder, and
`MantisTrainer.transform` then yields *adapted* embeddings in which the unknown
drivers can be scored by prototype distance exactly as before. The open-set
machinery (`evaluate_partition`) is reused unchanged, so frozen and adapted
representations are compared on identical partitions, splits and scoring rules.

**2. Absolute level is restored.** `mantis/architecture/version1.py:58` defines

    ts_scaler = lambda x: (x - mean(x, axis=2)) / (std(x, axis=2) + 1e-5)

applied per window per channel before the convolutions. The encoder therefore
sees *shape only*; a driver who holds 45% pedal and one who holds 20% are
indistinguishable to it once the window is normalised, and no amount of
fine-tuning can recover information that was divided out at the input.
`level_features` adds back two numbers per channel, and every representation is
evaluated with and without them so the contribution is measured rather than
assumed.

**3. The read-out is no longer only nearest-prototype.** PCA is a dimensionality
step, not a classifier, so exp03's PCA sweep never tested whether the frozen
representation was weak or merely hostile to Euclidean distance in 12,800
dimensions. `closed_set_heads` scores each representation three ways: a linear
probe (the standard protocol for evaluating a learned representation), LDA to a
supervised subspace followed by nearest centroid, and a random forest, which
assumes no metric at all.

**Arms.** `full` (pre-trained, fine-tuned end to end) and `scratch` (identical
architecture, random initialisation, trained end to end). `head` is dropped:
with a linear probe and a random forest now run on the frozen embeddings, a
frozen-encoder-plus-trained-head arm measures nothing those do not. `scratch` is
**not** optional — without it, "the foundation model works" cannot be
distinguished from "a transformer works", and the pre-training claim has no
control. The frozen representation enters as a reference row, reusing the
embeddings `embed.py` already wrote.

Run from the repo root in the `truckidme` env. Smoke test first:
    /home/ap9107/anaconda3/envs/truckidme/bin/python \\
        -m experiments.exp04_open_set_finetune.run --partitions 1 --epochs 3

Then the full experiment:
    /home/ap9107/anaconda3/envs/truckidme/bin/python \\
        -m experiments.exp04_open_set_finetune.run
"""
from __future__ import annotations

import argparse
import pickle
import time
from pathlib import Path

import numpy as np
import torch
from mantis.trainer import MantisTrainer

from experiments.exp04_open_set_finetune.encoder import (BATCH_SIZE, DEVICE,
                                                         LEARNING_RATE,
                                                         build_network)
from experiments.exp04_open_set_finetune.plots import (plot_auroc_comparison,
                                                       plot_closed_set,
                                                       plot_embedding_geometry,
                                                       plot_roc)
from src.config import DATA_INTERIM, OUT_FIGURES
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, SCORE_RULES,
                                 evaluate_partition, summarise)
from src.features.build_embeddings import embedding_path as frozen_embedding_path
from src.features.build_tensors import tensor_path
from src.models.readouts import average_heads, closed_set_heads
from src.models.splits import known_train_index, known_unknown_partitions

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EXPERIMENT_DIR / "results.md"

# Under data/ because it is gitignored and can reach a few hundred MB: it holds
# every partition's raw scores so the figures can be redrawn without retraining.
CHECKPOINT_PATH = DATA_INTERIM / "exp04_stage2_checkpoint.pkl"

# 51.2 s puts the 512-point grid at exactly 10.0 Hz, the modal native rate of the
# channel set (20 of the 50 kept channels sample at 10 Hz), so the most common
# channel is neither decimated nor interpolated. It also yields ~2.3x the windows
# of a 120 s setting, which matters because fine-tuning an 8M-parameter encoder on
# ~1,250 training windows is the data-starved end of this experiment.
WINDOW_SECONDS = 51.2

ARMS: tuple[str, ...] = ("full", "scratch")
SEED = 42

# Set from Stage 1's curves, not inherited from finetune_mantis, so the recorded
# configuration and the executed run cannot drift apart.
#
# Stage 1 trained all three arms for 200 epochs and logged every one. Validation
# accuracy is flat from roughly epoch 60 onward — `full` reads 29.2% at 60, 32.2%
# at its peak of 91, and 31.7% at 200 — while adjacent epochs differ by ~2pp, so
# the peak's exact location is noise on 202 validation windows (one window is
# 0.5pp). Any budget past the knee is equivalent; 100 is chosen as a round number
# comfortably beyond it that halves the cost of a 186-epoch budget.
EPOCHS = 100

def save_checkpoint(state: dict) -> None:
    """Persist completed partitions so a crash costs minutes, not hours.

    Written to a temporary file and renamed, because `rename` is atomic on the
    same filesystem: a crash during the write leaves the previous checkpoint
    intact rather than a truncated one.

    Args:
        state: open_rows, head_rows, arm_minutes and the count of completed
            partitions.
    """
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    staging = CHECKPOINT_PATH.with_suffix(".tmp")
    with staging.open("wb") as handle:
        pickle.dump(state, handle, protocol=pickle.HIGHEST_PROTOCOL)
    staging.replace(CHECKPOINT_PATH)


def load_checkpoint() -> dict:
    """Completed partitions from a previous run, or an empty state.

    Returns:
        open_rows, head_rows, arm_minutes and the count of completed partitions.
    """
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open("rb") as handle:
            return pickle.load(handle)
    return {"open_rows": {}, "head_rows": {},
            "arm_minutes": {arm: [] for arm in ARMS}, "completed": 0}


def level_features(windows: np.ndarray) -> np.ndarray:
    """Per-window, per-channel mean and standard deviation.

    These are precisely the two statistics Mantis divides out at its input, so
    they are unrecoverable from any embedding, frozen or adapted.

    Args:
        windows: (n_windows, n_channels, steps) tensor.

    Returns:
        (n_windows, 2 * n_channels) — all means, then all stds, channel order
        preserved in both halves.
    """
    return np.concatenate([windows.mean(axis=2), windows.std(axis=2)],
                          axis=1).astype(np.float32)


def adapted_embeddings(arm: str, windows: np.ndarray, drivers: np.ndarray,
                       starts: np.ndarray, known: np.ndarray,
                       num_epochs: int) -> tuple[np.ndarray, float]:
    """Fine-tune one arm on one partition's known drivers, then embed everything.

    Args:
        arm: 'full' (pre-trained) or 'scratch' (random initialisation).
        windows: (n_windows, n_channels, steps) tensor.
        drivers: driver id per window.
        starts: window start time per window.
        known: driver ids treated as enrolled.
        num_epochs: training epochs.

    Returns:
        (embeddings for every window, training minutes). Embeddings have shape
        (n_windows, n_channels * hidden_dim); unknown drivers and all test
        windows were never seen during fitting.
    """
    torch.manual_seed(SEED)       # same initialisation and batch order per arm
    np.random.seed(SEED)

    train_index = known_train_index(drivers, starts, known)
    _, labels = np.unique(drivers[train_index], return_inverse=True)

    model = MantisTrainer(device=DEVICE,
                          network=build_network(pretrained=(arm != "scratch")))
    clock = time.perf_counter()
    model.fit(windows[train_index], labels,
              fine_tuning_type=("scratch" if arm == "scratch" else arm),
              adapter=None, num_epochs=num_epochs, batch_size=BATCH_SIZE,
              base_learning_rate=LEARNING_RATE)
    minutes = (time.perf_counter() - clock) / 60

    return model.transform(windows, batch_size=256), minutes


def build_report(open_set: dict[str, dict], heads: dict[str, dict],
                 timings: dict[str, float], n_known: int, n_windows: int,
                 n_channels: int, partitions: int, epochs: int,
                 figures: list[Path]) -> str:
    """Render the experiment outcome.

    Args:
        open_set: representation name to summarised open-set metrics.
        heads: representation name to averaged closed-set head accuracies.
        timings: arm name to mean fine-tuning minutes.
        n_known: enrolled driver count per partition.
        n_windows: total windows in the tensor.
        n_channels: channel count.
        partitions: partitions evaluated.
        epochs: training epochs used.
        figures: paths of the written figures.

    Returns:
        Markdown report.
    """
    lines = [
        "# exp04 — open-set driver identification with an adapted encoder",
        "",
        f"**{partitions} partition(s) of {n_known} known / {N_UNKNOWN} unknown "
        f"drivers**, stratified by awareness group. {WINDOW_SECONDS:g} s windows "
        f"({n_windows} total, {n_channels} channels, 512-point grid = "
        f"{512 / WINDOW_SECONDS:.2f} Hz). Encoders are fitted on the known "
        "drivers' **training** windows only, for "
        f"{epochs} epochs; the unknown drivers are used for evaluation and "
        "nothing else. Values are mean ± sd across partitions.",
        "",
        "`+ level` appends each window's per-channel mean and standard deviation "
        f"({2 * n_channels} features) to the representation. Mantis divides both "
        "out at its input (`ts_scaler`), so they cannot be recovered from any "
        "embedding; this measures what that normalisation costs.",
        "",
        "## Open set — rejecting the never-enrolled",
        "",
        "AUROC by scoring rule; **0.500 is chance**. `window` scores one window "
        "at a time; `driver` takes the median score per driver, which is the "
        "deployment question.",
        "",
        "| Representation | " + " | ".join(f"`{r}`" for r in SCORE_RULES)
        + " | best driver |",
        "|---|" + "--:|" * (len(SCORE_RULES) + 1),
    ]
    for name, stats in open_set.items():
        cells = " | ".join(f"{stats[f'auroc:{r}'][0]:.3f} ± "
                           f"{stats[f'auroc:{r}'][1]:.3f}" for r in SCORE_RULES)
        best = max(SCORE_RULES, key=lambda r: stats[f"driver_auroc:{r}"][0])
        lines.append(f"| {name} | {cells} | "
                     f"**{stats[f'driver_auroc:{best}'][0]:.3f}** (`{best}`) |")

    lines += [
        "",
        "## Closed set — naming the enrolled drivers",
        "",
        f"{n_known}-way, random floor {1 / n_known:.1%}. Three read-outs on the "
        "same representation: `linear_probe` is the standard protocol for "
        "evaluating a learned representation, `lda_centroid` replaces PCA's "
        "unsupervised variance objective with a supervised between-driver one, "
        "and `random_forest` assumes no metric. A large spread between them means "
        "exp03's low frozen number was a **read-out** limitation rather than a "
        "representation limitation.",
        "",
        "| Representation | linear probe | LDA + centroid | random forest |",
        "|---|--:|--:|--:|",
    ]
    for name, per_head in heads.items():
        cells = " | ".join(
            f"**{per_head[h][1][0]:.1%}** ± {per_head[h][1][1]:.1%} "
            f"(top-2 {per_head[h][2][0]:.1%})"
            for h in ("linear_probe", "lda_centroid", "random_forest"))
        lines.append(f"| {name} | {cells} |")

    lines += [
        "",
        "## Cost",
        "",
        "| Arm | Mean fine-tuning minutes per partition |",
        "|---|--:|",
    ]
    for arm, minutes in timings.items():
        lines.append(f"| {arm} | {minutes:.1f} |")

    lines += [
        "",
        "## How to read this",
        "",
        "- **`full` − `scratch`** is the value of the pre-training, with the "
        "architecture held fixed. It is the only comparison here that licenses a "
        "claim about foundation models rather than about transformers.",
        "- **`+ level` − plain** is what instance normalisation costs. If it is "
        "large, the finding is that a shape-only encoder cannot see driver "
        "identity on this data, whatever its weights.",
        "- **frozen** reuses exp03's embeddings unchanged, as the reference "
        "point adaptation is measured against.",
        "",
    ] + ([
        "## Figures",
        "",
    ] + [f"- `{p.relative_to(OUT_FIGURES.parent.parent)}`" for p in figures] + [""]
         if figures else [
        "## Figures",
        "",
        "**Not yet drawn** — this is an interim report written after partition "
        f"{partitions}. Figures are produced once the run completes.",
        "",
    ]) + [
        "## Caveat that bounds every number",
        "",
        "Each driver drove **once**, so an unknown driver is also an unknown "
        "*day*: a rejection may fire because the conditions are unfamiliar rather "
        "than because the person drives differently. These AUROCs are an upper "
        "bound on genuine behavioural rejection. See `DECISIONS.md` C1.",
        "",
    ]
    return "\n".join(lines) + "\n"


def aggregate(open_rows: dict[str, list[dict]], head_rows: dict[str, list[dict]],
              arm_minutes: dict[str, list[float]]
              ) -> tuple[dict, dict, dict]:
    """Summarise whatever partitions have completed so far.

    Args:
        open_rows: representation name to per-partition open-set results.
        head_rows: representation name to per-partition read-out accuracies.
        arm_minutes: arm name to per-partition training minutes.

    Returns:
        (open-set summaries, averaged read-outs, mean minutes per arm).
    """
    return ({name: summarise(rows) for name, rows in open_rows.items()},
            {name: average_heads(rows) for name, rows in head_rows.items()},
            {arm: float(np.mean(values)) if values else 0.0
             for arm, values in arm_minutes.items()})


def main() -> None:
    """Run every arm on every partition and write the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partitions", type=int, default=N_PARTITIONS,
                        help="known/unknown partitions to evaluate")
    parser.add_argument("--epochs", type=int, default=EPOCHS,
                        help="fine-tuning epochs per arm")
    parser.add_argument("--restart", action="store_true",
                        help="ignore any existing checkpoint and start over")
    args = parser.parse_args()

    for path in (tensor_path(WINDOW_SECONDS),
                 frozen_embedding_path("cls_token", WINDOW_SECONDS)):
        if not path.exists():
            raise FileNotFoundError(
                f"missing {path}; run exp03's build_tensors.py and embed.py first")

    bundle = np.load(tensor_path(WINDOW_SECONDS), allow_pickle=False)
    windows, drivers, starts = bundle["X"], bundle["driver"], bundle["start_time"]
    frozen = np.load(frozen_embedding_path("cls_token", WINDOW_SECONDS),
                     allow_pickle=False)
    if not np.array_equal(frozen["driver"], drivers):
        raise ValueError("tensor and frozen embeddings disagree on driver labels; "
                         "they are not from the same build")

    levels = level_features(windows)
    partitions = known_unknown_partitions(drivers, N_UNKNOWN, N_PARTITIONS,
                                          SEED)[:args.partitions]
    n_known = len(partitions[0][0])
    print(f"{windows.shape} tensor | {n_known} known / {N_UNKNOWN} unknown | "
          f"{len(partitions)} partition(s) | {args.epochs} epochs | "
          f"levels {levels.shape}")

    if args.restart and CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
    state = load_checkpoint()
    open_rows: dict[str, list[dict]] = state["open_rows"]
    head_rows: dict[str, list[dict]] = state["head_rows"]
    arm_minutes: dict[str, list[float]] = state["arm_minutes"]
    completed: int = state["completed"]
    geometry: dict[str, np.ndarray] = {}      # partition 1 only, for the t-SNE
    geometry_known: np.ndarray = np.array([])
    if completed:
        print(f"resuming from checkpoint: {completed} partition(s) already "
              f"scored ({CHECKPOINT_PATH})", flush=True)

    for index, (known, unknown) in enumerate(partitions, start=1):
        if index <= completed:
            print(f"\npartition {index}/{len(partitions)} — already scored, "
                  "skipping", flush=True)
            continue
        print(f"\npartition {index}/{len(partitions)}", flush=True)
        representations = {"frozen": frozen["E"]}
        for arm in ARMS:
            embeddings, minutes = adapted_embeddings(arm, windows, drivers, starts,
                                                     known, args.epochs)
            representations[arm] = embeddings
            arm_minutes[arm].append(minutes)
            print(f"  {arm:<8} fitted in {minutes:.1f} min -> {embeddings.shape}",
                  flush=True)
        if index == 1:
            geometry = dict(representations)
            geometry_known = known

        for name, features in representations.items():
            for suffix, matrix in ((name, features),
                                   (f"{name} + level",
                                    np.hstack([features, levels]))):
                open_rows.setdefault(suffix, []).append(
                    evaluate_partition(matrix, drivers, starts, known, unknown))
                head_rows.setdefault(suffix, []).append(
                    closed_set_heads(matrix, drivers, starts, known))
                best = max(SCORE_RULES,
                           key=lambda r: open_rows[suffix][-1]["auroc"][r])
                print(f"    {suffix:<22} AUROC {open_rows[suffix][-1]['auroc'][best]:.3f} "
                      f"({best})  probe top-1 "
                      f"{head_rows[suffix][-1]['linear_probe'][1]:.1%}", flush=True)

        save_checkpoint({"open_rows": open_rows, "head_rows": head_rows,
                         "arm_minutes": arm_minutes, "completed": index})
        interim_open, interim_heads, interim_timings = aggregate(
            open_rows, head_rows, arm_minutes)
        RESULTS_PATH.write_text(build_report(
            interim_open, interim_heads, interim_timings, n_known, len(windows),
            windows.shape[1], index, args.epochs, []))
        print(f"  checkpointed {index}/{len(partitions)}; interim results in "
              f"{RESULTS_PATH.name}", flush=True)

    open_set, heads, timings = aggregate(open_rows, head_rows, arm_minutes)
    if not open_set:
        raise RuntimeError("no partitions completed; nothing to report")

    plot_rule = max(SCORE_RULES,
                    key=lambda r: np.mean([s[f"auroc:{r}"][0]
                                           for s in open_set.values()]))
    figures = [plot_roc(open_rows, plot_rule),
               plot_auroc_comparison(open_set, SCORE_RULES),
               plot_closed_set(heads, 1 / n_known)]
    if geometry:
        figures.append(plot_embedding_geometry(geometry, drivers, geometry_known))
    else:
        # partition 1 was restored from a checkpoint, so its embeddings are gone;
        # they are 350 MB and not worth persisting for one figure
        print("\nskipping the t-SNE: partition 1 was resumed, not recomputed")
    print(f"\nfigures ({plot_rule} chosen for ROC): "
          + ", ".join(p.name for p in figures))

    scored = max(len(rows) for rows in open_rows.values())
    RESULTS_PATH.write_text(build_report(
        open_set, heads, timings, n_known, len(windows), windows.shape[1],
        scored, args.epochs, figures))

    print("\nbest open-set AUROC per representation:")
    for name, stats in open_set.items():
        best = max(SCORE_RULES, key=lambda r: stats[f"auroc:{r}"][0])
        print(f"  {name:<22} {stats[f'auroc:{best}'][0]:.3f} ({best})")
    print(f"\nresults -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
