"""Channel attention as a fourth read-out on frozen Mantis embeddings.

## Why this exists

`MantisTrainer.transform` applies the encoder to each of the 50 channels
*independently* and concatenates the results (`mantis/trainer.py`, `transform`),
so the 12,800-dim embedding is **channel-major**: 50 blocks of 256. Nothing in
the pipeline ever mixes channels. The read-outs that consume it then do:

    BatchNorm1d(12800) + Linear(12800, 36)      # exp04's `full`/`scratch` head
    LogisticRegression on 12,800 features       # linear_probe
    PCA(200) -> LDA -> nearest centroid         # lda_centroid
    RandomForest on 12,800 features             # random_forest

The three linear read-outs can learn a *static* weight per (channel, dim), but
they cannot weight a channel **according to the window's content** — "the brake
channels matter here, because this driver is braking". Attention can.

## What this tests, and what it separates

Two mechanisms are often conflated when people say "add attention":

- `pool`     — input-dependent channel *weighting* only. A learned query scores
               the 50 channel tokens, softmax, weighted sum of values.
- `selfattn` — weighting **plus** cross-channel *interaction*: tokens exchange
               information before pooling, so conjunctions ("accelerator high
               AND brake pressure high") become representable.

Running both separates them. If `pool` ≈ `selfattn`, interactions are not the
missing ingredient and the gain is purely adaptive weighting.

## The prior is not favourable

A random forest represents conjunctions by construction — a root-to-leaf path is
an AND of conditions — and on frozen embeddings it scored **21.2%**, the *worst*
of the three read-outs, 7.5pp below `lda_centroid`'s 28.7%. That is evidence
against cross-channel interaction being what the linear read-outs are missing.
The defence for running this anyway is that the forest hunts conjunctions among
12,800 scalars, sampling ~113 per split, whereas attention operates on 50
structured tokens. The search spaces are not comparable, so the forest's failure
does not settle the question — but it does lower the expected gain.

## This is not extra capacity

| Head | Parameters |
|---|--:|
| `BatchNorm1d(12800) + Linear(12800, 36)` (incumbent) | 486,436 |
| `pool` | 141,604 |
| `selfattn` | 272,932 |

Both variants are *smaller* than the head they are compared against. That matters
because Stage 1 showed the binding constraint is training-set size (100% train
accuracy by epoch 40, ~+70pp generalisation gap), so a read-out that adds
parameters would be the wrong move. These reallocate them instead. The exact
counts are printed at runtime rather than trusted from this docstring.

## Scope, and the limitation that comes with it

**Frozen embeddings only.** The `full` arm's adapted embeddings were never
persisted (`MantisTrainer.fit` has no checkpointing — verified: no `torch.save`),
so an attention read-out on adapted features would cost another ~3.7 h of
refitting. Everything here therefore measures attention against the *frozen*
row of `results.md`, which is the clean H4 test and needs no new tensors.

Data lineage is **identical** to `run.py`: the same cached
`embeddings_armB_51.2s.npz`, the same five group-stratified 36/10 partitions at
seed 42, the same chronological 70/5/25 within-driver split, the same
`evaluate_partition` scoring. Only the read-out changes, which is exactly the
H4 axis — so this extends exp04 rather than starting a new experiment.

## Open set

Expect nothing. Four of the five rejection rules are calibration-free distances,
and `scratch` (random initialisation) already ties `full` at 0.516 vs 0.514, so
the open-set null is a property of the embedding geometry rather than of the
read-out. It is scored here because it is free, not because it is the hypothesis.

## Commands

```bash
python -u -m experiments.exp04_open_set_finetune.attention_readout
python -u -m experiments.exp04_open_set_finetune.attention_readout --variant selfattn
python -u -m experiments.exp04_open_set_finetune.attention_readout --variant both
```
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
from sklearn.preprocessing import StandardScaler
from torch import nn

from src.config import OUT_FIGURES
from src.models.open_set import (N_PARTITIONS, N_UNKNOWN, evaluate_partition,
                                 summarise)
from src.models.splits import (driver_group, known_unknown_partitions,
                               split_by_driver)
from src.models.splits import known_train_index
from src.features.build_embeddings import embedding_path as frozen_embedding_path

WINDOW_SECONDS = 51.2
HIDDEN_DIM = 256              # Mantis embedding width per channel
SEED = 42
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
HEAD_KS = (1, 2)

# Fixed budget, final epoch, no early stopping and no best-epoch selection —
# the same protocol as the rest of exp04, so the comparison against
# linear_probe / lda_centroid / random_forest is like-for-like. 200 epochs costs
# seconds here because the encoder is frozen and only the head trains.
EPOCHS = 200
BATCH_SIZE = 64

# 1e-3, not the 1e-4 used in `encoder.py`. That value is for nudging an 8.1M
# parameter *pre-trained* encoder; this is a randomly initialised 142k head,
# where 1e-4 would still be mid-warmup at the end of the budget. Stated as a
# deliberate deviation rather than silently inherited.
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-2

VARIANTS = ("pool", "selfattn")
RESULTS_PATH = Path(__file__).parent / "attention_readout.md"
ATTENTION_FIGURE = OUT_FIGURES / "exp04_attention_weights.png"
TOP_CHANNELS = 15


class AttentionPool(nn.Module):
    """Input-dependent channel weighting over Mantis's per-channel embeddings.

    A single learned query scores the 50 channel tokens; the softmax over those
    scores is the attention weight, and the output is the weighted sum of value
    projections. No token-to-token interaction, so this isolates *weighting*.
    """

    def __init__(self, hidden_dim: int, n_classes: int) -> None:
        """Build the head.

        Args:
            hidden_dim: embedding width per channel.
            n_classes: number of known drivers.
        """
        super().__init__()
        self.norm = nn.LayerNorm(hidden_dim)
        self.key = nn.Linear(hidden_dim, hidden_dim)
        self.value = nn.Linear(hidden_dim, hidden_dim)
        self.query = nn.Parameter(torch.randn(hidden_dim) * hidden_dim ** -0.5)
        self.classifier = nn.Linear(hidden_dim, n_classes)
        self.scale = hidden_dim ** -0.5

    def forward(self, tokens: torch.Tensor
                ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Weight, pool and classify the channel tokens.

        Args:
            tokens: (batch, n_channels, hidden_dim).

        Returns:
            (logits, attention weights of shape (batch, n_channels),
            pooled representation of shape (batch, hidden_dim)).
        """
        normed = self.norm(tokens)
        scores = (self.key(normed) @ self.query) * self.scale
        weights = torch.softmax(scores, dim=1)
        pooled = (weights.unsqueeze(-1) * self.value(normed)).sum(dim=1)
        return self.classifier(pooled), weights, pooled


