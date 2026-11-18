# exp06 — which Mantis output token to read out

## Objective

Mantis cuts each channel's 512 points into 32 patches of 16 and adds one extra
slot, the CLS token, whose job is to summarise the whole series. After the
transformer there are 33 vectors of 256 numbers per channel, and `output_token`
decides how they become one. There are exactly three options (anything else
raises `KeyError` in `TransformerUnit.forward`):

| Option | Dims per channel | What it is |
|---|--:|---|
| `cls_token` | 256 | the CLS slot |
| `mean_token` | 256 | the average of the 32 patch slots |
| `combined` | 512 | `cls_token` followed by `mean_token` |

All three use the same pre-trained weights; this is a read-out choice, not a
different model. `combined` holds twice the numbers but no new view of the
signal: it is the two 256-wide summaries side by side.
`QC/verify_embeddings.py` confirms this exactly on our data (difference 0.00).

The project had been using `cls_token`, chosen in `DECISIONS.md` D10 with a
nearest-centroid read-out on the earlier 62-channel configuration, closed set
only, and without ever testing `mean_token`.

## Four scripts, and what each one is for

| Script | Arm | Split | Role |
|---|---|---|---|
| `run.py` | frozen | test | first pass, **mistake of method**: ranked tokens on test |
| `confirm_token.py` | frozen | inner validation | **the decision** |
| `rescore_frozen.py` | frozen | test | **the frozen grid**: every window × token × read-out block, closed and open set; reports only |
| `full_token.py` | fine-tuned | test | does the choice hold after fine-tuning; reports only, pre-registered |

Only `confirm_token.py` chooses anything. Inner validation splits the training
windows again (70 / 5 / 25 per driver) and never touches the test split.

## Data lineage

| Stage | What | Shape |
|---|---|---|
| window tensors | `src/features/build_tensors.py`: 50 channels, 512 points | (n, 50, 512) |
| frozen embeddings | `src/features/build_embeddings.py`: Mantis-8M, each token, read out after block 3 of 6 (index 2) and after block 6; all six blocks for `mean_token` | (n, 12,800) or (n, 25,600) |
| fine-tuned embeddings | `full_token.py`: all parameters trained per partition, 30 s | (3,876, 12,800) or (3,876, 25,600) |
| split | per-driver chronological 70 / 5 / 25; inner split of the 70% for selection | |
| closed set | linear probe, LDA + centroid, random forest | 46 classes (decision) or 36 (reports) |
| open set | exp07's pre-registered scoring: LDA → L2-normalise → whiten → cosine to nearest driver mean | driver AUROC over 5 partitions |

## Results

### 1. The decision — frozen, inner validation, 46-way (`confirm_token.md`)

| Window | `cls_token` | **`mean_token`** | `combined` | margin |
|---|--:|--:|--:|--:|
| 30 s | 19.2% | **26.5%** | 22.9% | +7.3pp |
| 51.2 s | 24.4% | **33.4%** | 26.8% | +9.0pp |
| 90 s | 25.6% | **38.0%** | 29.3% | +12.4pp |
| 120 s | 28.7% | **36.0%** | 33.7% | +7.3pp |

**`mean_token` wins at every window, by 7–12pp.** From here on the project reads
out `mean_token`. These are inner-validation numbers and are not comparable
with test figures.

### 2. Frozen, open set, re-scored (`rescore_frozen.md`, test, 36-way)

`run.py` had found open-set window AUROC between 0.49 and 0.55 for every token,
and the earlier version of this README concluded that the token "improved
naming drivers but not rejecting strangers". That was measured with the
open-set scoring exp07 later showed to be the bottleneck. Re-scored with the
scoring that works, **the conclusion is reversed**:

| Window | `cls_token` | **`mean_token`** | `combined` |
|--:|--:|--:|--:|
| 30 s | 0.543 | **0.632** | 0.565 |
| 51.2 s | 0.599 | **0.677** | 0.676 |
| 90 s | 0.581 | **0.746** | 0.664 |
| 120 s | 0.581 | **0.648** | 0.600 |

Driver AUROC, mean over 5 partitions. `mean_token` is best at every window,
on open set as on closed set (closed-set LDA: −5 to −11pp for `cls_token`,
−1 to −7pp for `combined`). `combined` ties only at 51.2 s.

### 3. Fine-tuned, 30 s (`full_token.md`, test, 36-way)

| Token | LDA | probe | driver AUROC |
|---|--:|--:|--:|
| `cls_token` | 40.2% ± 1.9 | 42.1% ± 1.0 | 0.713 ± 0.078 |
| **`mean_token`** | **45.3% ± 2.6** | **42.9% ± 1.6** | 0.689 ± 0.043 |
| `combined` | 40.6% ± 1.3 | 41.9% ± 1.6 | 0.648 ± 0.085 |

- **Closed set:** `mean_token` beats both alternatives with LDA on **all 5
  partitions**.
- **Open set:** `cls_token` is +0.024 higher but improves on only 3 of 5
  partitions, with a spread of ±0.078 — within noise.
- **Fine-tuning does not close the gap.** At the same 30 s window, LDA trails
  `mean_token` by about the same amount in both arms: `cls_token` −5.9pp frozen,
  −5.0pp fine-tuned; `combined` −2.9pp frozen, −4.6pp fine-tuned.

