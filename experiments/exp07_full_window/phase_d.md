# exp07 Phase D — frozen vs fine-tuned, and the pooling rule

30 s windows, `mean_token`, 5 partitions of 36 known / 10 unknown drivers. Scoring is Phase C's **pre-registered** configuration — LDA projection, `l2norm_whiten`, `mean` prototypes, `cosine` distance — held fixed. Only the arm and the pooling rule vary. **0.500 is chance.**

## Window-level AUROC (no pooling)

| Arm | window AUROC |
|---|--:|
| `frozen` | 0.557 ± 0.010 |
| `full` | 0.585 ± 0.025 |

## Driver-level AUROC by pooling rule

Each driver's window scores reduced to one number, then AUROC over 36 enrolled against 10 strangers.

| Pooling | `frozen` | `full` | full − frozen |
|---|--:|--:|--:|
| **`median`** | 0.632 ± 0.051 | **0.689** ± 0.043 | +0.057 |
| `mean` | 0.654 ± 0.055 | 0.709 ± 0.071 | +0.054 |
| `trimmed` | 0.657 ± 0.052 | 0.707 ± 0.068 | +0.051 |
| `min` | 0.631 ± 0.055 | 0.637 ± 0.058 | +0.006 |
| `q75` | 0.608 ± 0.073 | 0.662 ± 0.086 | +0.054 |
| `q90` | 0.568 ± 0.067 | 0.629 ± 0.043 | +0.061 |
| `max` | 0.538 ± 0.078 | 0.618 ± 0.037 | +0.080 |
| `vote` | 0.552 ± 0.027 | 0.553 ± 0.039 | +0.002 |

**`median` is the inherited default**, shown in bold. Best observed for `full`: `mean` at 0.709.

## Reading this

- **`full` − `frozen` is what fine-tuning bought** on open-set rejection, with the scoring configuration held fixed. It is the only comparison here that separates the encoder from the read-out.
- **The pooling column is exploratory.** `median` was pre-registered by inheritance; if another rule wins, that is a finding to confirm elsewhere, not a number to swap into the headline.
- Driver-level compares 36 against 10 — 46 points — so a single partition's value carries roughly ±0.09. The ± columns are across five partitions and are roughly half that.

## Limitations

- One drive per driver: a stranger is also an unseen *day*, so part of any separation is new conditions rather than a new person. See `DECISIONS.md` C1.
- The frozen arm reuses one embedding for all five partitions (the encoder never sees labels), whereas `full` was fine-tuned separately per partition. That is correct, but it means the frozen arm's variation comes only from the partition draw.
- Scoring configuration was chosen for the fine-tuned arm on inner validation; it may not be optimal for frozen.
