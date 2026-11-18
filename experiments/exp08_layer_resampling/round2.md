# exp08 Round 2 — `np.interp` vs bin averaging, on test

layer 2, `mean_token`, `full`, 60 epochs, the five exp07 partitions (36 known / 10 unknown, seed 42). Every number is on the **test** split. Open set uses exp07's pre-registered scoring. Values are mean ± sd over partitions; the two resampling methods share partitions, so comparisons are paired.

| Window | Resampling | partitions | probe | LDA | forest | window AUROC | driver AUROC |
|---|---|--:|--:|--:|--:|--:|--:|
| 30 s | interp | 5 | 42.9% ± 1.6 | 45.3% ± 2.6 | 26.9% ± 2.0 | 0.585 ± 0.025 | **0.689** ± 0.043 |
| 30 s | binavg | 5 | 43.8% ± 1.1 | 46.5% ± 1.3 | 26.3% ± 1.1 | 0.580 ± 0.024 | **0.707** ± 0.082 |
| 51.2 s | interp | 5 | 36.2% ± 2.6 | 39.6% ± 1.9 | 35.6% ± 1.5 | 0.566 ± 0.035 | **0.637** ± 0.063 |
| 51.2 s | binavg | 5 | 32.7% ± 2.6 | 37.5% ± 1.9 | 34.9% ± 1.6 | 0.558 ± 0.023 | **0.587** ± 0.068 |
| 90 s | interp | 5 | 34.6% ± 2.4 | 41.8% ± 1.5 | 31.9% ± 1.5 | 0.598 ± 0.031 | **0.691** ± 0.091 |
| 90 s | binavg | 5 | 33.8% ± 2.4 | 40.9% ± 1.1 | 32.5% ± 1.6 | 0.589 ± 0.035 | **0.667** ± 0.037 |
| 120 s | interp | 5 | 35.9% ± 1.1 | 38.2% ± 3.3 | 39.9% ± 2.1 | 0.579 ± 0.024 | **0.648** ± 0.043 |
| 120 s | binavg | 5 | 36.1% ± 1.1 | 42.4% ± 3.4 | 41.0% ± 2.2 | 0.559 ± 0.053 | **0.608** ± 0.123 |

## Paired differences (bin averaging − `np.interp`)

| Window | LDA | window AUROC | driver AUROC | partitions where driver AUROC improved |
|---|--:|--:|--:|--:|
| 30 s | +1.3pp | -0.005 | +0.018 | 2 of 5 |
| 51.2 s | -2.1pp | -0.008 | -0.051 | 1 of 5 |
| 90 s | -0.9pp | -0.009 | -0.024 | 2 of 5 |
| 120 s | +4.2pp | -0.020 | -0.041 | 2 of 5 |

## Decision

At 30 s, bin averaging changes driver AUROC by +0.018 (2 of 5 partitions improved) and LDA accuracy by +1.3pp. **The rule is not met: `np.interp` stays in the headline.**

Other windows are exploratory: choosing a window from test numbers would be selection on test.

## Limitations

- One seed; partitions vary the driver draw, not training noise.
- One drive per driver, so a stranger is also an unseen day. See `DECISIONS.md` C1.