Pre-registered before the run: the headline stays `mean_token` whatever this
showed, because switching on test numbers would be selecting on test.

### 4. The frozen grid across read-out blocks (`rescore_frozen.md`, test)

Mantis numbers its six transformer blocks from 0, so the project's read-out
(index 2) is the output after **block 3**. The grid adds the final block for every
token and window, and all six blocks for `mean_token`. Closed set 46-way (LDA),
open set driver AUROC:

| Block | 30 s | 90 s | 120 s |
|---|--:|--:|--:|
| **1 of 6** | **32.1%** / 0.693 | **44.9%** / 0.717 | **39.5%** / 0.615 |
| 3 of 6 (index 2) | 27.2% / 0.632 | 39.6% / 0.746 | 36.7% / 0.648 |
| 6 of 6 (final) | 24.0% / 0.628 | 28.9% / 0.628 | 26.2% / 0.548 |

Closed-set accuracy falls with depth at every window; the open-set column has no
consistent pattern. `mean_token` stays best at the final block too, so the token
choice does not depend on the block.

This table is on test, so it chooses nothing. The block was decided on inner
validation in exp08 (`layer_profile.md`, `DECISIONS.md` D14): the frozen arm
moves to block 1 at 90 s.

### Why `combined` loses, though it contains `mean_token`

`combined` holds `mean_token` unchanged, so a perfect read-out could ignore the
`cls_token` half and match `mean_token` exactly. It never does. The shortfall is
therefore the read-out's, not the encoder's: `combined` doubles the features
per training example (4.7 → 9.4 at 30 s) from the same windows, and the extra
weights are estimated from no more data. Since `cls_token` alone is the weaker
half in every comparison, `combined` adds estimation noise faster than signal.

The accurate claim is "**`combined` adds nothing our read-outs can use at this
sample size**", not that it contains less information. Testing this needs a
read-out that controls the extra features (stronger regularisation, or PCA to
`mean_token`'s width) — future work.

## Which headline numbers come from this experiment

The **frozen arm's** headline numbers are read from this experiment's grid
(`rescore_frozen.md`). Its configuration — block 1, 90 s, `mean_token` — was
chosen on inner validation elsewhere (token: `confirm_token.md` here; block and
window: exp08 `layer_profile.md`, `DECISIONS.md` D14).

| Arm | Configuration | Closed set, 46-way | Open set, driver AUROC | Numbers from |
|---|---|--:|--:|---|
| frozen | block 1, 90 s, `mean_token` | **44.9%** | **0.717 ± 0.069** | this grid (test) |
| fine-tuned | block 3, 30 s, `mean_token` | 43.1% ± 0.9 | 0.689 ± 0.043 | exp07 Phase E, Phase C |

Later experiments re-tested both arms and changed neither: bin averaging (exp08
Round 2) and fine-tuning at block 1 (exp08, D14) both failed their rules.

## ⚠️ How far to trust each number

The same configuration, measured on inner validation and then on test:

| Frozen, block 1, 90 s | inner validation | test |
|---|--:|--:|
| closed set, 46-way | 43.4% | 44.9% |
| open set, driver AUROC | 0.611 ± 0.049 | 0.717 ± 0.069 |

**The closed-set number holds** (+1.5pp). **The open-set number moves by 0.106**
between the two splits. This is the same instability seen at block 3: frozen at
90 s scored 0.531 on inner validation and 0.746 on test. Driver AUROC rests on
46 drivers per partition, so it swings with which windows land where. The honest
open-set claim is therefore that frozen and fine-tuned are **comparable**, not
that frozen is better — and the fine-tuned arm's open-set number is the more
stable of the two (inner 0.678 on one partition, test 0.689).

## Commands

```bash
python -u -m experiments.exp06_encoder_readout.confirm_token    # the decision
python -u -m experiments.exp06_encoder_readout.run              # first pass, test
python -u -m experiments.exp06_encoder_readout.rescore_frozen   # frozen open set, CPU

# fine-tuned token comparison, ~2 h on two GPUs
nohup bash experiments/exp06_encoder_readout/run_full_token.sh \
    > outputs/logs/exp06_full_token_launcher.log 2>&1 &
```

`rescore_frozen.py` reads the frozen embeddings built by
`src/features/build_embeddings.py`; run that first.

## Limitations, and where each was taken up

| Limitation | Status | Where |
|---|:-:|---|
| Token comparisons read out after block 3 only | 🟢 addressed | the grid here adds the final block (`mean_token` still leads at all 4 windows); the block itself was decided in exp08 `layer_profile.md`, D14 |
| Fine-tuned token comparison at 30 s only | 🟡 by design | 30 s is the fine-tuned arm's chosen window (exp07 `phase_a.md`, D11); other windows untested for the fine-tuned token |
| One training seed for the fine-tuned token comparison | 🟡 partly | exp07 Phase E repeats fine-tuned `mean_token` at 2 seeds (46-way 43.1% ± 0.9); the comparison itself is not repeated |
| Open-set scoring was selected on fine-tuned block-3 embeddings | 🟡 open | stated in D14; the frozen arm's 0.717 uses it untuned |
| Driver AUROC unstable between splits | 🟡 open | section above; reported, not resolved |
| Whether a regularised read-out lets `combined` beat `mean_token` | ❌ future work | — |
| One drive per driver | 🔴 cannot be addressed with this data | `DECISIONS.md` C1 |
