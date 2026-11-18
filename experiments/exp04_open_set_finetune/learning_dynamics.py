"""exp04 Stage 1 — learning dynamics: how does each arm actually train?

A thermometer, not a result. Nothing here goes into the capstone as a finding;
its only job is to tell Stage 2 how many epochs to train, and to make the
optimisation visible instead of assumed.

**Why this is needed at all.** `MantisTrainer.fit` computes the mean loss per
epoch, writes it to a progress bar, and discards it — no history, no validation,
no callback. So the training loop here is a faithful replica of the library's,
reusing its `FineTuningNetwork`, `LabeledDataset`, `adjust_learning_rate` and the
trainer's own `_get_fine_tuning_params`, so the parameter freezing and the
schedule stay the library's behaviour rather than a reimplementation of it. The
only additions are per-epoch logging and an evaluation pass.

**What the curves will settle.** `mantis/trainer/trainer_utils/scheduling.py`
applies a 10-epoch linear warmup then cosine decay to zero, and the warmup is
`10 * len(loader)` steps **regardless of `num_epochs`**. At the 30 epochs used
previously that is a third of training spent warming up before a steep 20-epoch
cosine; at 200 epochs it is 5%. The earlier run was therefore not "less
training" but a differently shaped schedule, and the two are not comparable as
one model trained longer. Where validation accuracy peaks under a well-shaped
schedule is an empirical question, and 200 epochs on ~1,050 training windows for
36 classes is very likely far past it.

**The inner split, and why the test set is not touched here.** Reading curves off
the test windows and then choosing an epoch budget from them is selection on
test, which would quietly inflate Stage 2. So the known drivers' *training*
portion is subdivided per driver: the first 82% trains, a one-window gap is
discarded, the last 15% validates. Windows are non-overlapping in time and the
three ranges are disjoint and contiguous, so no raw sample appears in two of
them. The gap matters because adjacent windows are nearly identical driving;
without it validation accuracy is optimistic and the chosen epoch count drifts
late. The test windows are never loaded.

Stage 2 then refits on the full training portion — inner-train, gap and
inner-val reunited — so the epoch count it inherits was chosen on a model that
saw ~18% less data. The true optimum there is slightly later. That is standard
practice after hyperparameter selection, and it is recorded rather than hidden.

Run from the repo root in the `truckidme` env. Validate the path first:
    /home/ap9107/anaconda3/envs/truckidme/bin/python \\
        -m experiments.exp04_open_set_finetune.learning_dynamics \\
        --epochs 3 --arms full

Then the real Stage 1:
    /home/ap9107/anaconda3/envs/truckidme/bin/python \\
        -m experiments.exp04_open_set_finetune.learning_dynamics
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from mantis.trainer import MantisTrainer
from mantis.trainer.trainer_utils.architecture import FineTuningNetwork
from mantis.trainer.trainer_utils.dataset import LabeledDataset
from mantis.trainer.trainer_utils.scheduling import adjust_learning_rate
from torch import nn
from torch.utils.data import DataLoader

from experiments.exp04_open_set_finetune.encoder import (BATCH_SIZE, DEVICE,
                                                         LEARNING_RATE,
                                                         build_network)
from src.config import DATA_INTERIM, OUT_FIGURES
from src.models.open_set import N_PARTITIONS, N_UNKNOWN
from src.models.splits import known_unknown_partitions, split_by_driver

EXPERIMENT_DIR = Path(__file__).resolve().parent
HISTORY_PATH = EXPERIMENT_DIR / "learning_dynamics.csv"
REPORT_PATH = EXPERIMENT_DIR / "learning_dynamics.md"
FIGURE_PATH = OUT_FIGURES / "exp04_learning_dynamics.png"

WINDOW_SECONDS = 51.2
ARMS: tuple[str, ...] = ("full", "head", "scratch")
EPOCHS = 200
SEED = 42
PARTITION_INDEX = 0          # curves describe optimisation, not a driver draw
EVAL_BATCH = 256

# fractions of each driver's *training* windows; the 3% between is the gap
INNER_TRAIN_END = 0.82
INNER_VAL_START = 0.85


def tensor_path(window_seconds: float) -> Path:
    """Where exp03 saved one window length's verified tensor.

    Args:
        window_seconds: window length.

    Returns:
        Path to the Arm B window tensor.
    """
    return DATA_INTERIM / f"windows_armB_{window_seconds:g}s.npz"


def inner_split(drivers: np.ndarray, starts: np.ndarray,
                train_index: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Subdivide the training windows per driver, discarding a gap.

    Args:
        drivers: driver id per window.
        starts: window start time per window.
        train_index: outer training positions.

    Returns:
        (inner_train_index, inner_val_index), disjoint and chronological within
        each driver.
    """
    inner_train, inner_val = [], []
    for driver in np.unique(drivers[train_index]):
        positions = train_index[drivers[train_index] == driver]
        order = np.argsort(starts[positions])
        count = len(order)
        inner_train.append(positions[order[:int(INNER_TRAIN_END * count)]])
        inner_val.append(positions[order[int(INNER_VAL_START * count):]])
    return (np.sort(np.concatenate(inner_train)),
            np.sort(np.concatenate(inner_val)))


