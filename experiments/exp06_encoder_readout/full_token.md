# exp06 — output token on the fine-tuned encoder

`full` fine-tuning, 30 s, `np.interp`, layer 2, the five exp07 partitions (36 known / 10 unknown). Every number is on the **test** split; mean ± sd over partitions. Open set uses exp07's pre-registered scoring.

**Pre-registered:** the headline stays `mean_token` whatever this shows. This run reports whether the token matters after fine-tuning; it does not choose one.

| Token | Features | partitions | probe | LDA | forest | window AUROC | driver AUROC |
|---|--:|--:|--:|--:|--:|--:|--:|
| `cls_token` | 12,800 | 5 | 42.1% ± 1.0 | 40.2% ± 1.9 | 31.5% ± 2.2 | 0.568 ± 0.008 | 0.713 ± 0.078 |
| `mean_token` | 12,800 | 5 | 42.9% ± 1.6 | 45.3% ± 2.6 | 26.9% ± 2.0 | 0.585 ± 0.025 | 0.689 ± 0.043 |
| `combined` | 25,600 | 5 | 41.9% ± 1.6 | 40.6% ± 1.3 | 30.9% ± 1.5 | 0.571 ± 0.012 | 0.648 ± 0.085 |

## Paired differences against `mean_token`

| Token | LDA | driver AUROC | partitions where LDA improved | partitions where driver AUROC improved |
|---|--:|--:|--:|--:|
| `cls_token` | -5.0pp | +0.024 | 0 of 5 | 3 of 5 |
| `combined` | -4.6pp | -0.041 | 0 of 5 | 2 of 5 |

## Limitations

- One seed; partitions vary the driver draw, not training noise.
- 30 s only, the fine-tuned arm's window from exp07 Phase A.
- One drive per driver. See `DECISIONS.md` C1.
