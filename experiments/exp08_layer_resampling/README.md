# exp08 — re-testing early choices: read-out block and resampling

## Objective

Two choices were fixed early and never tested against alternatives: **where to
read out of the encoder** (block index 2, the Mantis paper's recommendation) and
**how to resample onto 512 points** (`np.interp`). This experiment re-tests both,
for both arms, with every decision made on inner validation under a rule written
before the run. Round 3 then describes the headline configuration from three
further angles.

Mantis numbers its six transformer blocks from 0: index 2 is the output after
**block 3**, and "final" is after block 6. Files and cells named `layer2` mean
block 3.

## The rounds

| Round | Question | Split | Rule | Outcome |
|---|---|---|---|---|
| 1 (`round1.py`) | block 3 vs final × `np.interp` vs bin averaging, both arms, 4 windows | inner validation | switch only if ≥ 2pp better | 🟢 incumbent stands: block 3, `np.interp` |
| 2 (`round2.py`) | `np.interp` vs bin averaging, fine-tuned, 5 partitions, 4 windows | test | binavg only if mean driver AUROC higher **and** ≥ 4/5 partitions improve **and** LDA not > 2pp lower | 🔴 not met (2 of 5): `np.interp` stays (`DECISIONS.md` S6) |
| layer profile (`layer_profile.py`) | all 6 blocks, frozen, 4 windows | inner validation | switch only if ≥ 2pp better at ≥ 3 of 4 windows | 🟢 **met (4 of 4): frozen moves to block 1** (D14) |
| block 1, fine-tuned (`round1.py --layer 0`, `block1_inner.py`) | block 1 vs block 3, fine-tuned, 4 windows | inner validation | same rule | 🔴 not met (2 of 4): fine-tuned stays at block 3 (D14) |
| 3 (`round3.py`) | awareness groups, operating points, enrolment size | test | none — descriptive | reported |

`block1_test.py` was written in advance to report block 1 on test if its rule
was met. It was not, so it was never run.

## Data lineage

| Stage | What | Shape |
|---|---|---|
| window tensors | `src/features/build_tensors.py` (`np.interp`) or `build_binavg_tensors.py` (bin averaging) | (n, 50, 512), n = 3,876 / 2,267 / 1,290 / 964 |
| frozen embeddings | `src/features/build_embeddings.py`, `mean_token`, every block | (n, 12,800) |
| fine-tuned embeddings | `src/models/finetune.py` recipe, read-out block as tested | (n, 12,800) |
| split | per-driver chronological 70 / 5 / 25; inner validation splits the 70% again | |
| closed set | `src/models/readouts.py`: probe, LDA + centroid, forest | 36 or 46 classes |
| open set | `src/models/open_set.py`, pre-registered scoring (D12) | driver AUROC over 5 partitions |

Bin averaging takes the mean of the raw samples in each of 512 bins and fills an
empty bin by interpolation at its centre. It changes the median channel by 0.3%
at 30 s; SPN 908 changes most (14% at 30 s, 35% at 120 s).

## Results

### Round 1 — inner validation (`round1.md`)

Fine-tuned, closed set (best read-out, 36-way): block 3 beats the final block at
every window (best 47.8% vs 42.4%). The rule compares each cell's best window:
bin averaging's (47.6%) does not beat `np.interp`'s (47.8%), although at 90 s
alone it is 2.6pp ahead. The incumbent — block 3, `np.interp` — stands.

### Round 2 — resampling on test (`round2.md`)

| Window | LDA, binavg − interp | driver AUROC, binavg − interp | partitions improved |
|--:|--:|--:|--:|
| **30 s** | +1.3pp | +0.018 | 2 of 5 |
| 51.2 s | −2.1pp | −0.051 | 1 of 5 |
| 90 s | −0.9pp | −0.024 | 2 of 5 |
| 120 s | +4.2pp | −0.041 | 2 of 5 |

Bin averaging's higher mean at 30 s rests on one partition. `np.interp` stays.

### Layer profile — frozen, inner validation (`layer_profile.md`)

46-way LDA:

| Block | 30 s | 51.2 s | 90 s | 120 s |
|---|--:|--:|--:|--:|
| **1 of 6** | **30.1%** | **38.5%** | **43.4%** | 38.8% |
| 2 of 6 | 27.9% | 34.9% | 42.1% | **44.4%** |
| 3 of 6 (incumbent) | 26.5% | 33.4% | 38.0% | 36.0% |
| 4 of 6 | 24.9% | 29.8% | 33.1% | 32.0% |
| 5 of 6 | 21.9% | 25.9% | 27.3% | 27.5% |
| 6 of 6 (final) | 20.3% | 24.1% | 24.8% | 23.6% |

Accuracy falls with depth at every window. Block 1 beats block 3 by 2.8–5.4pp
at all four windows: the frozen arm moves to block 1, and its window, re-chosen
on the same inner validation, is 90 s. Block 3 reproduces exp06's
`confirm_token.md` exactly.

### Block 1 for the fine-tuned arm — inner validation (`block1_inner.md`)

| Window | training windows | block 3 | block 1 |
|--:|--:|--:|--:|
| **30 s** | 1,462 | **47.8%** | 34.7% |
| 51.2 s | 840 | 39.9% | 44.2% |
| 90 s | 462 | 45.0% | 45.5% |
| 120 s | 341 | 38.4% | 45.7% |

Block 1 wins at 2 of 4 windows and never reaches block 3's best: the
fine-tuned arm stays at block 3, 30 s. The same report shows what fine-tuning
adds at a matched block and window — up to +17.9pp where training windows are
plentiful, and a loss at 90–120 s where they are scarce.

### Round 3 — the headline configuration from three angles (`round3.md`)

Fine-tuned block 3, 30 s, five partitions, test. The frozen columns of this
round use the same configuration (block 3, 30 s), not the frozen arm's own.

**Awareness groups** (closed set, LDA, 36-way): G1 44.2%, G2 45.0%, G3 46.3% —
no group is harder to name. Open set within each group: G2 strangers are the
easiest to reject (driver AUROC 0.847), G1 the hardest (0.601).

**Operating points** (strangers as the positive class):

| level | AUROC | AUPR | EER | strangers accepted at 95% enrolled accepted |
|---|--:|--:|--:|--:|
| window | 0.585 | 0.263 | 0.444 | 93.6% |
| driver | 0.689 | 0.450 | 0.341 | 82.0% |

At an operating point that accepts 95% of enrolled drivers, most strangers are
still accepted: the open-set separation is real but weak.

**Enrolment size** (frozen, the clean curve): top-1 18.4% → 24.3% → 28.7% →
30.5% with 25 / 50 / 75 / 100% of each driver's training windows. Still rising
at 100%: more enrolment data would help.

## Files

| File | What |
|---|---|
| `build_binavg_tensors.py` | bin-averaged tensors, aligned row for row with the `np.interp` ones |
| `round1.py` → `cells/*.json` → `summarise.py` → `round1.md` | Round 1 |
| `round2.py` → `round2_cells/*.json` → `round2.md` | Round 2 |
| `round3.py` → `round3.md` | Round 3 |
| `layer_profile.py` → `layer_profile_cells/*.json` → `layer_profile.md` | frozen block profile |
| `block1_inner.py` → `block1_inner.md` | fine-tuned block-1 decision (reads `cells/layer0_interp.json`) |
| `block1_test.py` | written in advance; **not run** (rule not met) |
| `run_round1.sh`, `run_round2.sh` | two-GPU launchers |

## Commands

```bash
python -m experiments.exp08_layer_resampling.build_binavg_tensors

nohup bash experiments/exp08_layer_resampling/run_round1.sh > outputs/logs/exp08_round1.log 2>&1 &
python -m experiments.exp08_layer_resampling.summarise
nohup bash experiments/exp08_layer_resampling/run_round2.sh > outputs/logs/exp08_round2_launcher.log 2>&1 &
python -m experiments.exp08_layer_resampling.round3

python -u -m experiments.exp08_layer_resampling.layer_profile --window 30 --window 51.2
python -u -m experiments.exp08_layer_resampling.layer_profile --window 90 --window 120
python -u -m experiments.exp08_layer_resampling.layer_profile --summarise

python -u -m experiments.exp08_layer_resampling.round1 --layer 0 --resampling interp
python -u -m experiments.exp08_layer_resampling.block1_inner
```

## Limitations

- **Round 1 and the block-1 fine-tuned comparison use one partition** (GPU
  cost); the frozen layer profile uses all five.
- **The block profile is `mean_token` only.**
- **Round 3's frozen columns use block 3, 30 s**, the matched configuration,
  not the frozen arm's own (block 1, 90 s).
- **Driver AUROC is unstable between splits**: frozen block 1, 90 s scores 0.611
  on inner validation and 0.717 on test (exp06 README).
- **One drive per driver.** See `DECISIONS.md` C1.