def build_head(hidden_dim: int, num_channels: int, n_classes: int) -> nn.Module:
    """The classification head, exactly as `MantisTrainer.fit` builds it.

    Args:
        hidden_dim: encoder output width per channel.
        num_channels: raw channel count (each channel is encoded separately).
        n_classes: number of drivers to separate.

    Returns:
        BatchNorm followed by a linear layer, on DEVICE.
    """
    width = hidden_dim * num_channels
    return nn.Sequential(nn.BatchNorm1d(width),
                         nn.Linear(width, n_classes)).to(DEVICE)


def evaluate(model: nn.Module, inputs: np.ndarray,
             labels: np.ndarray) -> tuple[float, float]:
    """Accuracy and mean cross-entropy of a model on one set.

    Args:
        model: the fine-tuning network.
        inputs: raw windows, or precomputed embeddings for the 'head' arm.
        labels: integer labels.

    Returns:
        (accuracy, mean loss).
    """
    model.eval()
    predicted, total_loss = [], 0.0
    with torch.no_grad():
        for start in range(0, len(inputs), EVAL_BATCH):
            batch_x = torch.as_tensor(inputs[start:start + EVAL_BATCH],
                                      dtype=torch.float32, device=DEVICE)
            batch_y = torch.as_tensor(labels[start:start + EVAL_BATCH],
                                      dtype=torch.long, device=DEVICE)
            output = model(batch_x)
            total_loss += float(nn.functional.cross_entropy(
                output, batch_y, reduction="sum").item())
            predicted.append(output.argmax(dim=1).cpu().numpy())
    return (float(np.mean(np.concatenate(predicted) == labels)),
            total_loss / len(labels))


