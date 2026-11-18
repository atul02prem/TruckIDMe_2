# exp08 Round 1 — read-out layer x resampling, inner validation

`mean_token`, 60 epochs, one 36-known/10-unknown partition (seed 42). Encoders are fitted on **inner-train**; every number is **inner validation**, so nothing here touches the test split. Closed set is 36-way (chance 2.8%), best of probe / LDA / forest. Open set is exp07's pre-registered scoring (LDA, `l2norm_whiten`, `mean`, `cosine`), driver-level AUROC.

**4 of 4 cells finished.**

## `full` — closed-set top-1

| Cell | 30 s | 51.2 s | 90 s | 120 s | best |
|---|--:|--:|--:|--:|--:|
| `layer2_interp` | 47.8% | 39.9% | 45.0% | 38.4% | **47.8%** |
| `layer2_binavg` | 47.6% | 36.8% | 47.6% | 39.1% | **47.6%** |
| `final_interp` | 42.4% | 34.6% | 35.4% | 34.1% | **42.4%** |
| `final_binavg` | 45.0% | 32.1% | 38.6% | 28.3% | **45.0%** |

## `full` — open-set driver AUROC

| Cell | 30 s | 51.2 s | 90 s | 120 s | best |
|---|--:|--:|--:|--:|--:|
| `layer2_interp` | 0.678 | 0.717 | 0.506 | 0.722 | **0.722** |
| `layer2_binavg` | 0.692 | 0.819 | 0.492 | 0.750 | **0.819** |
| `final_interp` | 0.761 | 0.533 | 0.594 | 0.561 | **0.761** |
| `final_binavg` | 0.864 | 0.675 | 0.461 | 0.631 | **0.864** |

## `frozen` — closed-set top-1

| Cell | 30 s | 51.2 s | 90 s | 120 s | best |
|---|--:|--:|--:|--:|--:|
| `layer2_interp` | 29.9% | 37.4% | 43.4% | 42.0% | **43.4%** |
| `layer2_binavg` | 29.7% | 35.2% | 41.8% | 42.8% | **42.8%** |
| `final_interp` | 24.5% | 28.7% | 32.8% | 27.5% | **32.8%** |
| `final_binavg` | 26.2% | 28.7% | 33.3% | 29.7% | **33.3%** |

## `frozen` — open-set driver AUROC

| Cell | 30 s | 51.2 s | 90 s | 120 s | best |
|---|--:|--:|--:|--:|--:|
| `layer2_interp` | 0.622 | 0.536 | 0.531 | 0.692 | **0.692** |
| `layer2_binavg` | 0.756 | 0.681 | 0.550 | 0.761 | **0.761** |
| `final_interp` | 0.675 | 0.511 | 0.492 | 0.592 | **0.675** |
| `final_binavg` | 0.775 | 0.606 | 0.433 | 0.717 | **0.775** |

## Decision

No challenger beats the incumbent `layer2_interp` (47.8%) by more than the pre-committed 2pp margin (best: `layer2_interp` at 47.8%). **The incumbent stands and exp07's test numbers are final.**

## Limitations

- One partition and one seed per cell; differences under ~2pp are within single-split noise, which is why the margin exists.
- Inner-validation accuracies are fitted on ~70% of the training windows and are not comparable to test numbers.
- One drive per driver. See `DECISIONS.md` C1.
