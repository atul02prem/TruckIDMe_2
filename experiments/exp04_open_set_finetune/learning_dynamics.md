# exp04 Stage 1 — learning dynamics

One partition (36 known / 10 unknown), 51.2 s windows, **200 epochs**, batch 64, base lr 1e-04, AdamW (betas 0.9/0.999, weight decay 0.05), seed 42. **986 inner-train / 202 inner-val windows** over 36 classes. The test windows are not loaded by this script.

This is a tuning artefact, not a result. Its only output is the epoch budget Stage 2 should use.

## Where each arm peaks

| Arm | Best val top-1 | at epoch | Val top-1 at final epoch | Train top-1 at best | Gap at best | Minutes |
|---|--:|--:|--:|--:|--:|--:|
| `full` | **32.2%** | 91 | 31.7% | 100.0% | +67.8% | 37.7 |
| `head` | **27.2%** | 122 | 26.2% | 100.0% | +72.8% | 0.1 |
| `scratch` | **24.8%** | 186 | 22.8% | 100.0% | +75.2% | 37.8 |

## Reading this

- **Best epoch vs final epoch.** If validation accuracy at the final epoch is well below its peak, 200 epochs overfits and Stage 2 should stop earlier. If the two are close, the budget is not yet the binding constraint.
- **The generalisation gap** is the honest measure of how much of the training accuracy is memorisation. With 986 training windows over 36 classes (~27 per driver), a large gap is expected; what matters is the epoch at which validation stops improving.
- **The learning-rate panel** shows the library's schedule: a 10-epoch linear warmup — fixed at 10 epochs whatever `num_epochs` is — then cosine decay to zero. At 30 epochs that warmup is a third of training; at 200 epochs it is 5%. Runs at different epoch budgets are therefore differently shaped schedules, not the same model trained longer.
- **`head` trains on precomputed embeddings**, so its curve shows whether the frozen representation is linearly separable at all, independently of how long the encoder is adapted.

## Recommendation for Stage 2

**186 epochs**, taken as the later of the `full` and `scratch` peaks so neither arm is handicapped by a budget chosen for the other.

Stage 2 refits on the full training portion — inner-train, gap and inner-val reunited, about 1188 windows — so it sees ~20% more data than was used to choose this number. The true optimum there is slightly later, which this budget does not correct for.

Full per-epoch history: `learning_dynamics.csv`. Figure: `outputs/figures/exp04_learning_dynamics.png`.

