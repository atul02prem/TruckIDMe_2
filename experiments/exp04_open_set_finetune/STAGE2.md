# exp04 Stage 2 — pre-registration

> **Kept exactly as written before Stage 2 ran** — editing a pre-registration after the results would defeat it. Its context mentions an earlier open-set figure (0.543) and the classical aggregates, both outside the Mantis report; the outcome is in `README.md` and `results.md`.

Written **before** the run, so the interpretation of each possible outcome is
committed in advance and cannot be chosen after seeing the numbers. Stage 1's
results and the full data lineage are in `README.md`; this file is only about
what Stage 2 does, what it will produce, and what each result would mean.

## The question

**Can a time-series foundation model refuse a driver it was never enrolled on?**

exp03 measured a frozen Mantis encoder: open-set AUROC **0.543** — chance. The
expert aggregates scored the same. Neither representation could tell an
unenrolled driver from an enrolled one.

Stage 2 asks whether **adaptation** changes that, and whether any change comes
from the pre-training or merely from the architecture.

## What runs

```
for each of 5 partitions (36 known / 10 unknown, group-stratified, seed 42):
    fine-tune `full`     on the 36 known drivers' training windows, 100 epochs
    fine-tune `scratch`  on the same windows, same recipe, random init
    for each of 6 representations:
        open-set   → evaluate_partition: 5 scoring rules, window + driver AUROC
        closed-set → 3 read-outs: linear probe, LDA+centroid, random forest
```

The six representations are three encoders × the level toggle:

| Representation | Features | Encoder state |
|---|--:|---|
`frozen` | 12,800 | pre-trained, never adapted (exp03's embeddings, reused) |
`frozen + level` | 12,900 | as above, plus per-window per-channel mean and std |
`full` | 12,800 | pre-trained, fine-tuned on this partition's known drivers |
`full + level` | 12,900 | as above, plus level |
`scratch` | 12,800 | random init, trained on the same windows |
`scratch + level` | 12,900 | as above, plus level |

**Nothing in the open-set evaluation differs between representations.** Same
partitions, same chronological splits, same scaler-and-PCA fitted on known-train
only, same five scoring rules, same threshold calibration. The representation is
the only variable, which is what makes the comparison mean anything.

**The 10 unknown drivers are never seen by any encoder and never used to fit a
scaler, a PCA, a prototype or a threshold.** They appear once, at evaluation.

## Cost, honestly

| Component | Estimate |
|---|--:|
10 fine-tuning runs @ 100 epochs | ~19 min each → **~190 min** |
Scoring: 6 representations × 5 partitions | **~60–105 min** (uncertain) |
Figures, t-SNE | ~5 min |
| **Total** | **~4–5 h** |

The scoring estimate is the uncertain one: a logistic regression over 12,800
features with 36 classes, a 500-tree forest on the same, and a PCA(200)+LDA, all
repeated 30 times. **The smoke test measures this exactly**, since scoring cost
does not depend on the epoch count. If it lands at the high end, the honest
levers are dropping to 3 partitions or dropping the `+ level` variants of
`scratch`.

Earlier I quoted ~3.2 h. That counted only the fine-tuning and was wrong to
present as the total.

## Pre-committed interpretation

### H1 — does adaptation enable rejection?

Compare `full`'s best driver-level AUROC against the frozen 0.543.

| Outcome | Reading |
|---|---|
**≥ 0.70** | Adaptation enables open-set rejection. The primary positive finding; the one-drive confound then becomes the main threat to it and must be stated with the number, not after it |
**0.60 – 0.70** | Real but weak signal. Reportable only alongside the confound and the partition spread |
**≤ 0.55** | **Null.** Adaptation does not enable rejection on this data. Still a result: it corroborates DriveDNA's frozen-foundation-model finding at 46 drivers on real heavy-truck J1939, which no published work has done |

A null here is not a failed experiment. It is the honest answer to the capstone's
question, and it is the outcome Stage 1's calibration drift makes more likely.

### H2 — is it the pre-training, or the architecture?

| Outcome | Reading |
|---|---|
`full` > `scratch` on AUROC | pre-training helps **rejection**, not just naming. Strongest version of the claim |
`full` ≈ `scratch` on AUROC | pre-training helps **naming but not rejection** — a sharper and more interesting result than either arm alone, because Stage 1 already showed +7.4pp on closed-set accuracy. It would mean the two capabilities are dissociable |

### H3 — what does instance normalisation cost?

Mantis z-scores every window per channel at its input, so absolute level is
unrecoverable from any embedding. `+ level` restores exactly those two numbers.

| Outcome | Reading |
|---|---|
`+ level` lifts every representation substantially | input normalisation is a real bottleneck for identity tasks. A mechanistic finding about TSFMs, and the most transferable thing in the experiment |
`+ level` lifts only `frozen` | adaptation can partly compensate for what normalisation discards |
no change anywhere | absolute level is not identity-bearing here. **My hypothesis dies**, and the 33.3% vs 10.6% gap needs a different explanation |

### H4 — was exp03's 10.6% the representation or the read-out?

| Outcome | Reading |
|---|---|
probe / forest ≫ nearest-centroid | exp03 **understated** the frozen representation; the limit was 12,800 Euclidean dimensions, not the encoder |
all three read-outs similar | the frozen representation is genuinely weak, and exp03's number stands |

### A prediction from Stage 1

Validation loss rose monotonically while validation accuracy improved —
accuracy up, calibration down. **If `msp` (one minus max class probability) is
the *worst* scoring rule for `full` while being adequate for `frozen`, that is
the predicted consequence**, and it would be a genuine finding about why
confidence-thresholding fails for open-set driver identification.

## What Stage 2 does not answer

- **Whether this generalises across trips or days.** One drive per driver. An
  unknown driver is also an unknown day, so any positive AUROC conflates "new
  person" with "new conditions". Inseparable with this dataset.
- **Whether window length matters for the adapted arms.** Fixed at 51.2 s. The
  sweep exists for the frozen and expert-feature representations in exp03.
- **Whether overlap would help.** Deferred. Stage 1 showed the binding
  constraint is training-set size, so this is the largest known unexplored lever.
- **Anything about classical models.** Out of scope by decision.

## Commands

```bash
# smoke test: validates the path and measures the real scoring cost
/home/ap9107/anaconda3/envs/truckidme/bin/python -u \
    -m experiments.exp04_open_set_finetune.run --partitions 1 --epochs 3

# the experiment
/home/ap9107/anaconda3/envs/truckidme/bin/python -u \
    -m experiments.exp04_open_set_finetune.run
```

Outputs: `results.md` in this folder, and five figures under `outputs/figures/`
(`exp04_roc`, `exp04_auroc_comparison`, `exp04_closed_set`,
`exp04_embedding_geometry`, plus Stage 1's `exp04_learning_dynamics`).

## Known risks

| Risk | Mitigation |
|---|---|
`transform()` might not reflect the fine-tuned weights | the smoke test will show `full` and `scratch` embeddings differing from `frozen`; if all three score identically, that is the bug |
Memory: 3 × 2267 × 12,800 float32 retained for the t-SNE ≈ 350 MB, plus 117 MB per `hstack` copy | fits; GPU peak in Stage 1 was 14.9 / 24.6 GB |
`LogisticRegression` may not converge in 2000 iterations at 12,800 features | a convergence warning is informative, not fatal; the probe is a read-out, not the result |
Scoring cost higher than estimated | smoke test measures it before the full run commits 4+ hours |
