# Capstone Proposal — Literature Survey Deck (content master)

Structure per paper: **THEIR POV** (what the paper claims/does) vs **MY POV**
(what I take from it for this project). Speaker notes marked "Say".
Papers still to add: Gahr 2019, MOMENT, EEG-TSFM.

---

## Slide 1 — Title
**Open-Set Driver Identification from Heavy-Duty J1939 CAN Data using Time-Series Foundation Models**
Capstone proposal · ORNL Driver Identification Dataset · 46 drivers, 2014 Kenworth T270

---

## Slide 2 — The problem
- Every pedal press, torque request and brake application is broadcast on the truck's J1939 bus
- If driving style is measurable there → **authentication without extra hardware** (theft, unauthorised use) and fleet analytics
- The field asks a **closed-set** question: "which of my known drivers is this?"
- The security question is **open-set**: "is this one of my drivers *at all*?"
- Our dataset: 46 usable drivers, native CAN rates — but **one drive per driver**

> **Say:** The gap between those two questions is the project.

---

## Slide 3 — Lanigan et al. (2025) — the dataset
*J. Transportation Security · peer-reviewed*

**THEIR POV**
- 50 drivers, one 20-mile / 50-min route, Fort Collins; 2014 Kenworth T270
- 3×2 design: awareness (Control/Aware/Aware+Protocol) × experience (Standard/Professional)
- Cyberattack mid-route: needles → 0, all warning lights, 2 Hz tone — **instrument cluster only**
- Awareness alone is insufficient: stop rate 9% → 30% → **100%**; reaction 30.3 s → 16.1 s → **7.5 s**

**MY POV**
- SOPs matter: awareness + explicit instructions, not awareness alone
- The attack never touches J1939 → **our behaviour signals are truthful; no masking needed**
- **One drive per driver** = driver and trip are confounded → the root limitation of this project
- G3's 100% stop rate may explain why G3 is consistently hardest for our classifier: the protocol **homogenises** behaviour
- Stopping distance differs by group → a window overlapping the attack could leak **group**, not identity

---

## Slide 4 — Kidmose et al. (2025) — KCID: the data critique
*arXiv preprint*

**THEIR POV**
- Reviews 6 public driver-fingerprinting datasets; frames driver authentication as **anti-theft defence-in-depth**
- **All public sets are decoded OBD-II**, mostly ≤1 Hz (Barreto: 0.14 Hz)
- Raw CAN wins on **coverage · temporal resolution · fidelity**; costs are **noise** and **interpretability**
- Bluetooth OBD collection adds **latency and packet loss**
- Five gaps: decoded data · low rates · **fixed routes are unrealistic** · single vehicle · no demographics

**MY POV**
- Justifies our data choice: native-rate J1939, 46 drivers — more drivers than any set they review
- Their "raw CAN is noisy, filter it" advice **is our leakage audit**, done more rigorously
- Two criticisms land on us too: **fixed route, single vehicle** — declare both
- They never say "open-set" or claim saturation → the framing is **ours to argue**, not theirs to cite

---

## Slide 5 — Enev et al. (2016) — the foundational result
*PoPETs · peer-reviewed*

**THEIR POV**
- 15 drivers, one 2009 sedan; parking-lot maneuvers + 50-mile open-road loop
- **Brake pedal alone**: 87.3% from ~15 min, **100%** from 1.5 h; all sensors → 100%
- Quadratic interpolation + **decimation to 60 Hz**, justified by human actuation bandwidth (Nyquist)
- Fingerprint **stable across days and roads**: 91% for a re-recorded driver

**MY POV**
- A single direct-action signal can carry identity — so **channel choice matters more than channel count**
- **Free driving beats prescribed maneuvers** (50% vs 87–100%) → don't over-weight the attack window
- We improve on their order: filter **before** decimating (mean-per-100 ms), they denoise after
- Their stability result **contradicts** Shin's drift finding — the field disagrees, and we sit in that tension
- ⚠️ They compute scaling from **test** data — a leak we will not copy

---

## Slide 6 — Kwak et al. (2017) — Know Your Master
*arXiv preprint · origin of the HCRL dataset*

