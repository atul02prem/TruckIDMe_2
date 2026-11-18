# exp07 — fine-tuned Mantis, end to end: window, closed set, open set

This is the project's headline experiment. It fine-tunes Mantis-8M on the
enrolled drivers, measures closed-set identification (naming a known driver)
and open-set rejection (refusing a driver who was never enrolled), and records
how each configuration choice was made so that no headline number was chosen
on the test split.

## Where this experiment stands after exp08

exp07 produced the fine-tuned arm's headline numbers, and they stand: exp08
re-tested resampling and the read-out block for this arm, and neither rule was
met. exp08 did change the **frozen** arm — read out after block 1, at 90 s, it
matches the fine-tuned arm (`DECISIONS.md` D14). The frozen rows in Phases D and
E below use the *same* configuration as the fine-tuned arm, which isolates what
fine-tuning adds at that configuration; they are not the frozen arm's best.

| Arm | Configuration | Closed set, 46-way | Open set, driver AUROC |
|---|---|--:|--:|
| fine-tuned | block 3, 30 s | 43.1% ± 0.9 (Phase E) | 0.689 ± 0.043 (Phase C) |
| frozen | block 1, 90 s | 44.9% | 0.717 ± 0.069 |

The frozen row comes from exp06's grid. Comparable within error bars; the
frozen open-set number is the less stable of the two (exp06 README).

## Fixed configuration

| | | Chosen in |
|---|---|---|
| Encoder | Mantis-8M, pre-trained, read out after block 3 of 6 (index 2) | exp03; kept for this arm in exp08 (`DECISIONS.md` D14) |
| Output token | `mean_token` | exp06, inner validation |
| Channels | audited 50 | `DECISIONS.md` S3 |
| Resampling | `np.interp` to 512 points | exp03; kept after exp08 Round 2 (S6) |
| Fine-tuning | all 8,590,372 parameters, 60 epochs, lr 1e-4, batch 64, seed 42 | — |
| Split | per-driver chronological: first 70% train, 5% gap, last 25% test | `src/models/splits.py` |
| Open-set partitions | 5 group-stratified draws of 36 enrolled / 10 strangers, seed 42 | exp04 |

## How each choice was protected from the test split

Every selection happened on **inner validation**: the training windows split
again (70/5/25 per driver), with the test windows never scored. Only after a
choice was fixed was it evaluated once on test.

| Phase | Chooses | Selected on |
|---|---|---|
| A | window length for the fine-tuned arm | inner validation |
| C (sweep) | open-set scoring configuration | inner validation, then fixed in writing before C (final) |
| B, C (final), D, E | nothing — they only report | test |

## Data lineage (dimensions at each stage)

| Stage | What | Shape |
|---|---|---|
| exp03 tensor | 50 channels, 30 s windows, 512 points (17.07 Hz) | (3,876, 50, 512) |
| fine-tuning set | enrolled drivers' training windows | ~2,100 (36 drivers) or 2,691 (46) |
| encoder output | 50 channels × 256 (`mean_token`) | (3,876, 12,800) |
| closed-set read-out | linear probe / LDA + centroid / random forest | 36 or 46 classes |
| open-set scoring | standardise → LDA projection (35 dims) → L2-normalise → whiten → cosine distance to nearest driver mean | one score per window |
| driver-level open set | median score over a driver's test windows | 46 points per partition |

## Results

### Phase A — the best window depends on whether the encoder is fine-tuned

Inner validation, one partition, 36-way:

| Window | Inner-train windows | Fine-tuned, best read-out |
|---|--:|--:|
| **30 s** | 1,462 | **47.8%** |
| 51.2 s | 840 | 39.9% |
| 90 s | 462 | 45.0% |
| 120 s | 341 | 38.4% |

| | Ranking |
|---|---|
| frozen (exp06) | 90 > 120 > 51.2 > **30** |
| fine-tuned | **30** > 90 > 51.2 > 120 |

The frozen encoder's worst window is the fine-tuned encoder's best. Fine-tuning
is limited by the number of training windows — 30 s gives four times as many as
120 s — while frozen read-outs prefer longer, smoother windows. **30 s chosen**,
2.8pp clear of the next.

### Phase B — closed set, 36-way, five partitions (test)

| Read-out | Top-1 |
|---|--:|
| linear probe | 42.9% ± 1.6 |
| **LDA + centroid** | **45.3% ± 2.6** |
| random forest | 26.9% ± 2.0 |

Chance is 2.8%. For reference, exp04's fine-tuned arm (`cls_token`, 51.2 s, same
partitions) reached 33.2% ± 2.7 with LDA. Fine-tuning took 22.7 min per
partition. Embeddings are saved per partition so open-set scoring needs no
refit.

### Phase C — open set: the scoring, not the encoder, was the limit

**The sweep** (`phase_c_sweep.md`) tried 1,300 scoring configurations on inner
validation: 10 projections (PCA at 5–100 dimensions, and LDA) × 5 transforms ×
4 prototype types × 13 scoring rules. Judged by the **median** across all
configurations sharing a setting — far more stable than the single best cell:

