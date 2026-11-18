# Arm B embedding analysis — what did the frozen encoder encode?

**50 channels, 12800 embedding features, 46 drivers, random floor 2.17%.** Frozen Mantis, no training. Standardisation and PCA are fitted on training windows only; the split is chronological within each driver with a discarded gap.

## 1–3. Can a driver be named from a window?

Nearest prototype: each driver's early windows averaged into one point, each late window assigned to the closest.

| Window | Train | Test | k | Centroid top-1 | top-5 | 1-NN | 5-NN |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 30s | 2691 | 983 | 100 | **7.4%** | 28.1% | 7.2% | 6.4% |
| 51.2s | 1567 | 585 | 400 | **10.6%** | 30.9% | 8.9% | 6.3% |
| 90s | 878 | 336 | 400 | **8.9%** | 29.8% | 6.0% | 6.2% |
| 120s | 654 | 256 | 400 | **10.2%** | 29.3% | 9.4% | 5.5% |

## 2. Driver, or trip phase? — the decisive comparison

η² per embedding dimension against three competing labels, on identical embeddings and identical training windows. **If phase separates better than driver, the encoder is reading drive progression rather than identity**, and the accuracies above are an artefact.

| Window | η² driver (mean / max) | η² phase (mean / max) | η² group (mean / max) | dims > 0.10: driver / phase |
|--:|--:|--:|--:|--:|
| 30s | 0.0388 / 0.259 | 0.0094 / 0.121 | 0.0031 / 0.058 | 471 / 5 |
| 51.2s | 0.0568 / 0.381 | 0.0131 / 0.158 | 0.0042 / 0.065 | 1226 / 26 |
| 90s | 0.0849 / 0.505 | 0.0192 / 0.221 | 0.0052 / 0.098 | 3348 / 144 |
| 120s | 0.1074 / 0.547 | 0.0267 / 0.295 | 0.0067 / 0.119 | 5999 / 437 |

## 4. Is the dimensionality defeating us? — the k sweep

Scored on an **inner** chronological split of the training windows, so the test windows above were never used to choose k. The 50 in the inherited code was a default with no argument behind it.

| Window | k | Variance explained | Inner top-1 |
|--:|--:|--:|--:|
| 30s | 10 | 44.7% | 2.7% |
| 30s | 25 | 56.7% | 5.5% |
| 30s | 50 | 65.5% | 6.3% |
| 30s | 100 ✅ | 74.1% | 7.3% |
| 30s | 200 | 82.4% | 7.0% |
| 30s | 400 | 90.3% | 7.2% |
| 51.2s | 10 | 42.7% | 5.1% |
| 51.2s | 25 | 56.3% | 7.3% |
| 51.2s | 50 | 65.8% | 8.1% |
| 51.2s | 100 | 75.3% | 9.5% |
| 51.2s | 200 | 84.5% | 10.1% |
| 51.2s | 400 ✅ | 92.9% | 10.5% |
| 90s | 10 | 41.4% | 3.8% |
| 90s | 25 | 56.6% | 5.9% |
| 90s | 50 | 67.7% | 7.0% |
| 90s | 100 | 78.3% | 7.7% |
| 90s | 200 | 88.5% | 7.3% |
| 90s | 400 ✅ | 97.0% | 8.7% |
| 120s | 10 | 41.9% | 6.0% |
| 120s | 25 | 57.5% | 10.6% |
| 120s | 50 | 69.3% | 10.6% |
| 120s | 100 | 80.6% | 10.1% |
| 120s | 200 | 91.3% | 11.5% |
| 120s | 400 ✅ | 99.4% | 13.4% |

### How to read the curve

- **flat in k** — dimensionality was never the bottleneck; the limitation is the representation itself
- **peak at small k, falling after** — confirms that distances degenerate in high dimension, which is what nearest-prototype depends on
- **monotonic rise to the ceiling** — information is spread thin across dimensions and PCA is discarding it

**Caveat.** The inner split draws from the same 46 drives, so its windows are correlated with the outer training windows. It is the right protocol for this data, but k is less independently chosen than the window count suggests.

## Figures

Two t-SNE projections of the **same points**, coloured two ways — if the clusters follow phase rather than driver, that is visible in one glance:

- `outputs/figures/armB_tsne_driver_*.png`
- `outputs/figures/armB_tsne_phase_*.png`