**THEIR POV**
- 10 drivers, KIA Soul, 23 km Seoul, **1 Hz OBD-II**; 51 features → **15** by InfoGain ranking
- min–max scaling → **mean/median/std per 60 s window** → DT/RF/KNN/MLP, 10-fold CV
- Statistical features are the win: MLP 0.747 → **0.964**
- Verification by **threshold (0.97)** → alert the owner
- >99% on all road types; parking lot lowest

**MY POV**
- Their top features are **transmission oil temperature** and **long-term fuel trim**, praised *because "the driver cannot manipulate these data"*
- 🔴 That is the error our work corrects: **if the driver can't manipulate it, it isn't behaviour** — it's session state
- 🔴 60 s windows stepping **1 s** + 10-fold CV → near-duplicate samples on both sides of every fold
- Thresholded rejection already exists (2017) → our contribution is **calibration + AUROC + scale**, not the threshold idea
- Reusable: redundancy removal → univariate ranking → normalisation → per-window statistics

---

## Slide 7 — Hu et al. (2023) — ensemble deep learning + augmentation
*IET Intelligent Transport Systems · peer-reviewed*

**THEIR POV**
- **M 1-D CNN + BLSTM** bagging ensemble, 20 drivers, 8 CAN signals — **no attention**
- Ensemble 0.9595 vs 0.9475 / 0.9133 — the gain is mostly **stability**
- Params: MLP 762k · ResNet 514k · FCN 277k · **M 1-D CNN 90k** · LSTM 6k
- Four augmentations: **sliding window · noise · timeline reversal · random drift**
- Test = **last 30%** of the drive (chronological)

**MY POV**
- **Augmentation pays most when data is scarce: +15.2 pts at 1 min, +1.3 pts at 15 min** — that is our regime
- Ranked for us: sliding window (easiest) → **drift** (may make the model invariant to slow trip-state offsets) → noise (scale per signal) → reversal (breaks causality)
- Accuracy does not track parameter count → small models are viable
- Attention is the **parallel** family; LSTM/GRU must walk the sequence step by step

---

## Slide 8 — Shin et al. (2025) — MLOps, MTF images, drift
*Electronics (MDPI) · peer-reviewed journal*

**THEIR POV**
- CAN → **Markov Transition Field images** → ResNet-18, retrained continuously on Google Cloud
- Old-data model 33–49% vs recent-data model **67–78%** → "behaviour drifts, retrain often"
- Detects **unregistered drivers** (trained on A/B/C, flags D) with multi-maneuver voting
- Only **turns** exceed 70%; straight/stop/start fail

**MY POV**
- Converting series to images gives **structure at the cost of precision** — and unlocks the CNN/ImageNet ecosystem
- ⚠️ Their "drift" experiment is really **cross-session vs same-session** (~20-month gap): the best published evidence that our same-session numbers are **upper bounds**
- Unregistered-driver detection **already exists** → our claim must be sharper: calibrated threshold, AUROC, 46 drivers, audited signals
- Featureless images for constant driving = a warning that **most of a drive is low-information**
- Borrow their visualisation habit: **t-SNE of embeddings by driver, and again by trip phase** (a visual leakage check)

---

## Slide 9 — Lee et al. (2025) — P-AttEnc: few-shot prototypes
*arXiv preprint*

**THEIR POV**
- Driver ID as **multivariate time-series classification**
- **Attention-only encoder** (87.6% fewer parameters, 44–79% faster) + **prototypical network**
- Prototype = mean embedding of a few labelled windows; classify by **Euclidean distance**
- Closed-set 99.0–99.9%; 10-way 1-shot 69.8%; "unknown drivers 65.7%"

**MY POV**
- The **mechanism transfers directly**: Mantis embeddings → per-driver prototype → nearest-prototype matching = **enrollment without retraining**
- ⚠️ "65.7% on unknown drivers" is a **2-way** test — chance is 50%
- 10 drivers per dataset; 30 s windows with 50% overlap under a random split
- **No channel selection, no multi-rate handling, no sampling rate stated at all** → the gap we occupy
- Attention on CAN is **not new here** (their own related work has it) — the novelty is attention *alone* + few-shot

---

## Slide 10 — Feofanov et al. (2025/26) — Mantis: our primary model
*arXiv preprint · classification-native TSFM*

