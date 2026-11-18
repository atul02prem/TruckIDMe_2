# exp07 Phase E — 46-way closed-set identification

All **46 drivers enrolled**, chance **2.2%**. `mean_token`, 30 s windows, per-driver chronological 70/5/25 split. The fine-tuned arm is repeated at 2 seeds (42, 1337); the frozen arm is deterministic.

Every other fine-tuned number in exp07 is 36-way, which is an easier problem; this is the full-cohort measurement.

## Results

| Arm | linear probe | LDA + centroid | random forest |
|---|--:|--:|--:|
| `full` (fine-tuned) | **41.4%** ± 1.9% | **43.1%** ± 0.9% | **26.5%** ± 3.9% |
| `frozen` | 27.6% | 27.2% | 17.4% |

## Comparison at the same cohort size

| | 46-way top-1 |
|---|--:|
| **fine-tuned Mantis, `mean_token`, 30 s** | **43.1%** |
| frozen Mantis, `mean_token`, block 1, 90 s, LDA (exp06 grid; D14) | 44.9% |
| frozen Mantis, `mean_token`, 120 s, LDA (`exp06`) | 36.7% |
| frozen Mantis, `cls_token`, 120 s, LDA (`exp05`) | 27.7% |
| chance | 2.2% |

Fine-tuning cost: **29.1 min** per seed.

## Per-seed detail

| Seed | linear probe | LDA + centroid | random forest | min |
|---|--:|--:|--:|--:|
| 42 | 39.5% | 42.2% | 22.6% | 29.1 |
| 1337 | 43.2% | 43.9% | 30.4% | 29.1 |

## Limitations

- **Two seeds vary the training process, not the data.** The split is fixed, so this error bar does not capture how much the result depends on which windows land in train versus test.
- **No open-set measurement is possible here** — with all 46 drivers enrolled there are no strangers. That is measured at 36-way in Phase C and Phase D.
- Fixed 60-epoch budget, final epoch, no model selection.
- Resampling is `np.interp`, which aliases on downsample; at 30 s the grid is 17.07 Hz, the least affected of the four window lengths.
- One drive per driver. See `DECISIONS.md` C1.
