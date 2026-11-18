# exp04 — does adapting the encoder help? :: FINE-TUNING vs from SCRATCH vs FROZEN (PRE-TRAINED)

## Objective

The capstone's primary question, asked directly: **can a time-series foundation
model refuse a driver it was never enrolled on?** exp03 showed the frozen encoder
separates drivers only weakly. This experiment asks whether **adaptation**
changes that, and isolates how much of any change comes from the **pre-training**
rather than from the architecture.

It also tests two explanations for the frozen encoder's low closed-set number:
that Mantis's input normalisation throws away identity (H3), and that the
nearest-prototype read-out, not the representation, was the limit (H4).

## Hypotheses and outcomes

Fixed in `STAGE2.md` before Stage 2 ran.

| | Hypothesis | Falsified if | Outcome |
|---|---|---|---|
| H1 | Fine-tuning lifts open-set AUROC above chance | AUROC stays at chance for `full` | 🔴 **not supported here**: best driver AUROC 0.566 (`full`) vs 0.559 (`frozen`). exp07 later showed the scoring, not the encoder, was the limit (`DECISIONS.md` D12) |
| H2 | Pre-training contributes beyond the architecture: `full` > `scratch` | `full` ≈ `scratch` | 🟢 **supported**: LDA 33.2% vs 19.2% (+14.0pp), better under all three read-outs |
| H3 | Mantis's per-window normalisation discards identity; appending mean and std lifts every representation | `+ level` changes nothing | 🔴 **falsified**: LDA 28.7 → 29.0% frozen, 33.2 → 33.2% fine-tuned |
| H4 | The frozen encoder's low number was partly a read-out artefact | all read-outs agree with nearest-prototype | 🟢 **supported**: read-outs span 21–29% on the same frozen embeddings; at a matched 46-way cohort, nearest-prototype 10.6% → LDA 23.2% (exp05) |

**Why H3 was worth testing.** `mantis/architecture/version1.py:58` z-scores
every window per channel before the encoder sees it:

```python
ts_scaler = lambda x: (x - mean(x, axis=2)) / (std(x, axis=2) + 1e-5)
```

so the encoder sees **shape only** — a driver holding 45% accelerator and one
holding 20% look identical once the window is normalised, and no fine-tuning can
recover what was divided out. H3's falsification says absolute level is not
where identity lives on this data.

## Arms