| Step | Best setting | Median driver AUROC | Runner-up |
|---|---|--:|---|
| projection | **LDA** | 0.667 | PCA 100: 0.574 |
| transform | **L2-normalise then whiten** | 0.561 | whiten then L2: 0.539 |
| prototype | **one mean per driver** | 0.571 | median: 0.564 |
| scoring rule | **cosine distance** | 0.610 | classifier confidence: 0.598 |

Standard out-of-distribution detectors all scored below 0.50 on the median:
nearest-neighbour distance 0.456, local outlier factor 0.485, isolation forest
0.465, one-class SVM 0.415. Several prototypes per driver (k-means) did not help.

**The pre-registered configuration** — LDA, L2-normalise then whiten, mean
prototype, cosine — was written down before any test window was scored.

**On test** (`phase_c_final.md`), five partitions, same fine-tuned embeddings:

| Scoring | Window AUROC | Driver AUROC |
|---|--:|--:|
| exp04's scoring (PCA 50, raw, Mahalanobis) | 0.511 | 0.514 ± 0.062 |
| exp04's scoring with cosine distance | 0.543 | 0.623 ± 0.074 |
| **pre-registered** | **0.585** | **0.689 ± 0.043** |
| best single cell of the inner-validation sweep | 0.528 | 0.549 ± 0.075 |

Chance is 0.500. Three findings:

1. **The old scoring gives 0.514 even on these better embeddings.** The
   improvement comes entirely from how distance is measured — mainly from
   projecting with LDA instead of PCA.
2. **0.689 lands at the top of exp04's pre-registered "real but weak signal"
   band (0.60–0.70).** Two LDA variants not chosen in advance reached
   0.724 ± 0.062 and 0.729 ± 0.064; they are reported as exploratory.
3. **Picking the sweep's single best cell would have failed.** It scored 0.806
   on inner validation and 0.549 on test. Choosing by the median instead of the
   maximum is what produced a number that held.

### Phase D — frozen versus fine-tuned, and how to pool a driver's windows

Same pre-registered scoring, five partitions:

| Encoder | Window AUROC | Driver AUROC |
|---|--:|--:|
| frozen | 0.557 | 0.632 ± 0.051 |
| fine-tuned | 0.585 | 0.689 ± 0.043 |

At this matched configuration (block 3, 30 s) fine-tuning adds +0.057. Most of
the gain from 0.514 to 0.689 came from the scoring configuration; the frozen
encoder alone, scored well, reaches 0.632 here — and 0.717 at its own
inner-validation choice (block 1, 90 s; D14).

Pooling a driver's window scores by median (the default), mean or trimmed mean
gives 0.689–0.709, inside each other's error bars. Rules that look at the
extreme windows do worse (90th percentile 0.629, maximum 0.618), so strangers
differ in their typical driving, not in a few unusual windows.

### Phase E — closed set, 46-way, all drivers enrolled (test)

With no strangers held out, every driver is enrolled. Two training seeds:

| Encoder | linear probe | **LDA + centroid** | random forest |
|---|--:|--:|--:|
| **fine-tuned** | 41.4% ± 1.9 | **43.1% ± 0.9** | 26.5% ± 3.9 |
| frozen | 27.6% | 27.2% | 17.4% |

Chance is 2.2%. At this matched configuration fine-tuning adds +15.9pp. Read
out after block 1 at 90 s — its own inner-validation choice — the frozen encoder
reaches 44.9% (D14). Most of that climb is the window, not the block: at block 1,
30 s → 90 s adds 12.8pp; at 30 s, block 3 → block 1 adds 5.0pp (exp06 grid). The
matched comparison runs frozen at the fine-tuned arm's window, which is the
frozen arm's worst. 29.1 min per seed.

## Files

| File | What |
|---|---|
| `phase_a.py` → `phase_a.md` | window length, inner validation |
| `phase_b.py` → `phase_b.md` | 5-partition fine-tuning, test; saves embeddings |
| `phase_c.py` → `phase_c_preview.md` | first open-set sweep — **scored on test, exploratory only** |
| `phase_c_sweep.py` → `phase_c_sweep.md` | 1,300-configuration sweep, inner validation |
| `phase_c_final.py` → `phase_c_final.md` | pre-registered configuration on test |
| `phase_d.py` → `phase_d.md` | frozen vs fine-tuned; pooling rules |
| `phase_e_46way.py` → `phase_e_46way.md` | 46-way, two seeds |

## Commands

```bash
python -u -m experiments.exp07_full_window.phase_a
python -u -m experiments.exp07_full_window.phase_b
python -u -m experiments.exp07_full_window.phase_c_sweep
python -u -m experiments.exp07_full_window.phase_c_final
python -u -m experiments.exp07_full_window.phase_d
python -u -m experiments.exp07_full_window.phase_e_46way
```

## Limitations

- **One drive per driver.** A stranger is also an unseen day, so part of any
  open-set separation may come from new conditions rather than a new person.
  This bounds every open-set number. See `DECISIONS.md` C1.
- Driver-level AUROC rests on 46 points per partition; one partition varies by
  about ±0.09, five partitions by about ±0.04.
- Fixed 60-epoch budget, final epoch, no early stopping or best-epoch selection.
- Phase E's error bar covers training seeds only, not the choice of split.
- Resampling (S6) and the read-out block (D14) were re-tested in exp08; neither
  changed this arm. `phase_a.md` and `phase_b.md` still list the read-out layer as
  untested: they predate that work.
