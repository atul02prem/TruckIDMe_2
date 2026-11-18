# exp08 — read-out block profile, frozen encoder, inner validation

Frozen Mantis-8M, `mean_token`, every block. **Inner validation** only: the training windows split again 70 / 5 / 25 per driver; no test window is read. Mantis numbers its blocks from 0.

**Pre-registered rule:** switch from index 2 only if another block beats it by ≥ 2pp in 46-way inner LDA at ≥ 3 of 4 windows. Open set is reported and does not decide.

## 46-way closed set, LDA + centroid (decides)

| Block | 30 s | 51.2 s | 90 s | 120 s |
|---|--:|--:|--:|--:|
| index 0 (block 1 of 6) | 30.1% | 38.5% | 43.4% | 38.8% |
| index 1 (block 2 of 6) | 27.9% | 34.9% | 42.1% | 44.4% |
| index 2 (block 3 of 6) | 26.5% | 33.4% | 38.0% | 36.0% |
| index 3 (block 4 of 6) | 24.9% | 29.8% | 33.1% | 32.0% |
| index 4 (block 5 of 6) | 21.9% | 25.9% | 27.3% | 27.5% |
| final (block 6 of 6) | 20.3% | 24.1% | 24.8% | 23.6% |

## Open set, inner driver AUROC, mean ± sd over 5 partitions (reported only)

| Block | 30 s | 51.2 s | 90 s | 120 s |
|---|--:|--:|--:|--:|
| index 0 (block 1 of 6) | 0.686 ± 0.030 | 0.686 ± 0.073 | 0.611 ± 0.049 | 0.664 ± 0.052 |
| index 1 (block 2 of 6) | 0.664 ± 0.023 | 0.659 ± 0.057 | 0.619 ± 0.049 | 0.629 ± 0.093 |
| index 2 (block 3 of 6) | 0.683 ± 0.090 | 0.628 ± 0.058 | 0.576 ± 0.032 | 0.618 ± 0.050 |
| index 3 (block 4 of 6) | 0.672 ± 0.088 | 0.609 ± 0.077 | 0.594 ± 0.053 | 0.572 ± 0.069 |
| index 4 (block 5 of 6) | 0.644 ± 0.141 | 0.659 ± 0.083 | 0.559 ± 0.062 | 0.541 ± 0.086 |
| final (block 6 of 6) | 0.638 ± 0.066 | 0.662 ± 0.085 | 0.557 ± 0.044 | 0.487 ± 0.115 |

## Decision

- index 0 (block 1 of 6): beats index 2 by ≥ 2pp at 4 of 4 windows (30 s, 51.2 s, 90 s, 120 s)
- index 1 (block 2 of 6): beats index 2 by ≥ 2pp at 2 of 4 windows (90 s, 120 s)
- index 3 (block 4 of 6): beats index 2 by ≥ 2pp at 0 of 4 windows
- index 4 (block 5 of 6): beats index 2 by ≥ 2pp at 0 of 4 windows
- final (block 6 of 6): beats index 2 by ≥ 2pp at 0 of 4 windows

**The rule is met: the frozen arm moves to index 0 (block 1 of 6)**, the qualifying block with the highest mean across windows.

## Limitations

- Inner validation draws on the same 46 drives as test; its windows are correlated with the outer training windows.
- Frozen arm only; a block change for the fine-tuned arm needs its own fine-tuning runs.
- `mean_token` only.