| Arm | Initialisation | Training | What it isolates |
|---|---|---|---|
| `full` | pre-trained checkpoint | every parameter, on the known drivers | the adapted foundation model |
| `scratch` | random | every parameter, same windows and recipe | the architecture **without** pre-training |
| `frozen` | pre-trained checkpoint | none | the reference point |
| `head` | pre-trained checkpoint | classification head only | Stage 1 only (its embeddings equal `frozen`'s) |

`scratch` is the control without which "the foundation model works" cannot be
told apart from "a transformer works".

## Two stages

**Stage 1 — choosing the epoch budget** (`learning_dynamics.py`, inner
validation, one partition, 200 epochs, every epoch logged). Mantis's scheduler
uses a fixed 10-epoch warmup then cosine decay, so the budget changes the shape
of training, not only its length.

| Arm | Best inner-val top-1 | at epoch | Final (200) |
|---|--:|--:|--:|
| `full` | **32.2%** | 91 | 31.7% |
| `head` | 27.2% | 122 | 26.2% |
| `scratch` | 24.8% | 186 | 22.8% |

Every arm memorises the training set by epoch ~40; validation accuracy is flat
from about epoch 60, and epochs 60 and 200 are within noise. **100 epochs** was
pinned for Stage 2 (later experiments use 60, which this curve also supports).

**Stage 2 — the experiment** (`run.py`, test split, 5 partitions).

## Results — Stage 2 (`results.md`)

51.2 s windows, 36 known / 10 unknown drivers, five group-stratified partitions,
mean ± sd.

### Closed set (36-way, chance 2.8%)

| Representation | linear probe | LDA + centroid | random forest |
|---|--:|--:|--:|
| `full` | 30.1% ± 2.3 | **33.2% ± 2.7** | 31.8% ± 1.5 |
| `frozen` | 26.2% ± 1.4 | 28.7% ± 2.7 | 21.2% ± 0.8 |
| `scratch` | 19.3% ± 0.6 | 19.2% ± 1.1 | 24.4% ± 1.3 |

`+ level` rows are in `results.md`; none differs from its plain row by more than
2.4pp, and LDA by at most 0.3pp.

### Open set (driver AUROC, chance 0.500)

| Representation | best rule | driver AUROC |
|---|---|--:|
| `full` | Mahalanobis | 0.566 |
| `frozen` | ratio | 0.559 |
| `scratch` | Euclidean | 0.577 |

All five rules, all six representations: window AUROC 0.48–0.52. At this point
in the project open set looked impossible; exp07 traced it to the PCA-based
scoring used here.

### Attention read-outs (`attention_readout.md`)

Two learned read-outs that weight the 50 channels, on the frozen embeddings:

| Read-out | top-1 (36-way) | open set, driver AUROC |
|---|--:|--:|
| attention pooling | 11.3% ± 1.4 | 0.494 |
| channel self-attention | 10.9% ± 1.7 | 0.503 |
| LDA + centroid (reference) | 28.7% ± 2.7 | — |

Both lose to a flat LDA by ~17pp. With ~33 training windows per driver, a
read-out with 140–270k parameters overfits where LDA does not.

## What this experiment established

- **Pre-training matters** (H2): the same architecture trained from random
  initialisation is 14pp worse.
- **Fine-tuning helps closed set** (+4.5pp LDA over frozen here).
- **The read-out matters as much as the encoder** (H4).
- **Absolute level does not carry identity** (H3).
- **Open set was at chance — under this scoring.** Resolved in exp07.

## Superseded since

exp04's configuration was the best available when it ran. Each choice was later
re-tested:

| exp04 used | Replaced by | Where |
|---|---|---|
| `cls_token` | `mean_token` | `DECISIONS.md` D13 (exp06) |
| read-out after block 3 for both arms | block 1 for frozen; block 3 kept for fine-tuned | D14 (exp08) |
| 51.2 s for both arms | arm-specific: frozen 90 s, fine-tuned 30 s | D11, D14 |
| PCA(50) open-set scoring | LDA → L2 → whiten → cosine, pre-registered | D12 (exp07) |
| 100 epochs | 60 | exp07 |

## Data lineage (dimensions at each stage)

| Stage | What changed the shape | Shape |
|---|---|---|
| window tensor | `src/features/build_tensors.py`, 51.2 s, 50 channels, `np.interp` to 512 points | (2,267, 50, 512) |
| frozen embedding | `src/features/build_embeddings.py`, block index 2, `cls_token` | (2,267, 12,800) |
| level features | per-window per-channel mean and std | (2,267, 100) |
| partition | 36 known / 10 unknown, group-stratified, 5 partitions | ~1,774 known windows |
| outer split | known drivers' chronological 70% / 5% gap / 25% | train 1,188, test ~430 |
| Stage 1 inner split | the 70% split again | 986 / 202 |
| fine-tuned embedding | `MantisTrainer.transform` over all windows | (2,267, 12,800) |
| open-set scoring | `StandardScaler` + PCA(50), fitted on known-train | (2,267, 50) |
| closed-set read-outs | `src/models/readouts.py`; LDA preceded by PCA(200) | 12,800 → 200 → 35 |

Windows are non-overlapping and the split assigns disjoint contiguous ranges, so
no raw sample is in both train and test. Stage 1 never loads test windows.

## Configuration

| | |
|---|---|
| Drivers | 46 usable (G1S04 low CAN rate; G1S10/11/12 broken logger clock) |
| Channels | 50 (`DECISIONS.md` S1, S3) |
| Window | 51.2 s, non-overlapping; 512 / 51.2 s = 10.0 Hz, the modal native rate |
| Encoder | Mantis-8M, read-out after block 3 (index 2), `cls_token`; no channel adapter (`DECISIONS.md` B3, narrowed) |
| Training | 100 epochs, batch 64, lr 1e-4, AdamW, 10-epoch warmup then cosine, seed 42 |
| Open set | 5 rules (`euclidean`, `cosine`, `ratio`, `mahalanobis`, `msp`), `src/models/open_set.py`, earlier-rules section |
| Closed set | `src/models/readouts.py`: linear probe, LDA + centroid, random forest |

## Files

| File | What |
|---|---|
| `STAGE2.md` | pre-registration, written before Stage 2 ran |
| `learning_dynamics.py` → `learning_dynamics.md`, `.csv` | Stage 1 |
| `run.py` → `results.md` | Stage 2 |
| `encoder.py` | network construction and training constants |
| `attention_readout.py` → `attention_readout.md` | attention read-outs |
| `plots.py` | the figures below |

Figures in `outputs/figures/`: `exp04_learning_dynamics.png`, `exp04_roc.png`,
`exp04_auroc_comparison.png`, `exp04_closed_set.png`,
`exp04_embedding_geometry.png`, `exp04_attention_weights.png`.

## Commands

```bash
python -u -m experiments.exp04_open_set_finetune.learning_dynamics   # Stage 1
python -u -m experiments.exp04_open_set_finetune.run                 # Stage 2, ~3.7 h on one GPU
python -u -m experiments.exp04_open_set_finetune.attention_readout
```

## Limitations

- **One drive per driver**: an unknown driver is also an unknown day, so every
  open-set number is an upper bound on genuine behavioural rejection
  (`DECISIONS.md` C1).
- Fixed epoch budget, final epoch, no early stopping.
- Fine-tuned embeddings were not saved, so the attention read-outs ran on frozen
  embeddings only.
