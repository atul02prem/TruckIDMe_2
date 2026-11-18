# exp07 Phase B — `full` + `mean_token` at 30 s

**5 of 5 partitions.** Mantis-8M fine-tuned end to end (60 epochs, all 8,590,372 parameters) on each partition's 36 known drivers' training windows, then evaluated once on the held-out test windows. Group-stratified 36-known/10-unknown draws, seed 42 — the same draws exp04 used. Values are mean ± sd across partitions.

Window and output token were both selected on **inner validation** (Phase A and `exp06/confirm_token.md`), so the test split played no part in configuring this run.

## Closed set — 36-way, chance 2.8%

| Configuration | linear probe | LDA + centroid | random forest |
|---|--:|--:|--:|
| `full` + `mean_token`, 30 s | **42.9%** ± 1.6% | **45.3%** ± 2.6% | **26.9%** ± 2.0% |
| `full` + `cls_token`, 51.2 s (exp04) | 30.1% ± 2.3% | 33.2% ± 2.7% | 31.8% ± 1.5% |
| `frozen` + `cls_token`, 51.2 s (exp04) | 26.2% ± 1.4% | 28.7% ± 2.7% | 21.2% ± 0.8% |

## Open set — rejecting the never-enrolled

Window-level AUROC; **0.500 is chance**. exp04's `full` reached 0.514 and its random-initialisation arm reached 0.516. Phase C sweeps the scoring rules properly on the embeddings this run saves.

| Rule | `euclidean` | `cosine` | `ratio` | `mahalanobis` | `msp` |
|---|--:|--:|--:|--:|--:|
| window-level | 0.507 ± 0.040 | 0.543 ± 0.035 | 0.517 ± 0.031 | 0.514 ± 0.024 | 0.527 ± 0.029 |
| driver-level | 0.508 ± 0.070 | 0.623 ± 0.074 | 0.521 ± 0.108 | 0.537 ± 0.038 | 0.577 ± 0.074 |

Fine-tuning cost: **22.7 min** per partition.

## Saved artefacts

`data/interim_data/embeddings_phaseB_mean_token_30s_p<N>.npz` — one per partition. Phase C reads these; no refit is needed to add a scoring rule.

## Limitations

- **Fixed 60-epoch budget, final epoch, no model selection.** Immune to selecting on noise, and forgoes the ~1pp a smoothed-accuracy rule would buy.
- **Read-out layer fixed at 2.** The Mantis paper reports intermediate layers help *frozen* extraction; layer 6 may suit fine-tuning better. Untested.
- **Resampling is `np.interp`**, which aliases on downsample. At 30 s the grid is 17.07 Hz, above the native rate of 30 of 50 channels, so this is the window length least affected by that fault.
- One drive per driver, so an unknown driver is also an unknown day. See `DECISIONS.md` C1.
