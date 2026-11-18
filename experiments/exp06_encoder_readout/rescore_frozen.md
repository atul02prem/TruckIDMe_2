# The frozen grid — window × token × read-out layer

Frozen Mantis-8M, `np.interp`, every number on the **test** split. This table **reports**; it chooses nothing. The choices were made on inner validation: `mean_token` (exp06 `confirm_token.md`) and read-out index 2 (exp08 `round1.md`).

Mantis numbers its 6 transformer blocks from 0: **index 2** is the output after block 3, **final** after block 6.

## Main table

- **Closed set:** 46-way, all drivers enrolled, LDA + centroid. Chance 2.2%. Deterministic, so no error bar.
- **Open set:** driver AUROC, 36 enrolled / 10 strangers, mean ± sd over five partitions. Chance 0.500.

| Layer | Window | Token | Closed set, 46-way | Open set, driver AUROC |
|---|--:|---|--:|--:|
| index 2 (block 3 of 6) | 30 s | `cls_token` | 20.3% | 0.543 ± 0.050 |
| index 2 (block 3 of 6) | 30 s | `mean_token` | 27.2% | 0.632 ± 0.051 |
| index 2 (block 3 of 6) | 30 s | `combined` | 23.8% | 0.565 ± 0.044 |
| index 2 (block 3 of 6) | 51.2 s | `cls_token` | 23.2% | 0.599 ± 0.083 |
| index 2 (block 3 of 6) | 51.2 s | `mean_token` | 28.7% | 0.677 ± 0.098 |
| index 2 (block 3 of 6) | 51.2 s | `combined` | 28.0% | 0.676 ± 0.071 |
| index 2 (block 3 of 6) | 90 s | `cls_token` | 25.0% | 0.581 ± 0.030 |
| index 2 (block 3 of 6) | 90 s | `mean_token` | 39.6% | 0.746 ± 0.114 |
| index 2 (block 3 of 6) | 90 s | `combined` | 31.0% | 0.664 ± 0.029 |
| index 2 (block 3 of 6) | 120 s | `cls_token` | 27.7% | 0.581 ± 0.054 |
| index 2 (block 3 of 6) | 120 s | `mean_token` | 36.7% | 0.648 ± 0.012 |
| index 2 (block 3 of 6) | 120 s | `combined` | 30.9% | 0.600 ± 0.059 |
| final (block 6 of 6) | 30 s | `cls_token` | 21.3% | 0.552 ± 0.090 |
| final (block 6 of 6) | 30 s | `mean_token` | 24.0% | 0.628 ± 0.098 |
| final (block 6 of 6) | 30 s | `combined` | 22.4% | 0.644 ± 0.126 |
| final (block 6 of 6) | 51.2 s | `cls_token` | 23.1% | 0.583 ± 0.079 |
| final (block 6 of 6) | 51.2 s | `mean_token` | 25.5% | 0.651 ± 0.093 |
| final (block 6 of 6) | 51.2 s | `combined` | 24.3% | 0.615 ± 0.066 |
| final (block 6 of 6) | 90 s | `cls_token` | 27.1% | 0.619 ± 0.084 |
| final (block 6 of 6) | 90 s | `mean_token` | 28.9% | 0.628 ± 0.087 |
| final (block 6 of 6) | 90 s | `combined` | 28.3% | 0.637 ± 0.099 |
| final (block 6 of 6) | 120 s | `cls_token` | 22.7% | 0.479 ± 0.075 |
| final (block 6 of 6) | 120 s | `mean_token` | 26.2% | 0.548 ± 0.074 |
| final (block 6 of 6) | 120 s | `combined` | 25.8% | 0.501 ± 0.059 |

## Layer profile — `mean_token`, every block

Where in the network driver information sits. 30 s is the headline's window; 90 s and 120 s are where the frozen encoder does best. Each cell: 46-way closed set / open-set driver AUROC.

| Layer | 30 s | 51.2 s | 90 s | 120 s |
|---|--:|--:|--:|--:|
| index 0 (block 1 of 6) | 32.1% / 0.693 | 32.6% / 0.566 | 44.9% / 0.717 | 39.5% / 0.615 |
| index 1 (block 2 of 6) | 30.5% / 0.600 | 32.6% / 0.588 | 40.2% / 0.603 | 39.1% / 0.682 |
| index 2 (block 3 of 6) | 27.2% / 0.632 | 28.7% / 0.677 | 39.6% / 0.746 | 36.7% / 0.648 |
| index 3 (block 4 of 6) | 25.2% / 0.603 | 28.9% / 0.691 | 33.6% / 0.677 | 34.0% / 0.604 |
| index 4 (block 5 of 6) | 25.0% / 0.579 | 27.0% / 0.647 | 28.9% / 0.653 | 28.9% / 0.577 |
| final (block 6 of 6) | 24.0% / 0.628 | 25.5% / 0.651 | 28.9% / 0.628 | 26.2% / 0.548 |