class ChannelSelfAttention(nn.Module):
    """Cross-channel interaction, then mean pooling.

    Tokens attend to each other before pooling, so a conjunction of two channels
    is representable. Compared against `AttentionPool` this isolates the value
    of *interaction* over and above adaptive weighting.
    """

    def __init__(self, hidden_dim: int, n_classes: int) -> None:
        """Build the head.

        Args:
            hidden_dim: embedding width per channel.
            n_classes: number of known drivers.
        """
        super().__init__()
        self.norm = nn.LayerNorm(hidden_dim)
        self.query = nn.Linear(hidden_dim, hidden_dim)
        self.key = nn.Linear(hidden_dim, hidden_dim)
        self.value = nn.Linear(hidden_dim, hidden_dim)
        self.out = nn.Linear(hidden_dim, hidden_dim)
        self.classifier = nn.Linear(hidden_dim, n_classes)
        self.scale = hidden_dim ** -0.5

    def forward(self, tokens: torch.Tensor
                ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Mix the channel tokens, pool and classify.

        Args:
            tokens: (batch, n_channels, hidden_dim).

        Returns:
            (logits, mean attention received per channel, pooled representation).
        """
        normed = self.norm(tokens)
        scores = (self.query(normed) @ self.key(normed).transpose(1, 2)) * self.scale
        weights = torch.softmax(scores, dim=-1)
        mixed = self.out(weights @ self.value(normed)) + tokens
        pooled = mixed.mean(dim=1)
        return self.classifier(pooled), weights.mean(dim=1), pooled


def build_head(variant: str, n_classes: int) -> nn.Module:
    """Create one read-out variant.

    Args:
        variant: 'pool' or 'selfattn'.
        n_classes: number of known drivers.

    Returns:
        The head, on DEVICE.
    """
    head = (AttentionPool(HIDDEN_DIM, n_classes) if variant == "pool"
            else ChannelSelfAttention(HIDDEN_DIM, n_classes))
    return head.to(DEVICE)


def load_tokens() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load frozen embeddings and reshape them into channel tokens.

    `transform` concatenates each channel's embedding along axis 1 in channel
    order, so the 12,800-dim vector is channel-major and reshaping to
    (n_channels, hidden_dim) recovers the per-channel tokens exactly.

    Returns:
        (tokens of shape (n_windows, n_channels, hidden_dim), driver id per
        window, start time per window, channel names).
    """
    cached = np.load(frozen_embedding_path("cls_token", WINDOW_SECONDS),
                     allow_pickle=True)
    embeddings = cached["E"]
    channels = cached["channels"]
    n_channels = len(channels)
    if embeddings.shape[1] != n_channels * HIDDEN_DIM:
        raise ValueError(f"expected {n_channels} x {HIDDEN_DIM} = "
                         f"{n_channels * HIDDEN_DIM} features, "
                         f"got {embeddings.shape[1]}")
    tokens = embeddings.reshape(len(embeddings), n_channels, HIDDEN_DIM)
    return tokens, cached["driver"], cached["start_time"], channels


def standardise(tokens: np.ndarray, train_index: np.ndarray) -> np.ndarray:
    """Z-score every (channel, dim) feature using known-train windows only.

    Args:
        tokens: (n_windows, n_channels, hidden_dim).
        train_index: positions of this partition's known-train windows.

    Returns:
        Standardised tokens, same shape.
    """
    flat = tokens.reshape(len(tokens), -1)
    scaler = StandardScaler().fit(flat[train_index])
    return scaler.transform(flat).reshape(tokens.shape).astype(np.float32)


def train_head(variant: str, tokens: np.ndarray, labels: np.ndarray,
               train_index: np.ndarray, num_epochs: int
               ) -> tuple[nn.Module, int, float]:
    """Fit one attention read-out on one partition's known-train windows.

    Args:
        variant: 'pool' or 'selfattn'.
        tokens: standardised tokens for every window.
        labels: integer driver label per window (valid on train_index).
        train_index: positions of the known-train windows.
        num_epochs: fixed training budget; the final epoch's weights are used.

    Returns:
        (fitted head, trainable parameter count, training seconds).
    """
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    head = build_head(variant, n_classes=int(labels[train_index].max()) + 1)
    n_params = sum(p.numel() for p in head.parameters() if p.requires_grad)

    x = torch.from_numpy(tokens[train_index]).to(DEVICE)
    y = torch.from_numpy(labels[train_index].astype(np.int64)).to(DEVICE)

    optimiser = torch.optim.AdamW(head.parameters(), lr=LEARNING_RATE,
                                  weight_decay=WEIGHT_DECAY)
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser,
                                                          T_max=num_epochs)
    loss_fn = nn.CrossEntropyLoss()
    generator = torch.Generator().manual_seed(SEED)

    clock = time.perf_counter()
    head.train()
    for _ in range(num_epochs):
        order = torch.randperm(len(x), generator=generator).to(DEVICE)
        for start in range(0, len(order), BATCH_SIZE):
            batch = order[start:start + BATCH_SIZE]
            optimiser.zero_grad()
            logits, _, _ = head(x[batch])
            loss_fn(logits, y[batch]).backward()
            optimiser.step()
        schedule.step()
    seconds = time.perf_counter() - clock

    return head, n_params, seconds


