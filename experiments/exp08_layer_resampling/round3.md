# exp08 Round 3 — groups, operating points, data efficiency

Headline configuration: exp07 Phase B embeddings (layer 2, `mean_token`, 30 s, `np.interp`, `full`), five 36/10 partitions, test split, pre-registered open-set scoring. `frozen` is the same encoder never fine-tuned. Values are mean ± sd over partitions.

## A. Awareness groups

Closed-set top-1 (LDA + centroid, 36-way, chance 2.8%):

| Group | `full` | `frozen` |
|---|--:|--:|
| G1 | 44.2% ± 5.4 | 31.6% ± 1.3 |
| G2 | 45.0% ± 2.4 | 29.6% ± 2.1 |
| G3 | 46.3% ± 2.0 | 30.7% ± 3.1 |

Open-set AUROC within each group (enrolled drivers of the group vs strangers of the same group), pooled over the five partitions because each holds only 3–4 strangers per group:

| Group | `full` window | `full` driver | `frozen` window | `frozen` driver | strangers pooled |
|---|--:|--:|--:|--:|--:|
| G1 | 0.549 | 0.601 | 0.557 | 0.601 | 15 |
| G2 | 0.631 | 0.847 | 0.571 | 0.683 | 15 |
| G3 | 0.575 | 0.702 | 0.552 | 0.643 | 20 |

## B. Operating points (strangers = positive class)

| Arm | level | AUROC | AUPR | EER | strangers accepted when 95% of enrolled are accepted |
|---|---|--:|--:|--:|--:|
| `full` | window | 0.585 ± 0.025 | 0.263 ± 0.013 | 0.444 ± 0.018 | 93.6% ± 1.5 |
| `full` | driver | 0.689 ± 0.043 | 0.450 ± 0.034 | 0.341 ± 0.047 | 82.0% ± 11.7 |
| `frozen` | window | 0.557 ± 0.010 | 0.247 ± 0.015 | 0.460 ± 0.007 | 93.9% ± 1.8 |
| `frozen` | driver | 0.632 ± 0.051 | 0.350 ± 0.042 | 0.421 ± 0.072 | 92.0% ± 7.5 |

AUPR's chance level is the stranger share: ~0.20 at window level, 10/46 ≈ 0.22 at driver level. EER's chance level is 0.50.

## C. Data efficiency (RQ4)

Read-outs and prototypes rebuilt from the earliest share of each enrolled driver's training windows; test windows unchanged. **`frozen` is the clean curve. `full` is an optimistic upper bound** — its encoder was fine-tuned on 100% of the windows.

| Share of training windows | `frozen` top-1 | `frozen` driver AUROC | `full` top-1 | `full` driver AUROC |
|--:|--:|--:|--:|--:|
| 25% | 18.4% ± 1.3 | 0.518 ± 0.076 | 25.4% ± 2.0 | 0.595 ± 0.046 |
| 50% | 24.3% ± 1.0 | 0.577 ± 0.083 | 33.6% ± 2.5 | 0.640 ± 0.029 |
| 75% | 28.7% ± 1.5 | 0.642 ± 0.045 | 39.3% ± 2.6 | 0.642 ± 0.068 |
| 100% | 30.5% ± 1.4 | 0.632 ± 0.051 | 45.3% ± 2.0 | 0.689 ± 0.043 |

## Limitations

- Group-level open-set numbers rest on 13–17 strangers pooled across partitions; treat differences between groups as indicative only.
- The fine-tuned data-efficiency curve is an upper bound (see C).
- One drive per driver; a stranger is also an unseen day. See `DECISIONS.md` C1.
