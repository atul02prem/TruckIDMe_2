# The design space — every axis, what we have tested, what we have not

> **SUPERSEDED** by `design_space_final.md`. Kept as the snapshot of what had and had not been tested while exp06 was running; several rows below were settled afterwards (output token, read-out layer, resampling, open-set scoring).

A map of every choice this study makes, so the untested ones are visible rather
than implicit. Written after exp06 was launched; status reflects that moment.

Legend: ✅ tested properly · ⚠️ tested, but with an instrument or configuration
we no longer trust · 🔄 running · ❌ never tested.

---

## Stage 1 — Cohort and splits

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Cohort size | 46-way, 36-way | ✅ | 36-way is forced by the open-set holdout |
| Driver exclusions | 46 usable (4 dropped) | ⚠️ | G1S10/11/12 are likely salvageable — the corruption is `canloggerTime`-only, CAN `TimeXXX` and `gpsTime` are fine. Would give **49 drivers** |
| Awareness group (G1/G2/G3) | reported per-group for the classical baseline only | ⚠️ | never broken out for any Mantis result, though G3 was consistently hardest |
| Split ratio | 70% train / 5% gap / 25% test | ❌ | never varied |
| **Split direction** | early → late only | ❌ | **explicitly requested early on and never run**: train on the *last* 70%, test on the *first* 25%. Tests whether identity is stable in both temporal directions or whether we are exploiting warm-up behaviour |
| Partitions | 5, seed 42 | ✅ | |

## Stage 2 — Channels

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Channel set | `all50`, `actuated11`, `random11`×5, `attention15`, top-k by η² | ✅ | exp05 |
| Channel count | 5 / 11 / 15 / 25 / 50 | ✅ | `top15` (29.2%) beat `all50` (24.6%) at 46-way |
| SPN exclusion list | 52 dropped, fixed | ✅ | settled by the η² audit |
| Bursty signals (898/518/4191/3544) | excluded | ❌ | silent ~92% of the time; excluded for the first pass and never revisited |

## Stage 3 — Windowing

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Window length | 30 / 51.2 / 90 / 120 s | ✅ | exp05 sweep; LDA rises with length, probe peaks at 51.2 s |
| **Overlap** | **0% only** | ❌ | **the single biggest untested lever.** Much of the literature uses heavy overlap (some up to 98%). It would multiply the training set, which Stage 1 of exp04 identified as the binding constraint — but it also weakens the disjoint-sample guarantee, so the gap must be expressed in *time* and be at least one window long |
| Window phase/alignment | fixed | ❌ | minor |

## Stage 4 — Resampling

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| **Method** | `np.interp` (point sampling) only | ❌ | **known to be wrong for downsampling.** At 120 s the grid is 4.27 Hz and 39 of 50 channels are above it; 100 Hz channels are decimated 23× with no anti-aliasing. **Bin averaging** is the correct operation and is untested |
| Target length | 512, fixed | — | locked by the checkpoint (`seq_len` must be a multiple of `num_patches`=32, and the patch weights are pre-trained) |

## Stage 5 — Encoder

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Checkpoint | Mantis-8M chosen; MantisPlus, UTICA, MantisV2 also ranked | ⚠️ | ranked once with nearest-centroid on an 8-channel config |
| Read-out layer | 1 / 2 / 3 / final | ⚠️ | same superseded selection; layer 2 chosen |
| Output token | `cls_token` vs `combined`; `mean_token` never | 🔄 | **exp06 is re-running all three** with probe/LDA/RF, 46-way closed *and* open set |
| Embedding width | 256/channel, fixed | — | checkpoint-locked. `combined` gives 512 by concatenating two read-outs of the same space |
| **Multivariate handling** | per-channel concatenation only | ❌ | **the authors' recommended channel adapter is untested.** `fit()` trains adapters correctly, but `transform()` and `predict_proba()` both ignore them, so it needs ~30 lines of custom inference |
| Training mode | frozen / head / full / scratch | ✅ | exp04; full 31.0% > head 25.8% > scratch 22.5% |
| Epoch budget | 30 / 60 / 100 / 200 | ✅ | exp04 Stage 1 |
| Learning rate | 1e-4 only | ❌ | inherited from the published EEG fine-tuning recipe, never tuned for this data |
| Batch size | 64 only | ❌ | |
| Parameter-efficient tuning | none | ❌ | LoRA / BitFit / last-N-layers are the real middle ground between `head` (5.7%) and `full` (100%); Mantis exposes neither |