## Detail — 36-way closed set and window AUROC, same partitions

| Layer | Window | Token | Features | probe | LDA | forest | window AUROC | driver AUROC |
|---|--:|---|--:|--:|--:|--:|--:|--:|
| index 2 (block 3 of 6) | 30 s | `cls_token` | 12,800 | 26.1% ± 1.1 | 24.4% ± 1.2 | 17.2% ± 0.9 | 0.521 ± 0.015 | 0.543 ± 0.050 |
| index 2 (block 3 of 6) | 30 s | `mean_token` | 12,800 | 31.0% ± 0.9 | 30.3% ± 1.3 | 19.8% ± 1.0 | 0.557 ± 0.010 | 0.632 ± 0.051 |
| index 2 (block 3 of 6) | 30 s | `combined` | 25,600 | 28.8% ± 0.7 | 27.4% ± 1.0 | 19.7% ± 0.4 | 0.535 ± 0.017 | 0.565 ± 0.044 |
| index 2 (block 3 of 6) | 51.2 s | `cls_token` | 12,800 | 26.2% ± 1.4 | 28.7% ± 2.7 | 21.2% ± 0.8 | 0.551 ± 0.018 | 0.599 ± 0.083 |
| index 2 (block 3 of 6) | 51.2 s | `mean_token` | 12,800 | 32.1% ± 1.7 | 33.8% ± 2.2 | 25.6% ± 1.2 | 0.581 ± 0.034 | 0.677 ± 0.098 |
| index 2 (block 3 of 6) | 51.2 s | `combined` | 25,600 | 28.2% ± 1.8 | 32.4% ± 1.9 | 24.6% ± 0.8 | 0.575 ± 0.036 | 0.676 ± 0.071 |
| index 2 (block 3 of 6) | 90 s | `cls_token` | 12,800 | 25.1% ± 2.1 | 28.8% ± 2.4 | 17.0% ± 1.6 | 0.534 ± 0.025 | 0.581 ± 0.030 |
| index 2 (block 3 of 6) | 90 s | `mean_token` | 12,800 | 32.2% ± 2.3 | 39.3% ± 1.4 | 21.6% ± 2.6 | 0.603 ± 0.022 | 0.746 ± 0.114 |
| index 2 (block 3 of 6) | 90 s | `combined` | 25,600 | 27.9% ± 2.0 | 33.4% ± 1.7 | 19.8% ± 2.2 | 0.571 ± 0.021 | 0.664 ± 0.029 |
| index 2 (block 3 of 6) | 120 s | `cls_token` | 12,800 | 25.5% ± 1.9 | 27.6% ± 1.2 | 25.1% ± 2.0 | 0.535 ± 0.035 | 0.581 ± 0.054 |
| index 2 (block 3 of 6) | 120 s | `mean_token` | 12,800 | 31.4% ± 2.6 | 38.8% ± 2.9 | 29.0% ± 2.1 | 0.579 ± 0.027 | 0.648 ± 0.012 |
| index 2 (block 3 of 6) | 120 s | `combined` | 25,600 | 28.8% ± 3.2 | 31.6% ± 2.0 | 28.5% ± 2.2 | 0.554 ± 0.021 | 0.600 ± 0.059 |
| final (block 6 of 6) | 30 s | `cls_token` | 12,800 | 26.7% ± 1.4 | 25.5% ± 1.6 | 19.1% ± 0.5 | 0.526 ± 0.031 | 0.552 ± 0.090 |
| final (block 6 of 6) | 30 s | `mean_token` | 12,800 | 28.4% ± 1.7 | 27.6% ± 1.0 | 18.7% ± 0.8 | 0.536 ± 0.043 | 0.628 ± 0.098 |
| final (block 6 of 6) | 30 s | `combined` | 25,600 | 27.3% ± 1.2 | 26.6% ± 1.7 | 19.3% ± 0.4 | 0.537 ± 0.033 | 0.644 ± 0.126 |
| final (block 6 of 6) | 51.2 s | `cls_token` | 12,800 | 27.1% ± 1.9 | 28.2% ± 1.8 | 23.6% ± 0.8 | 0.532 ± 0.021 | 0.583 ± 0.079 |
| final (block 6 of 6) | 51.2 s | `mean_token` | 12,800 | 27.3% ± 1.6 | 27.9% ± 1.8 | 23.1% ± 0.8 | 0.550 ± 0.043 | 0.651 ± 0.093 |
| final (block 6 of 6) | 51.2 s | `combined` | 25,600 | 25.9% ± 1.7 | 28.4% ± 2.2 | 23.1% ± 1.2 | 0.546 ± 0.026 | 0.615 ± 0.066 |
| final (block 6 of 6) | 90 s | `cls_token` | 12,800 | 25.2% ± 2.4 | 28.6% ± 3.2 | 17.3% ± 1.6 | 0.553 ± 0.041 | 0.619 ± 0.084 |
| final (block 6 of 6) | 90 s | `mean_token` | 12,800 | 26.6% ± 0.9 | 31.2% ± 1.9 | 18.2% ± 1.6 | 0.536 ± 0.055 | 0.628 ± 0.087 |
| final (block 6 of 6) | 90 s | `combined` | 25,600 | 25.5% ± 1.8 | 29.9% ± 3.0 | 17.9% ± 1.4 | 0.554 ± 0.052 | 0.637 ± 0.099 |
| final (block 6 of 6) | 120 s | `cls_token` | 12,800 | 26.8% ± 2.8 | 26.5% ± 3.3 | 23.6% ± 1.9 | 0.504 ± 0.035 | 0.479 ± 0.075 |
| final (block 6 of 6) | 120 s | `mean_token` | 12,800 | 29.4% ± 2.7 | 27.2% ± 1.1 | 26.2% ± 2.0 | 0.510 ± 0.036 | 0.548 ± 0.074 |
| final (block 6 of 6) | 120 s | `combined` | 25,600 | 27.4% ± 2.5 | 27.2% ± 1.9 | 25.4% ± 2.0 | 0.503 ± 0.031 | 0.501 ± 0.059 |

