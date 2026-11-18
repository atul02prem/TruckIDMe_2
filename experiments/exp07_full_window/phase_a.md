# exp07 Phase A — window length for the fine-tuned arm

`full` fine-tuning with **`mean_token`**, 60 epochs, one 36-known/10-unknown partition (seed 42). The encoder is fitted on **inner-train only** and every number below is **inner-validation** — no test window is touched, so the window can be chosen here without biasing the eventual test result.

Chance is 2.8% (36 enrolled drivers).

| Window | Encoder fit on | linear probe | LDA + centroid | random forest | best | fit min |
|---|--:|--:|--:|--:|--:|--:|
| 30 s ✅ | 1,462 | 46.3% | 47.8% | 35.2% | **47.8%** | 15.6 |
| 51.2 s | 840 | 31.8% | 39.9% | 36.8% | **39.9%** | 9.4 |
| 90 s | 462 | 30.7% | 45.0% | 28.6% | **45.0%** | 5.2 |
| 120 s | 341 | 34.1% | 38.4% | 30.4% | **38.4%** | 3.8 |

Top two separated by **2.8pp**, outside the 2pp tiebreak band. **Chosen: 30 s.**

## Frozen comparison

The frozen ranking on inner validation (`exp06/confirm_token.md`, 46-way so not directly comparable in level, only in order) was 90 s > 120 s > 51.2 s > 30 s. Whether the fine-tuned arm agrees is the question this phase exists to answer — the two arms were expected to disagree, because fine-tuning is limited by training-set size and frozen read-outs are not.

## Saved artefacts

Fine-tuned embeddings are written to `data/interim_data/` as `embeddings_full_mean_token_<window>s.npz`, so Phase C's scoring sweep and any later scoring rule cost no GPU time. exp04 discarded its weights and paid for it.

## Limitations

- **One partition.** The ranking carries single-split uncertainty; the 2pp tiebreak rule was fixed before the run.
- **Encoder fitted on inner-train (~70% of known-train)**, so these accuracies sit below what Phase B will produce from the full training set. Compare windows within this table, not against others.
- Read-out layer fixed at 2. The Mantis paper reports intermediate layers help *frozen* extraction specifically, so layer 6 may suit the fine-tuned arm better — untested.
- One drive per driver. See `DECISIONS.md` C1.
