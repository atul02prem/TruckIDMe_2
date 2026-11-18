# exp04 — channel attention as a fourth read-out

Frozen Mantis embeddings reshaped to **50 channel tokens x 256 dims** and pooled by attention, instead of being consumed as one flat 12,800-dim vector. Same cached embeddings, same five 36-known/10-unknown partitions, same chronological split, same scoring as `results.md`; **only the read-out changes**, which is the H4 axis. Values are mean +/- sd across partitions.

`pool` applies input-dependent channel *weighting* only. `selfattn` adds cross-channel *interaction*. Comparing them separates the two mechanisms.

## Closed set — naming the enrolled drivers

36-way, random floor 2.8%. The incumbent read-outs on the **same frozen embeddings** are `linear_probe` 26.2% +/- 1.4, `lda_centroid` 28.7% +/- 2.7, `random_forest` 21.2% +/- 0.8.

| Read-out | top-1 | top-2 | parameters | train s/partition |
|---|--:|--:|--:|--:|
| `pool` | **11.3%** +/- 1.4% | 18.6% +/- 2.4% | 141,604 | 10.7 |
| `selfattn` | **10.9%** +/- 1.7% | 19.6% +/- 1.7% | 272,932 | 11.1 |
| `linear_probe` (incumbent) | 26.2% +/- 1.4% | 38.4% | 460,836 | — |
| `lda_centroid` (incumbent) | 28.7% +/- 2.7% | 41.2% | — | — |
| `random_forest` (incumbent) | 21.2% +/- 0.8% | 35.1% | — | — |

## Open set — rejecting the never-enrolled

AUROC on the pooled representation; **0.500 is chance**. The frozen flat-embedding reference is 0.514 (`mahalanobis`), and `scratch` — a randomly initialised encoder — reaches 0.516, so this column is reported for completeness and was not expected to move.

| Variant | `euclidean` | `cosine` | `ratio` | `mahalanobis` | `msp` |
|---|--:|--:|--:|--:|--:|
| `pool` | 0.490 +/- 0.042 | 0.498 +/- 0.042 | 0.492 +/- 0.031 | 0.491 +/- 0.031 | 0.497 +/- 0.021 |
| `selfattn` | 0.500 +/- 0.028 | 0.492 +/- 0.030 | 0.474 +/- 0.013 | 0.504 +/- 0.024 | 0.490 +/- 0.026 |

Driver-level AUROC (median score per driver):

| Variant | best rule | driver AUROC |
|---|---|--:|
| `pool` | `ratio` | **0.494** +/- 0.128 |
| `selfattn` | `mahalanobis` | **0.503** +/- 0.062 |

That 'best rule' column is a maximum over five rules and is therefore optimistically biased — in `results.md` the random-initialisation arm wins it. Read the per-rule means above instead.

## Figure

- `/home/ap9107/TruckIDMe/outputs/figures/exp04_attention_weights.png` — mean attention weight per channel, overall and split by awareness group. Uniform attention would be 0.020; distance from that line is how much the head concentrates on particular signals.

## Limitations

- **Frozen embeddings only.** The adapted (`full`) embeddings were never persisted, so attention on top of a fine-tuned encoder is untested.
- **Fixed 200-epoch budget, final epoch, no model selection**, matching the rest of exp04. No early stopping and no best-epoch cherry-picking, which also forgoes the ~1pp a smoothed-accuracy rule would buy.
- **The attention weights are descriptive, not causal.** A channel receiving high weight is one this head found useful given the other 49; it is not evidence that the channel is independently identity-bearing.
- One drive per driver, so an unknown driver is also an unknown day. See `DECISIONS.md` C1.