**THEIR POV**
- **4.2M parameters**, contrastive pre-training on **purely synthetic** data; input resized to 512 steps
- Beats larger models with a **frozen** encoder: UCR 0.820 vs MOMENT 0.779, Chronos-2 0.800, Catch22+ 0.797
- Out-of-distribution sensor transfer: Mantis 0.582 vs MOMENT 0.308
- Channel **adapters** (PCA or linear, d → 10) improve every multivariate dataset tested
- Best features come from an **intermediate** layer, not the last

**MY POV**
- **One channel at a time:** the encoder never sees two signals together; interaction happens only at the classifier
- **True zero-shot is impossible for identity** — their "zero-shot" still trains a classifier on labels
- **Open-set rejection needs a separate score** — nothing in Mantis provides one; that is our design work
- Its tokeniser already encodes **first-order differences** — the "jerkiness" our own RF found dominant
- ⚠️ It also encodes **unnormalised patch mean/std** → absolute levels survive → our audited signal list is still required

---

## Slide 11 — Datasets across the survey

| Dataset | Drivers | Vehicles | Data type | Rate | Route |
|---|---|---|---|---|---|
| **ORNL (ours)** | **46 usable** | 1 truck | raw J1939 → SPNs | **native (10 ms–1 s)** | fixed |
| CIAIR (2007) | **274** | 1 van | speech + video + sensors | — | naturalistic |
| KCID (2025) | 16 | 4 | raw CAN | 1,000–2,500 Hz | daily + fixed |
| Hallac (2016) | 64 | 10 | real-world sensors | — | single turn |
| HCRL (2016) | 10 | 1 | decoded OBD-II | 1 Hz | fixed |
| Barreto 19drivers | 19 | 1 | decoded OBD-II | 0.14 Hz | fixed |
| UK 19 Drivers (2021) | 19 | 1 | decoded OBD-II | 1 Hz | fixed |
| Enev (2016) | 15 | 1 | stock sensors | 60 Hz | lot + 50-mi loop |

> **Say:** Largest driver pool at native CAN rates — and the only one with a single session per driver.

---

## Slide 12 — What the literature is missing
1. **Open-set is rudimentary** — thresholds exist (Kwak 2017, Shin 2025) but none is calibrated, none reports AUROC, none at scale
2. **No foundation models** applied to CAN driver identification
3. **Same-session evaluation inflates results** (Shin: 67–78% → 33–49% across sessions)
4. **Leakage is rarely audited** — Kwak's best features are vehicle state; our own pipeline fell **99.6% → 29%** when trip artifacts were removed
5. **Multi-rate CAN is never addressed** — the datasets in use arrive pre-aligned at 1 Hz

---

## Slide 13 — Proposed approach
- **Signals:** audited set only (η² + physical reasoning; 40 SPNs excluded, max feature η² 0.47)
- **Preprocessing:** 10 Hz alignment (mean-per-100 ms decimation · zero-order hold) → non-overlapping windows (51 s native / 120 s resized) → per-window instance normalisation
- **Representation:** frozen **Mantis** embeddings (intermediate layer) → measure separability → fine-tune only if needed
- **Enrollment:** per-driver **prototype** = mean embedding of early windows
- **Open-set:** distance to nearest prototype as a **rejection score**; threshold calibrated on known drivers only; reported as **AUROC**
- **Baselines:** 9-aggregate RF (ours, 50% top-1 from 2 min) and Catch22

---

## Slide 14 — Evaluation plan
- **36 known / 10 unknown drivers**, 5 random partitions stratified by awareness group
- Within each known driver: train first 70% · 5% gap discarded · test last 25%
- Metrics: top-1/2/5 among the 36 (chance 2.8%) · **AUROC** for known vs unknown · learning curve over enrollment size
- Declared limitations: one session per driver · fixed route · one vehicle · skewed demographics

---

## Slide 15 — Timeline
| Week | Deliverable |
|---|---|
| 1 | Windowed tensor; frozen Mantis embeddings; separability measured |
| 2 | Open-set scoring + AUROC over 5 partitions; RF and Catch22 baselines |
| 3 | Fine-tuning if needed; learning curve; ablations |
| 4 | Write-up, figures, final report |