## Stage 6 — Representation post-processing

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Level features (per-channel mean+std) | with / without | ✅ | exp04 H3 — helps only `frozen` under random forest, +2.4pp |
| PCA dimensionality | 50 (open set), 200 (LDA) | ❌ | both are arbitrary and **never swept**, yet every distance score depends on the first one |
| Scaling | `StandardScaler`, fitted on train | ✅ | |
| Channel attention | attention-pool, self-attention | ✅ | exp04 — both lose to flat linear read-outs by ~15pp |

## Stage 7 — Read-out

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Read-out type | nearest-centroid / probe / LDA+centroid / RF / attention | ✅ | **the largest single effect in the study**: 10.9% → 28.7% on identical embeddings |
| **Read-out hyperparameters** | defaults | ❌ | **`LogisticRegression` `C` was never swept.** At 12,800 features against ~1,240 examples, the default `C=1.0` is unlikely to be right, and the probe is one of the two best read-outs |
| Forest size | 500 trees | ❌ | never varied |
| Decision granularity | per-window and driver-pooled | ✅ | pooling lifts open-set AUROC materially |

## Stage 8 — Open set

| Axis | Levels tried | Status | Note |
|---|---|:-:|---|
| Scoring rule | euclidean / cosine / ratio / mahalanobis / msp | ✅ | all ≈ 0.51 |
| **k-NN distance** | — | ❌ | **the main methodological omission.** Every rule we tried scores against a *class centroid*; k-NN distance to the nearest training window is the standard strong OOD baseline and routinely beats centroid methods |
| Energy score (−logsumexp of logits) | — | ❌ | needs logits, so needs a refit (weights were never saved) |
| **Verification framing (1-vs-1)** | — | ❌ | we only ask "is this one of the 36?". The standard biometric question is "this claims to be driver 7 — accept?", which is a much easier and more conventionally reported task (EER, FAR/FRR) |
| Unknown count | 10 of 46 | ❌ | never varied; the operating point matters for AUROC interpretation |
| Threshold percentile | 95 | ❌ | |
| Enrollment size | all train windows | ❌ | how many windows are needed to enrol a driver is a deployment question we never asked |
| **Within-driver drift diagnostic** | — | ❌ | would quantify *why* open-set fails: if a known driver's late windows are already as far from their own prototype as unknown drivers are, rejection is information-theoretically impossible on single-trip data |

---

## Ranked by value ÷ cost

| # | Axis | Cost | Why |
|--:|---|--:|---|
| 1 | **k-NN open-set score** | ~5 min | directly targets the null; the one standard baseline we skipped |
| 2 | **`LogisticRegression` C sweep** | ~10 min | could lift every closed-set probe number for free |
| 3 | **Reversed train/test split** | ~10 min | explicitly requested long ago, never run; tests temporal direction |
| 4 | **Within-driver drift diagnostic** | ~5 min | converts "open-set was null" into "open-set is impossible here, and here is the number" |
| 5 | **Bin averaging** | ~25 min | fixes a known-wrong operation; worst at 120 s |
| 6 | **Verification framing (EER)** | ~15 min | the conventional biometric metric, computable from cached distances |
| 7 | **Channel adapter** | ~45 min | the authors' recommended path; reviewers will ask |
| 8 | **Overlap** | ~1 h+ | biggest potential accuracy lever, but complicates the leakage argument |
| 9 | PCA dimension sweep | ~15 min | every distance score depends on an unswept constant |
| 10 | Salvage G1S10/11/12 → 49 drivers | ~1 h | more data, and a harder benchmark |

## The honest summary

Roughly **half of the axes above have never been tested**, and three of the
untested ones bear directly on conclusions we have already drawn:

- The open-set null rests on **centroid-based** scoring rules only (#1, #4).
- Every closed-set number uses **unswept read-out hyperparameters** (#2).
- The resampling is **known to alias** at the window length that produced our
  best frozen result (#5).

None of these is likely to overturn the headline findings — read-out choice
dominating, pre-training helping, open-set failing — but #1 and #4 are what
would make the open-set claim defensible rather than merely reported.