## Detail — 46-way closed set, all three read-outs

| Layer | Window | Token | probe | LDA | forest |
|---|--:|---|--:|--:|--:|
| index 2 (block 3 of 6) | 30 s | `cls_token` | 22.9% | 20.3% | 15.0% |
| index 2 (block 3 of 6) | 30 s | `mean_token` | 27.6% | 27.2% | 17.4% |
| index 2 (block 3 of 6) | 30 s | `combined` | 26.6% | 23.8% | 17.0% |
| index 2 (block 3 of 6) | 51.2 s | `cls_token` | 24.6% | 23.2% | 19.1% |
| index 2 (block 3 of 6) | 51.2 s | `mean_token` | 28.9% | 28.7% | 22.1% |
| index 2 (block 3 of 6) | 51.2 s | `combined` | 23.6% | 28.0% | 21.4% |
| index 2 (block 3 of 6) | 90 s | `cls_token` | 22.6% | 25.0% | 14.6% |
| index 2 (block 3 of 6) | 90 s | `mean_token` | 28.9% | 39.6% | 18.2% |
| index 2 (block 3 of 6) | 90 s | `combined` | 24.4% | 31.0% | 17.0% |
| index 2 (block 3 of 6) | 120 s | `cls_token` | 21.9% | 27.7% | 20.3% |
| index 2 (block 3 of 6) | 120 s | `mean_token` | 29.7% | 36.7% | 28.5% |
| index 2 (block 3 of 6) | 120 s | `combined` | 25.4% | 30.9% | 24.6% |
| final (block 6 of 6) | 30 s | `cls_token` | 23.4% | 21.3% | 16.6% |
| final (block 6 of 6) | 30 s | `mean_token` | 24.9% | 24.0% | 17.4% |
| final (block 6 of 6) | 30 s | `combined` | 23.5% | 22.4% | 15.3% |
| final (block 6 of 6) | 51.2 s | `cls_token` | 23.8% | 23.1% | 21.9% |
| final (block 6 of 6) | 51.2 s | `mean_token` | 23.2% | 25.5% | 20.3% |
| final (block 6 of 6) | 51.2 s | `combined` | 22.1% | 24.3% | 20.7% |
| final (block 6 of 6) | 90 s | `cls_token` | 21.1% | 27.1% | 14.9% |
| final (block 6 of 6) | 90 s | `mean_token` | 23.5% | 28.9% | 14.9% |
| final (block 6 of 6) | 90 s | `combined` | 23.5% | 28.3% | 15.5% |
| final (block 6 of 6) | 120 s | `cls_token` | 22.3% | 22.7% | 20.7% |
| final (block 6 of 6) | 120 s | `mean_token` | 26.6% | 26.2% | 23.4% |
| final (block 6 of 6) | 120 s | `combined` | 25.4% | 25.8% | 26.6% |

## Limitations

- Test-split numbers, reported, not used for selection.
- Driver AUROC rests on 46 drivers per partition; one partition varies by about ±0.09, so differences under ~0.05 are not meaningful.
- One drive per driver. See `DECISIONS.md` C1.