def train_with_history(arm: str, windows: np.ndarray, labels: np.ndarray,
                       train_index: np.ndarray, val_index: np.ndarray,
                       epochs: int) -> tuple[list[dict], float]:
    """Train one arm, recording loss, accuracy and learning rate every epoch.

    Mirrors `MantisTrainer.fit`: same head, same AdamW settings, same schedule,
    same drop-last rule. Only the logging and the validation pass are added.

    Args:
        arm: 'full', 'head' or 'scratch'.
        windows: (n_windows, n_channels, steps) tensor.
        labels: integer driver label per window.
        train_index: inner training positions.
        val_index: inner validation positions.
        epochs: training epochs.

    Returns:
        (per-epoch history rows, total minutes).
    """
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    trainer = MantisTrainer(device=DEVICE,
                            network=build_network(pretrained=(arm != "scratch")))
    trainer.fine_tuning_type = arm
    n_channels = windows.shape[1]
    head = build_head(trainer.network.hidden_dim, n_channels,
                      len(np.unique(labels[train_index])))

    # the 'head' arm trains on embeddings, so the encoder runs once rather than
    # once per epoch — exactly what fit() does for this fine-tuning type
    if arm == "head":
        train_inputs = trainer.transform(windows[train_index], batch_size=EVAL_BATCH)
        val_inputs = trainer.transform(windows[val_index], batch_size=EVAL_BATCH)
        model = FineTuningNetwork(None, head, None).to(DEVICE)
    else:
        train_inputs, val_inputs = windows[train_index], windows[val_index]
        model = FineTuningNetwork(trainer.network, head, None).to(DEVICE)

    trainer.fine_tuned_model = model
    parameters = trainer._get_fine_tuning_params(fine_tuning_type=arm)
    optimise = set(parameters)
    for _, parameter in model.named_parameters():
        parameter.requires_grad = parameter in optimise
    model.eval()
    trainer._set_train(fine_tuning_type=arm)

    optimizer = torch.optim.AdamW(parameters, lr=LEARNING_RATE,
                                  betas=(0.9, 0.999), weight_decay=0.05)
    criterion = nn.CrossEntropyLoss()

    train_labels = labels[train_index]
    val_labels = labels[val_index]
    dataset = LabeledDataset(train_inputs, train_labels)
    drop_last = len(dataset) > BATCH_SIZE and len(dataset) % BATCH_SIZE == 1
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True,
                        drop_last=drop_last)

    history, step, clock = [], 1, time.perf_counter()
    for epoch in range(1, epochs + 1):
        trainer._set_train(fine_tuning_type=arm)
        losses, correct, seen, last_lr = [], 0, 0, LEARNING_RATE
        for batch_x, batch_y in loader:
            adjust_learning_rate(epochs, optimizer, loader, step, LEARNING_RATE)
            last_lr = float(optimizer.param_groups[0]["lr"])
            batch_x = batch_x.to(DEVICE)
            batch_y = batch_y.to(DEVICE)
            step += 1
            output = model(batch_x)
            loss = criterion(output, batch_y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
            correct += int((output.argmax(dim=1) == batch_y).sum().item())
            seen += len(batch_y)

        val_accuracy, val_loss = evaluate(model, val_inputs, val_labels)
        history.append({
            "arm": arm,
            "epoch": epoch,
            "learning_rate": last_lr,
            "train_loss": float(np.mean(losses)),
            "train_accuracy": correct / max(seen, 1),
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
        })
        if epoch % 10 == 0 or epoch == 1 or epoch == epochs:
            print(f"    epoch {epoch:>4}  lr {last_lr:.2e}  "
                  f"train loss {history[-1]['train_loss']:.3f}  "
                  f"train acc {history[-1]['train_accuracy']:.1%}  "
                  f"val acc {val_accuracy:.1%}")

    return history, (time.perf_counter() - clock) / 60


def plot_history(history: list[dict], path: Path) -> Path:
    """Save the four diagnostic panels.

    Args:
        history: every epoch of every arm.
        path: output path.

    Returns:
        The written path.
    """
    arms = sorted({row["arm"] for row in history})
    figure, axes = plt.subplots(2, 2, figsize=(13, 9))
    colours = dict(zip(arms, ("tab:blue", "tab:orange", "tab:green")))

    def series(arm: str, key: str) -> tuple[list[int], list[float]]:
        rows = [r for r in history if r["arm"] == arm]
        return [r["epoch"] for r in rows], [r[key] for r in rows]

    for arm in arms:
        epochs, values = series(arm, "train_loss")
        axes[0][0].plot(epochs, values, color=colours[arm], label=f"{arm} train")
        epochs, values = series(arm, "val_loss")
        axes[0][0].plot(epochs, values, color=colours[arm], ls="--", alpha=0.7,
                        label=f"{arm} val")

        epochs, values = series(arm, "train_accuracy")
        axes[0][1].plot(epochs, values, color=colours[arm], label=f"{arm} train")
        epochs, values = series(arm, "val_accuracy")
        axes[0][1].plot(epochs, values, color=colours[arm], ls="--", alpha=0.85,
                        label=f"{arm} val")

        epochs, values = series(arm, "learning_rate")
        axes[1][0].plot(epochs, values, color=colours[arm], label=arm)

        _, train_accuracy = series(arm, "train_accuracy")
        epochs, val_accuracy = series(arm, "val_accuracy")
        axes[1][1].plot(epochs, np.array(train_accuracy) - np.array(val_accuracy),
                        color=colours[arm], label=arm)

    axes[0][0].set(title="Cross-entropy", xlabel="epoch", ylabel="loss")
    axes[0][1].set(title="Accuracy (dashed = held-out inner validation)",
                   xlabel="epoch", ylabel="top-1")
    axes[1][0].set(title="Learning rate — 10-epoch warmup, then cosine to zero",
                   xlabel="epoch", ylabel="lr")
    axes[1][1].set(title="Generalisation gap (train − val)", xlabel="epoch",
                   ylabel="top-1 difference")
    for axis in axes.ravel():
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8)

    figure.tight_layout()
    OUT_FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def build_report(history: list[dict], minutes: dict[str, float], n_known: int,
                 n_train: int, n_val: int, epochs: int) -> str:
    """Render what the curves say.

    Args:
        history: every epoch of every arm.
        minutes: arm to training minutes.
        n_known: enrolled driver count.
        n_train: inner training windows.
        n_val: inner validation windows.
        epochs: epochs trained.

    Returns:
        Markdown report.
    """
    lines = [
        "# exp04 Stage 1 — learning dynamics",
        "",
        f"One partition ({n_known} known / {N_UNKNOWN} unknown), "
        f"{WINDOW_SECONDS:g} s windows, **{epochs} epochs**, batch {BATCH_SIZE}, "
        f"base lr {LEARNING_RATE:.0e}, AdamW (betas 0.9/0.999, weight decay 0.05), "
        f"seed {SEED}. **{n_train} inner-train / {n_val} inner-val windows** over "
        f"{n_known} classes. The test windows are not loaded by this script.",
        "",
        "This is a tuning artefact, not a result. Its only output is the epoch "
        "budget Stage 2 should use.",
        "",
        "## Where each arm peaks",
        "",
        "| Arm | Best val top-1 | at epoch | Val top-1 at final epoch | Train top-1 "
        "at best | Gap at best | Minutes |",
        "|---|--:|--:|--:|--:|--:|--:|",
    ]
    recommendations = {}
    for arm in sorted({row["arm"] for row in history}):
        rows = [r for r in history if r["arm"] == arm]
        best = max(rows, key=lambda r: r["val_accuracy"])
        recommendations[arm] = best["epoch"]
        lines.append(
            f"| `{arm}` | **{best['val_accuracy']:.1%}** | {best['epoch']} | "
            f"{rows[-1]['val_accuracy']:.1%} | {best['train_accuracy']:.1%} | "
            f"{best['train_accuracy'] - best['val_accuracy']:+.1%} | "
            f"{minutes[arm]:.1f} |")

    budget = max(recommendations.get(a, 0) for a in ("full", "scratch")
                 if a in recommendations) if recommendations else epochs
    lines += [
        "",
        "## Reading this",
        "",
        "- **Best epoch vs final epoch.** If validation accuracy at the final "
        f"epoch is well below its peak, {epochs} epochs overfits and Stage 2 "
        "should stop earlier. If the two are close, the budget is not yet the "
        "binding constraint.",
        "- **The generalisation gap** is the honest measure of how much of the "
        "training accuracy is memorisation. With "
        f"{n_train} training windows over {n_known} classes "
        f"(~{n_train / max(n_known, 1):.0f} per driver), a large gap is expected; "
        "what matters is the epoch at which validation stops improving.",
        "- **The learning-rate panel** shows the library's schedule: a 10-epoch "
        "linear warmup — fixed at 10 epochs whatever `num_epochs` is — then "
        "cosine decay to zero. At 30 epochs that warmup is a third of training; "
        f"at {epochs} epochs it is {10 / epochs:.0%}. Runs at different epoch "
        "budgets are therefore differently shaped schedules, not the same model "
        "trained longer.",
        "- **`head` trains on precomputed embeddings**, so its curve shows "
        "whether the frozen representation is linearly separable at all, "
        "independently of how long the encoder is adapted.",
        "",
        "## Recommendation for Stage 2",
        "",
        f"**{budget} epochs**, taken as the later of the `full` and `scratch` "
        "peaks so neither arm is handicapped by a budget chosen for the other.",
        "",
        "Stage 2 refits on the full training portion — inner-train, gap and "
        f"inner-val reunited, about {n_train + n_val} windows — so it sees "
        f"~{n_val / max(n_train, 1):.0%} more data than was used to choose this "
        "number. The true optimum there is slightly later, which this budget does "
        "not correct for.",
        "",
        f"Full per-epoch history: `{HISTORY_PATH.name}`. "
        f"Figure: `{FIGURE_PATH.relative_to(OUT_FIGURES.parent.parent)}`.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Train every arm with logging and write the report."""
    parser = argparse.ArgumentParser(description="exp04 Stage 1")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--arms", nargs="+", default=list(ARMS), choices=ARMS)
    args = parser.parse_args()

    path = tensor_path(WINDOW_SECONDS)
    if not path.exists():
        raise FileNotFoundError(f"missing {path}; run exp03's build_tensors.py first")

    bundle = np.load(path, allow_pickle=False)
    windows, drivers, starts = bundle["X"], bundle["driver"], bundle["start_time"]

    known, _ = known_unknown_partitions(drivers, N_UNKNOWN, N_PARTITIONS,
                                        SEED)[PARTITION_INDEX]
    known_positions = np.flatnonzero(np.isin(drivers, known))
    train_local, _ = split_by_driver(drivers[known_positions],
                                     starts[known_positions])
    outer_train = known_positions[train_local]
    inner_train, inner_val = inner_split(drivers, starts, outer_train)

    if set(inner_train) & set(inner_val):
        raise ValueError("inner train and validation windows overlap")
    _, labels = np.unique(drivers[known_positions], return_inverse=True)
    full_labels = np.full(len(drivers), -1, dtype=int)
    full_labels[known_positions] = labels

    print(f"{windows.shape} tensor | {len(known)} known drivers | "
          f"inner-train {len(inner_train)} / inner-val {len(inner_val)} windows | "
          f"{args.epochs} epochs | arms {', '.join(args.arms)}")

    history, minutes = [], {}
    for arm in args.arms:
        print(f"\n  {arm}:")
        rows, elapsed = train_with_history(arm, windows, full_labels, inner_train,
                                           inner_val, args.epochs)
        history += rows
        minutes[arm] = elapsed
        best = max(rows, key=lambda r: r["val_accuracy"])
        print(f"    best val top-1 {best['val_accuracy']:.1%} at epoch "
              f"{best['epoch']} | {elapsed:.1f} min")

    keys = ("arm", "epoch", "learning_rate", "train_loss", "train_accuracy",
            "val_loss", "val_accuracy")
    HISTORY_PATH.write_text(
        ",".join(keys) + "\n"
        + "\n".join(",".join(str(row[k]) for k in keys) for row in history) + "\n")
    plot_history(history, FIGURE_PATH)
    REPORT_PATH.write_text(build_report(history, minutes, len(known),
                                        len(inner_train), len(inner_val),
                                        args.epochs))
    print(f"\nhistory -> {HISTORY_PATH}\nfigure  -> {FIGURE_PATH}\n"
          f"report  -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
