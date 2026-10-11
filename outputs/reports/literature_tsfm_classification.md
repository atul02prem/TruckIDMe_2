# Time-Series Foundation Models (TSFMs) for Classification — Survey for TruckIDMe

Which pre-trained time-series models can be used to **classify** (not just forecast),
how they are used, and what that means for open-set driver identification from
J1939 CAN data (46 drivers, ~40 min each, one drive per driver).

**VERIFIED** = read from the primary PDF (in `literature_survey/`).
**UNVERIFIED** = abstract / search snippet only — locate the source before citing.
Compiled 2026-09-15.

---

## ⚑ Concerns first (what could break the TSFM plan)

| Flag | Concern | Evidence | What to do |
|---|---|---|---|
| 🔴 | **Frozen embeddings can fail on signals unlike the pre-training data.** | EEG paper: "freezing the encoder for EEG data leads to a huge decrease in performance, so fine-tuning is necessary" (VERIFIED). E-nose paper: fine-tuning necessary for Chronos-2 / MOMENT embeddings (UNVERIFIED, abstract). | Do not assume frozen embeddings separate drivers. Measure first (KNN / nearest-centroid), then budget time for a trained head or fine-tuning. |
| 🔴 | **Feature explosion from channel-independent encoding.** | MOMENT and Mantis encode each channel separately and concatenate (VERIFIED). Mantis's own paper suspects NuTime does better on multivariate data *because* its embedding is smaller (VERIFIED). | ~62 CAN channels × ~512 dims ≈ 30k features for ~1,200 training windows (36 drivers). Reduce: channel subset, PCA, or pooling across channels. |
| 🔴 | **Scale-preserving tokens can carry trip-level offsets (leakage route).** | Mantis encodes *unnormalised* patch mean/std alongside the normalised shape (VERIFIED); NuTime encodes window mean/std (UNVERIFIED detail). MOMENT uses reversible instance normalisation, which removes per-window level (VERIFIED). | Keep the audited 40-SPN exclusion list. Trip-state levels (temperatures, fuel) must stay out of the input regardless of model. |
| 🟡 | **Fixed input length of 512 steps.** | MOMENT pads/sub-samples to 512; Mantis resizes to 512 (VERIFIED). | A 2-min window at 10 Hz = 1,200 steps → resampled ~2.3× to ~4.3 Hz — still above the ~1 Hz pedal-control band (Feng 2016, see `literature_temporal_aggregation.md`). Acceptable; a 51 s window fits natively. |
| 🟡 | **Much of the classification-TSFM evidence comes from one research group.** | Feofanov / Redko / Xie / Pan (Huawei Noah's Ark) co-author Mantis, the EEG paper, TiViT, UTICA and TIC-FM (VERIFIED from author lists). Mantis includes a conflict-of-interest disclosure (VERIFIED). | Say so in the lit survey; the E-nose paper (different group) is a useful independent counterweight. |
| 🟡 | **Hand-crafted features remain competitive.** | Catch22+ (statistical features) beats MOMENT and NuTime on UCR: 0.797 vs 0.779 / 0.773 (VERIFIED, Mantis Table 1). | Keep the RF baseline in the study — it is the "expert prior" side of the research question. |
| 🟢 | **Small classification models are fine-tunable within a capstone.** | Mantis: 4.2M params (2.2M after layer pruning) (VERIFIED, Table 6). | Fine-tuning Mantis on one GPU is realistic; MOMENT (~125–385M) is not — the EEG authors skipped it for that reason (VERIFIED). |

---

## 1. How TSFMs are used for classification (two regimes)

Both defined in Mantis §3.1 (VERIFIED):

1. **Zero-shot feature extraction** — encoder frozen; embeddings `Z = F(x)` fed to any
   classifier (Mantis uses StandardScaler + Logistic Regression; MOMENT uses an SVM).
   *"Zero-shot" here still trains a classifier on labels.*
2. **Fine-tuning** — append a classification head and update head + encoder.

Two findings that change *how* to extract features (Mantis §3.4, VERIFIED):
- **Intermediate layers beat the final layer** for frozen classification — true for
  Mantis and for other TSFMs, including forecasting ones.
- Concatenating the [CLS] token with the mean of the other tokens improves results.

A third regime is emerging (UNVERIFIED, abstract): **in-context classification** —
TIC-FM (arXiv 2602.00620) treats the labelled set as context and predicts test labels
in one forward pass with no parameter updates; the authors argue that frozen-encoder +
trained classifier "violates the training-free premise of zero-shot". Conceptually close
to *enrollment*.

---

## 2. Model landscape

| Model | Venue / year | Family | Params | Pre-training | Input / channels | Fit for TruckIDMe |
|---|---|---|---|---|---|---|
| **Mantis** | arXiv 2502.15637 (v2 Jun 2026) | Classification TSFM | 4.2M (v2; EEG paper reports 8M for v1) | Contrastive; v2 on synthetic CauKer data only | Resized to 512, 32 tokens; channel-independent | 🟢 Primary candidate — classification-native, small, fine-tunable |
| **MOMENT** | ICML 2024 | General (masked reconstruction, T5 encoder) | 40 / 125 / 385M | Time Series Pile (masked patches) | T=512, 64 patches of 8; channel-independent; RevIN | 🟡 The standard reference; frozen use only (too big to fine-tune here) |
| **NuTime** | TMLR 2024 (arXiv 2310.07402) | Classification TSFM | 2.4M | 1.89M real series | Window shape + multi-scaled mean/std embedding | 🟡 Strong on multivariate/HAR; optional comparison |
| **UTICA** | arXiv 2603.01348 (Mar 2026) | Classification TSFM (DINOv2-style self-distillation on Mantis architecture) | — | — | — | 🟡 Claims SOTA on UCR/UEA (UNVERIFIED) |
| **Chronos-2** | arXiv 2510.15821 (Oct 2025) | Forecasting (group attention, multivariate) | 119.5M | Synthetic multivariate | Native multivariate | 🟡 Competitive frozen features, but forecasting objective |
| **TiRex** | arXiv 2505.23719 (2025) | Forecasting (xLSTM) | 35.3M | — | — | 🟡 Best forecasting model on UCR frozen (0.801) |
| **TiViT-H** | NeurIPS 2025 (arXiv 2506.08641) | Frozen *vision* transformer on time-series-as-image | 630.8M | OpenCLIP images | 2D patching | 🟡 Large; shows vision features complement TSFMs |
| **UniTS** | NeurIPS 2024 | Unified multi-task (incl. classification, few-shot prompting) | — | 38 multi-domain datasets | — | 🟡 Not in Mantis benchmark (UNVERIFIED details) |
| Catch22+ | (Mantis baseline) | Hand-crafted statistics | — | none | — | Reference — beats MOMENT/NuTime on UCR |

Param counts for MOMENT (tested variant 341.2M), TiRex, Chronos-2, TiViT-H, NuTime, Mantis
from Mantis Table 6 (VERIFIED); MOMENT family sizes from MOMENT §4 (VERIFIED).

---

## 3. Head-to-head numbers (frozen features, Mantis Tables 1–2, VERIFIED)

| Collection | Catch22+ | MOMENT | TiRex | Chronos-2 | TiViT-H | NuTime | **Mantis** |
|---|---:|---:|---:|---:|---:|---:|---:|
| UCR (128 univariate) | 0.797 | 0.779 | 0.801 | 0.800 | 0.794 | 0.773 | **0.820** |
| UEA-27 (multivariate) | 0.696 | 0.699 | 0.695 | 0.697 | 0.709 | 0.720 | **0.742** |
| HAR avg (7 datasets) | 0.648 | 0.679 | 0.699 | 0.685 | 0.645 | 0.738 | **0.756** |
| EEG avg | 0.697 | 0.702 | 0.722 | 0.724 | 0.722 | 0.692 | **0.736** |

Most relevant row for us: **HHAR-OOD** (sensor data from unseen devices/users) —
MOMENT 0.308, Catch22+ 0.481, NuTime 0.560, Mantis 0.582. Out-of-distribution transfer
is where frozen models differ most, and MOMENT is weakest there.

Caveat: benchmarks run by the Mantis authors; HAR/EEG rows use Random Forest (200 trees)
on embeddings instead of Logistic Regression.

---

## 4. Transfer to domains absent from pre-training (closest analogue to CAN)

- **EEG — Gnassounou et al. 2025 (arXiv 2510.27522), VERIFIED.** Fine-tuned Mantis
  (generic, pre-trained on real or purely synthetic data) outperforms EEGNet and
  CBraMod (an EEG-specific foundation model). Mantis processes channels independently
  yet still beats the multivariate CBraMod. Frozen encoder → "huge decrease"; fine-tuning
  necessary. MOMENT excluded as too large to fine-tune.
- **E-nose — Choi & Kamruzzaman 2026 (arXiv 2606.27672), UNVERIFIED (abstract).**
  Chronos-2 and MOMENT embeddings evaluated for gas identification; fine-tuning
  necessary; fusing TSFM embeddings with specialised models helps. Independent group.
- **Non-stationarity in embeddings — Choi, Shook & Dubrawski 2026 (arXiv 2604.16428),
  UNVERIFIED (abstract).** Studies how mean shifts, variance changes and trends become
  linearly readable in TSFM embeddings (controlled AR(1) settings). Relevant to the
  trip confound: day-level offsets may be easy for a classifier to read from embeddings.

**Pattern across all three:** generic TSFMs *can* transfer to unseen signal types, but
**frozen features are not enough — adaptation is needed.**

---

## 5. Bottom line for TruckIDMe

1. **Primary model: Mantis.** Built for classification, 4.2M params (fine-tunable),
   best frozen and out-of-distribution results in the largest benchmark, and the only
   model with published cross-domain fine-tuning evidence (EEG).
2. **Reference model: MOMENT (frozen only).** The most-cited general TSFM; include it
   so the survey isn't single-model, but don't plan to fine-tune it.
3. **Keep the RF baseline.** Hand-crafted features beat two of the TSFMs on UCR; the
   comparison *is* the research question (expert prior vs generic temporal prior).
4. **Pipeline order:** frozen embeddings (intermediate layer, CLS + mean tokens) →
   measure separability on the 36 known drivers → if weak, fine-tune Mantis or train a
   head. Expect to need step 3, based on the EEG / E-nose evidence.
5. **Open-set gap:** none of these papers evaluate rejection of unseen classes; open-set
   scoring (distance / max-softmax threshold, AUROC) must come from the open-set
   recognition literature.

## References

- Feofanov et al. — Mantis. arXiv:2502.15637 (v2, 2026). `literature_survey/Mantis_2502.15637.pdf`
- Goswami et al. — MOMENT. ICML 2024, PMLR 235:16115–16152. `literature_survey/MOMENT_2402.03885.pdf`
- Gnassounou et al. — Leveraging Generic TSFMs for EEG Classification. arXiv:2510.27522. `literature_survey/EEG_TSFM_2510.27522.pdf`
- Lin et al. — NuTime. TMLR 2024; arXiv:2310.07402
- Moakher, El Hili, Feofanov — UTICA. arXiv:2603.01348
- Ansari et al. — Chronos-2. arXiv:2510.15821
- Auer et al. — TiRex. arXiv:2505.23719
- Roschmann et al. — TiViT. NeurIPS 2025; arXiv:2506.08641
- Gao et al. — UniTS. NeurIPS 2024
- Fang et al. — TIC-FM, Rethinking Zero-Shot TSC. arXiv:2602.00620
- Choi & Kamruzzaman — TSFMs for E-Nose. arXiv:2606.27672
- Choi, Shook, Dubrawski — Non-Stationarity in TSFM Embedding Space. arXiv:2604.16428
