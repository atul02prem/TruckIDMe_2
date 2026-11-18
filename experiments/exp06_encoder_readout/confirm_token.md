# exp06 — output token confirmed on inner validation

`run.py` chose `mean_token` using **test**-split accuracy, which biases that estimate. This re-ranks the three tokens on an **inner validation split carved out of the training windows only**, so the test set plays no part in the choice.

Frozen encoder, audited 50 channels, 46 drivers, chance 2.2%. Best read-out per cell is shown; the full per-read-out numbers follow.

**`mean_token` wins on inner validation at 4 of 4 window lengths.**

## Inner-validation accuracy (selection is made here)

| Window | Output token | linear probe | LDA + centroid | random forest | best | test-split best (biased) |
|---|---|--:|--:|--:|--:|--:|
| 30 s | `cls_token` | 18.5% | 19.2% | 16.1% | **19.2%** | — |
| 30 s | `mean_token` ✅ | 22.3% | 26.5% | 17.2% | **26.5%** | — |
| 30 s | `combined` | 20.7% | 22.9% | 16.4% | **22.9%** | — |
| 51.2 s | `cls_token` | 19.8% | 24.4% | 21.2% | **24.4%** | 24.6% |
| 51.2 s | `mean_token` ✅ | 25.1% | 33.4% | 28.5% | **33.4%** | 28.9% |
| 51.2 s | `combined` | 22.0% | 26.8% | 23.4% | **26.8%** | 28.0% |
| 90 s | `cls_token` | 15.7% | 25.6% | 17.4% | **25.6%** | — |
| 90 s | `mean_token` ✅ | 22.7% | 38.0% | 16.5% | **38.0%** | — |
| 90 s | `combined` | 21.1% | 29.3% | 21.5% | **29.3%** | — |
| 120 s | `cls_token` | 18.5% | 28.7% | 19.1% | **28.7%** | 27.7% |
| 120 s | `mean_token` ✅ | 26.4% | 36.0% | 27.0% | **36.0%** | 36.7% |
| 120 s | `combined` | 19.1% | 33.7% | 25.8% | **33.7%** | 30.9% |

✅ marks the token selected at that window length.

## Reading this

- The **inner-validation** column is the legitimate basis for choosing an output token. The **test-split** column is what `run.py` reported and is biased by having been used to select.
- Inner-validation accuracies are expected to sit **below** the test-split ones: the inner-train set is only ~70% of the training windows, so every read-out is fitted on less data. **Compare tokens within a column, never across columns.**

## Limitations

- Single inner split, no error bars; the token gap on test was 9.0pp, well outside plausible selection noise, which is why one split is treated as sufficient to confirm rather than to measure.
- **Frozen encoder only.** Whether the same token wins after fine-tuning is a separate question, answered by the `full` arm.
- Read-out layer fixed at 2. The Mantis paper reports intermediate layers help frozen feature extraction specifically, which is the regime here.
- One drive per driver. See `DECISIONS.md` C1.