@torch.no_grad()
def apply_head(head: nn.Module, tokens: np.ndarray
               ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run a fitted head over every window.

    Args:
        head: fitted read-out.
        tokens: standardised tokens for every window.

    Returns:
        (logits, attention weights, pooled representation), all numpy.
    """
    head.eval()
    logits, weights, pooled = [], [], []
    for start in range(0, len(tokens), 256):
        chunk = torch.from_numpy(tokens[start:start + 256]).to(DEVICE)
        chunk_logits, chunk_weights, chunk_pooled = head(chunk)
        logits.append(chunk_logits.cpu().numpy())
        weights.append(chunk_weights.cpu().numpy())
        pooled.append(chunk_pooled.cpu().numpy())
    return (np.concatenate(logits), np.concatenate(weights),
            np.concatenate(pooled))


def rank_accuracy(scores: np.ndarray, classes: np.ndarray, truth: np.ndarray,
                  ks: tuple[int, ...]) -> dict[int, float]:
    """Top-k accuracy from a higher-is-better score matrix.

    Args:
        scores: (n_queries, n_classes), larger means more likely.
        classes: class labels aligned with the score columns.
        truth: true label per query.
        ks: the k values to report.

    Returns:
        {k: accuracy}.
    """
    ranking = classes[np.argsort(-scores, axis=1)]
    return {k: float(np.mean([t in row[:k] for t, row in zip(truth, ranking)]))
            for k in ks}


def run_partition(variant: str, tokens: np.ndarray, drivers: np.ndarray,
                  starts: np.ndarray, known: np.ndarray, unknown: np.ndarray,
                  num_epochs: int) -> dict:
    """Train and score one attention read-out on one partition.

    Args:
        variant: 'pool' or 'selfattn'.
        tokens: raw (unstandardised) channel tokens for every window.
        drivers: driver id per window.
        starts: window start time per window.
        known: driver ids treated as enrolled.
        unknown: driver ids never enrolled.
        num_epochs: fixed training budget.

    Returns:
        Closed-set accuracies from the head, the open-set result dict for the
        pooled representation, the attention weights, and cost.
    """
    train_index = known_train_index(drivers, starts, known)
    scaled = standardise(tokens, train_index)

    # integer labels, defined on the known drivers and aligned with the head's
    # output columns; -1 elsewhere so a mistake would raise rather than silently
    # train on an unknown driver
    known_ids = np.unique(drivers[train_index])
    labels = np.full(len(drivers), -1, dtype=np.int64)
    for code, driver in enumerate(known_ids):
        labels[drivers == driver] = code

    head, n_params, seconds = train_head(variant, scaled, labels, train_index,
                                         num_epochs)
    logits, weights, pooled = apply_head(head, scaled)

    positions = np.flatnonzero(np.isin(drivers, known))
    _, test_local = split_by_driver(drivers[positions], starts[positions])
    test_index = positions[test_local]
    closed = rank_accuracy(logits[test_index], known_ids, drivers[test_index],
                           HEAD_KS)

    open_set = evaluate_partition(pooled, drivers, starts, known, unknown)

    return {"closed": closed, "open": open_set, "weights": weights,
            "n_params": n_params, "seconds": seconds}


def plot_attention(weights: np.ndarray, drivers: np.ndarray,
                   channels: np.ndarray) -> None:
    """Draw mean attention per channel, overall and per awareness group.

    Args:
        weights: (n_windows, n_channels) attention weights from one partition.
        drivers: driver id per window.
        channels: channel names in token order.
    """
    overall = weights.mean(axis=0)
    order = np.argsort(-overall)[:TOP_CHANNELS][::-1]
    groups = sorted({driver_group(d) for d in drivers})

    figure, axes = plt.subplots(1, 2, figsize=(13, 6))
    uniform = 1.0 / len(channels)

    axes[0].barh(range(len(order)), overall[order], color="#4C72B0")
    axes[0].axvline(uniform, color="#C44E52", linestyle="--",
                    label=f"uniform ({uniform:.3f})")
    axes[0].set_yticks(range(len(order)))
    axes[0].set_yticklabels([f"SPN {channels[i]}" for i in order], fontsize=9)
    axes[0].set_xlabel("mean attention weight")
    axes[0].set_title(f"Top {TOP_CHANNELS} channels by attention")
    axes[0].legend(fontsize=9)

    width = 0.8 / len(groups)
    for offset, group in enumerate(groups):
        member = np.array([driver_group(d) == group for d in drivers])
        axes[1].barh(np.arange(len(order)) + offset * width,
                     weights[member].mean(axis=0)[order], height=width,
                     label=group)
    axes[1].set_yticks(np.arange(len(order)) + 0.4 - width / 2)
    axes[1].set_yticklabels([f"SPN {channels[i]}" for i in order], fontsize=9)
    axes[1].set_xlabel("mean attention weight")
    axes[1].set_title("By awareness group")
    axes[1].legend(fontsize=9)

    figure.suptitle("Channel attention on frozen Mantis embeddings "
                    "(partition 1, 51.2 s windows)")
    figure.tight_layout()
    figure.savefig(ATTENTION_FIGURE, dpi=150)
    plt.close(figure)


def write_report(summaries: dict[str, dict], closed: dict[str, dict],
                 costs: dict[str, tuple[int, float]], n_channels: int) -> None:
    """Write the results report next to the other exp04 reports.

    Args:
        summaries: {variant: summarise(...) output} for the open-set scores.
        closed: {variant: {k: (mean, std)}} closed-set accuracies.
        costs: {variant: (parameter count, mean training seconds)}.
        n_channels: number of channels, for the uniform-attention reference.
    """
    lines = [
        "# exp04 — channel attention as a fourth read-out",
        "",
        f"Frozen Mantis embeddings reshaped to **{n_channels} channel tokens x "
        f"{HIDDEN_DIM} dims** and pooled by attention, instead of being consumed "
        "as one flat 12,800-dim vector. Same cached embeddings, same five "
        f"36-known/10-unknown partitions, same chronological split, same "
        "scoring as `results.md`; **only the read-out changes**, which is the H4 "
        "axis. Values are mean +/- sd across partitions.",
        "",
        "`pool` applies input-dependent channel *weighting* only. `selfattn` adds "
        "cross-channel *interaction*. Comparing them separates the two mechanisms.",
        "",
        "## Closed set — naming the enrolled drivers",
        "",
        "36-way, random floor 2.8%. The incumbent read-outs on the **same frozen "
        "embeddings** are `linear_probe` 26.2% +/- 1.4, `lda_centroid` 28.7% "
        "+/- 2.7, `random_forest` 21.2% +/- 0.8.",
        "",
        "| Read-out | top-1 | top-2 | parameters | train s/partition |",
        "|---|--:|--:|--:|--:|",
    ]
    for variant, accuracy in closed.items():
        n_params, seconds = costs[variant]
        lines.append(
            f"| `{variant}` | **{accuracy[1][0] * 100:.1f}%** +/- "
            f"{accuracy[1][1] * 100:.1f}% | {accuracy[2][0] * 100:.1f}% "
            f"+/- {accuracy[2][1] * 100:.1f}% | {n_params:,} | {seconds:.1f} |")
    lines += [
        "| `linear_probe` (incumbent) | 26.2% +/- 1.4% | 38.4% | 460,836 | — |",
        "| `lda_centroid` (incumbent) | 28.7% +/- 2.7% | 41.2% | — | — |",
        "| `random_forest` (incumbent) | 21.2% +/- 0.8% | 35.1% | — | — |",
        "",
        "## Open set — rejecting the never-enrolled",
        "",
        "AUROC on the pooled representation; **0.500 is chance**. The frozen "
        "flat-embedding reference is 0.514 (`mahalanobis`), and `scratch` — a "
        "randomly initialised encoder — reaches 0.516, so this column is "
        "reported for completeness and was not expected to move.",
        "",
        "| Variant | `euclidean` | `cosine` | `ratio` | `mahalanobis` | `msp` |",
        "|---|--:|--:|--:|--:|--:|",
    ]
    rules = ("euclidean", "cosine", "ratio", "mahalanobis", "msp")
    for variant, summary in summaries.items():
        cells = " | ".join(
            f"{summary[f'auroc:{rule}'][0]:.3f} +/- "
            f"{summary[f'auroc:{rule}'][1]:.3f}" for rule in rules)
        lines.append(f"| `{variant}` | {cells} |")
    lines += [
        "",
        "Driver-level AUROC (median score per driver):",
        "",
        "| Variant | best rule | driver AUROC |",
        "|---|---|--:|",
    ]
    for variant, summary in summaries.items():
        best = max(rules, key=lambda r: summary[f"driver_auroc:{r}"][0])
        lines.append(f"| `{variant}` | `{best}` | "
                     f"**{summary[f'driver_auroc:{best}'][0]:.3f}** +/- "
                     f"{summary[f'driver_auroc:{best}'][1]:.3f} |")
    lines += [
        "",
        "That 'best rule' column is a maximum over five rules and is therefore "
        "optimistically biased — in `results.md` the random-initialisation arm "
        "wins it. Read the per-rule means above instead.",
        "",
        "## Figure",
        "",
        f"- `{ATTENTION_FIGURE}` — mean attention weight per channel, overall "
        f"and split by awareness group. Uniform attention would be "
        f"{1.0 / n_channels:.3f}; distance from that line is how much the head "
        "concentrates on particular signals.",
        "",
        "## Limitations",
        "",
        "- **Frozen embeddings only.** The adapted (`full`) embeddings were never "
        "persisted, so attention on top of a fine-tuned encoder is untested.",
        "- **Fixed 200-epoch budget, final epoch, no model selection**, matching "
        "the rest of exp04. No early stopping and no best-epoch cherry-picking, "
        "which also forgoes the ~1pp a smoothed-accuracy rule would buy.",
        "- **The attention weights are descriptive, not causal.** A channel "
        "receiving high weight is one this head found useful given the other 49; "
        "it is not evidence that the channel is independently identity-bearing.",
        "- One drive per driver, so an unknown driver is also an unknown day. "
        "See `DECISIONS.md` C1.",
    ]
    RESULTS_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Train and score the attention read-outs across all partitions."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=(*VARIANTS, "both"), default="pool")
    parser.add_argument("--partitions", type=int, default=N_PARTITIONS)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    arguments = parser.parse_args()
    variants = VARIANTS if arguments.variant == "both" else (arguments.variant,)

    tokens, drivers, starts, channels = load_tokens()
    print(f"{tokens.shape} channel tokens | {len(np.unique(drivers))} drivers "
          f"| device {DEVICE} | {arguments.epochs} epochs | variants {variants}")

    partitions = known_unknown_partitions(drivers, n_unknown=N_UNKNOWN,
                                          n_partitions=arguments.partitions,
                                          seed=SEED)

    open_rows: dict[str, list[dict]] = {v: [] for v in variants}
    closed_rows: dict[str, list[dict]] = {v: [] for v in variants}
    seconds: dict[str, list[float]] = {v: [] for v in variants}
    n_params: dict[str, int] = {}
    first_weights: np.ndarray | None = None

    for index, (known, unknown) in enumerate(partitions, start=1):
        print(f"\npartition {index}/{len(partitions)} "
              f"({len(known)} known / {len(unknown)} unknown)")
        for variant in variants:
            result = run_partition(variant, tokens, drivers, starts,
                                   known, unknown, arguments.epochs)
            open_rows[variant].append(result["open"])
            closed_rows[variant].append(result["closed"])
            seconds[variant].append(result["seconds"])
            n_params[variant] = result["n_params"]
            best = max(("euclidean", "cosine", "ratio", "mahalanobis", "msp"),
                       key=lambda r: result["open"]["auroc"][r])
            print(f"  {variant:9s} top-1 {result['closed'][1] * 100:5.1f}%  "
                  f"AUROC {result['open']['auroc'][best]:.3f} ({best})  "
                  f"{result['n_params']:,} params  {result['seconds']:.1f}s")
            if index == 1 and variant == "pool":
                first_weights = result["weights"]

    summaries = {v: summarise(open_rows[v]) for v in variants}
    closed = {v: {k: (float(np.mean([row[k] for row in closed_rows[v]])),
                      float(np.std([row[k] for row in closed_rows[v]])))
                  for k in HEAD_KS} for v in variants}

    if first_weights is not None:
        plot_attention(first_weights, drivers, channels)
        print(f"\nfigure -> {ATTENTION_FIGURE}")

    costs = {v: (n_params[v], float(np.mean(seconds[v]))) for v in variants}
    write_report(summaries, closed, costs, n_channels=tokens.shape[1])
    print(f"results -> {RESULTS_PATH}")
    for variant in variants:
        print(f"  {variant:9s} top-1 {closed[variant][1][0] * 100:.1f}% "
              f"+/- {closed[variant][1][1] * 100:.1f}%")


if __name__ == "__main__":
    main()
