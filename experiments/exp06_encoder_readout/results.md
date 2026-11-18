# exp06 — Mantis output token, measured with real read-outs

Frozen encoder, audited 50 channels, 46 drivers. `cls_token` and `mean_token` give 256 dims per channel; `combined` concatenates them for 512. All three use the same pre-trained weights — this is a read-out choice, not a different model.

Supersedes the `output_token` row of `outputs/reports/encoder_config_selection.md`, which ranked these with a **nearest-centroid** read-out (shown by exp04 to understate these embeddings by ~18pp), on an earlier 8-channel configuration, closed set only, and never tested `mean_token`.

## Closed set — 46-way, chance 2.2%

| Window | Output token | Features | linear probe | LDA + centroid | random forest | embed s |
|---|---|--:|--:|--:|--:|--:|
| 51.2 s | `cls_token` | 12,800 | 24.6% | 23.2% | 19.1% | 7.8 |
| 51.2 s | `mean_token` | 12,800 | 28.9% | 28.7% | 22.1% | 6.9 |
| 51.2 s | `combined` | 25,600 | 23.6% | 28.0% | 21.4% | 7.2 |
| 120 s | `cls_token` | 12,800 | 21.9% | 27.7% | 20.3% | 3.0 |
| 120 s | `mean_token` | 12,800 | 29.7% | 36.7% | 28.5% | 3.0 |
| 120 s | `combined` | 25,600 | 25.4% | 30.9% | 24.6% | 3.1 |

Best: **mean_token** at 120 s, 36.7%.

## Open set — 5 partitions of 36 known / 10 unknown

Window-level AUROC; **0.500 is chance**. The question `encoder_config_selection.md` never asked.

| Window | Output token | `euclidean` | `cosine` | `ratio` | `mahalanobis` | `msp` |
|---|---|--:|--:|--:|--:|--:|
| 51.2 s | `cls_token` | 0.509 ± 0.030 | 0.506 ± 0.013 | 0.521 ± 0.026 | 0.514 ± 0.039 | 0.489 ± 0.023 |
| 51.2 s | `mean_token` | 0.510 ± 0.022 | 0.506 ± 0.028 | 0.506 ± 0.017 | 0.502 ± 0.031 | 0.487 ± 0.031 |
| 51.2 s | `combined` | 0.510 ± 0.026 | 0.503 ± 0.020 | 0.508 ± 0.016 | 0.506 ± 0.034 | 0.496 ± 0.023 |
| 120 s | `cls_token` | 0.522 ± 0.027 | 0.509 ± 0.054 | 0.543 ± 0.035 | 0.524 ± 0.030 | 0.493 ± 0.038 |
| 120 s | `mean_token` | 0.523 ± 0.028 | 0.521 ± 0.046 | 0.535 ± 0.027 | 0.514 ± 0.025 | 0.487 ± 0.036 |
| 120 s | `combined` | 0.525 ± 0.026 | 0.520 ± 0.049 | 0.549 ± 0.020 | 0.524 ± 0.031 | 0.495 ± 0.035 |

## Features per training example

`combined` doubles the feature count at no change in sample size. Above 1 there are more features than examples, and distance-based scoring degrades as the ratio grows.

| Window | `cls_token` / `mean_token` | `combined` |
|---|--:|--:|
| 51.2 s | 8.1 | **16.2** |
| 120 s | 19.0 | **38.0** |

## Limitations

- **Frozen encoder only.** A different output token might interact with fine-tuning differently; untested.
- **Read-out layer fixed at 2.** The layer axis was ranked only by the same superseded nearest-centroid selection.
- Single chronological split for the closed-set column; the open-set column has five partitions.
- One drive per driver. See `DECISIONS.md` C1.
