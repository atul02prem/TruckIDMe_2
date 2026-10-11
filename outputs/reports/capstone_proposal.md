# Open-Set Driver Identification from Heavy-Duty J1939 CAN Data using Time-Series Foundation Models

**Capstone project proposal — draft v0.1 (2026-09-17)**

> DRAFT NOTES (remove before submission): items marked **[VERIFY]** depend on the
> user's own reading of Mantis / MOMENT; items marked **[TODO]** need a number or a
> citation check.

---

## 1. Problem and motivation

Modern commercial vehicles are networked computers on wheels. The SAE J1939 bus
that coordinates a Class-6 truck's engine, transmission and brakes is also an
observation channel: every pedal press, torque request and brake application is
broadcast continuously. If a driver's *style* is measurable in that stream, two
applications follow — **authentication** (detecting unauthorised use or theft
without extra hardware) and **fleet analytics** (attributing behaviour to a driver
for coaching or insurance).

Prior work almost exclusively asks a *closed-set* question: given data from a fixed
roster of drivers, which one is driving? That framing cannot serve the security
application, where the relevant input is by definition someone the system has never
enrolled. This project addresses the **open-set** question: identify known drivers
*and* reject unknown ones.

## 2. Background and related work

**(a) Foundations of CAN-based driver fingerprinting.** Enev et al. (2016)
established that drivers are distinguishable from in-vehicle sensors, reaching 100%
on 15 drivers with hand-engineered features, and argued a signal-processing case for
resampling (Nyquist limits tied to human actuation rates). Kwak et al. (2017) built
the widely reused HCRL dataset and a statistical-feature + classifier pipeline.

**(b) Deep learning and the accuracy ceiling.** Hu et al. (2023) apply ensemble deep
learning to CAN, and comparable pipelines convert CAN streams to image
representations for CNN classifiers. Reported accuracies of 97–99% are common, but
typically on ~10 drivers at 1 Hz. Gahr et al. (2019) is the most cautious
comparator: 72 drivers, 10 Hz, non-overlapping windows chosen specifically to avoid
train/test leakage, reporting 36% — expressed as a multiple of the random baseline.

**(c) Dataset critique and the open-set framing.** Kidmose et al. (2025) review
open-access driver-fingerprinting datasets and find systemic weaknesses: decoded
OBD-II instead of raw CAN, sampling rates as low as 0.14 Hz, artificial fixed routes
and missing demographics. They introduce KCID and frame driver authentication as
anti-theft defence-in-depth — the open-set framing this project adopts.

**(d) Few-shot identification.** Lee et al. (2025) combine an attention encoder with
a prototypical network (P-AttEnc), representing each driver by the mean embedding of
a few labelled windows, and report 69.8% one-shot identification and 65.7% on
"unknown" drivers. The unknown-driver evaluation is a 2-way test (50% chance) on
10-driver datasets, so the mechanism is more convincing than the evidence.

**(e) Time-series foundation models (TSFMs).** Mantis (Feofanov et al., 2025/26) is
purpose-built for time-series **classification**: 4.2M parameters, contrastive
pre-training on purely synthetic data, channel adapters for multivariate inputs, and
the strongest frozen-encoder accuracy in the largest published comparison (UCR 0.820).
Evidence that such models transfer to signals absent from pre-training comes from
Gnassounou et al. (2025): on EEG, a fine-tuned Mantis beat both EEGNet and CBraMod, an
EEG-specific foundation model, even when pre-trained only on synthetic data. Two
qualifications carry directly into this project. First, the same authors report that
**freezing the encoder caused a large performance drop, making fine-tuning necessary** —
larger general-purpose models such as MOMENT (Goswami et al., 2024) were excluded from
their study purely because their size makes fine-tuning impractical. Second, their
pre-training gains over random initialisation were modest (+0.3 to +5 points), so the
benefit of a generic temporal prior is real but bounded.

## 3. Gap

1. **Open-set evaluation in CAN driver identification is rudimentary.** Two studies
   touch it: Shin et al. (2025) flag an unregistered driver using a softmax over three
   registered drivers with multi-maneuver voting (1 Hz, one vehicle), and Lee et al.
   (2025) report unknown-driver accuracy of 65.7% in a **2-way** test where chance is
   50%. Neither calibrates a rejection threshold, reports a threshold-free metric such
   as AUROC, or evaluates at scale. This project contributes open-set evaluation with a
   calibrated distance-based rejection score across 46 drivers on audited signals.
   **[TODO: confirm on Scopus that no stronger open-set CAN work exists]**
2. **No application of time-series foundation models to CAN driver identification.**
   TSFM classification evidence comes from UCR/UEA, HAR, EEG and e-nose data. **[TODO: confirm]**
3. **Same-session evaluation inflates reported accuracy.** Shin et al. (2025) compare
   models trained on 2023 data against models trained on same-period data, both tested on
   2024 data: accuracy falls from 67–78% to 33–49% across the session gap. Nearly all
   published results — and, unavoidably, ours — are same-session, and should be read as
   upper bounds.
4. **Leakage is rarely audited.** With one drive per driver, trip artifacts
   (odometer, fuel level, ambient and engine temperatures) separate drivers
   perfectly for non-behavioural reasons. Our own pipeline reached **99.6%** before
   these were removed and **29%** after — a ~45 percentage-point inflation traced to
   the thermal/ambient/electrical family alone. Papers reporting 97–99% without such
   an audit should be read with this in mind.

## 4. Hypothesis and research questions

**Hypothesis.** Because only ~40 minutes of data exist per driver, representations
from a model pre-trained on large time-series corpora will identify drivers more
effectively than features engineered by hand, and will support rejection of
non-enrolled drivers.

- **RQ1 (separability).** Do frozen TSFM embeddings separate drivers on audited CAN
  signals, without any task-specific training?
- **RQ2 (expert vs generic prior).** How do TSFM representations compare with
  hand-engineered features (our 9-aggregate RF baseline; Catch22) under an identical
  chronological split?
- **RQ3 (open-set).** Can a distance-based rejection rule separate 10 non-enrolled
  drivers from 36 known ones, and how is that measured (AUROC)?
- **RQ4 (data efficiency).** How does accuracy decay as labelled data per driver is
  reduced, and does the TSFM decay more slowly than the RF baseline?

## 5. Data

ORNL Driver Identification Dataset: 50 participants driving a 2014 Kenworth T270
(Class 6) on a fixed route in Fort Collins, Colorado, instrumented on the J1939 bus
at native CAN rates, with a scripted cyberattack during every drive. The study is a
3×2 design: cyber-threat awareness (Control / Aware / Aware+Protocol, n = 17/16/17)
× driving experience (Standard 31 / Professional 19).

**46 drivers are usable.** G1S04 is excluded upstream for a low CAN sampling rate;
G1S10–G1S12 are excluded because the logger's clock never synchronised (all three
stamped 2022-05-01 against a true 2024 drive date).

**Two facts that shape the design.** First, the cyberattack affected only the
separate instrument-cluster bus; J1939 signals are truthful throughout, so no
masking is required. Second, **each driver drove exactly once**, so driver identity
and trip identity are confounded — the central threat to validity (§8).

## 6. Method

**6.1 Signal selection (leakage control).** Inputs are restricted to an audited
signal set. Signals are excluded by two model-independent criteria: η²
(between-driver variance / total variance) and physical reasoning about what the
signal measures. Cumulative counters, running averages, fluid levels and the
thermal/ambient/electrical family are excluded as trip-state proxies; pressures
tied to driver action (brake, boost, fuel rail) are retained. The audit converged at
40 excluded SPNs, with no remaining feature above η² = 0.47.

**6.1b Ranking contribution (only after integrity is settled).** η² + physics decide
what a signal is *allowed* to contribute; they do not rank what it *does* contribute.
For that, on already-cleared signals only: permutation importance (model-agnostic,
as used by Enev et al.), leave-one-signal-out and leave-one-family-out ablation,
SHAP attributions, univariate ranking (mutual information, ANOVA F, Kruskal–Wallis),
redundancy pruning by correlation/VIF, and — for embeddings — per-channel linear
probes and channel-dropout sensitivity. None of these may be used to judge leakage.

**6.2 Windowing.** Signals are aligned to a 10 Hz grid (mean-per-100 ms for fast
signals, zero-order hold for slow ones — the semantics of CAN). Windows are
non-overlapping. Two lengths are compared: 51 s (512 steps, the models' native input
length) and 120 s (1,200 steps, where our RF accuracy saturates, resized to 512).

**6.3 Representations.** Three, under an identical protocol:
- **Baseline A (expert prior):** 9 aggregates per signal (mean, median, std, min,
  max, p10, p90, and mean/std of absolute first differences) + Random Forest.
- **Baseline B:** Catch22 features + the same classifier.
- **TSFM:** Mantis embeddings (intermediate layer, [CLS] + mean-token concatenation).
  Multivariate input is handled channel-independently, with a PCA channel adapter where
  the channel count demands it. Frozen embeddings are measured first; fine-tuning follows
  if frozen performance is weak, as the EEG and e-nose results suggest it will be.
  Fine-tuning follows the recipe validated on EEG: a 3-layer MLP head (ELU, dropout),
  AdamW, lr 1e-4, batch 64, weight decay 0.01, cosine schedule with 20% warmup, gradient
  clipping at 1.0 and early stopping.
- **The central ablation (answers RQ2 directly):** train the same architecture from
  **random initialisation**, from the **synthetic-data checkpoint**, and from the
  **real-data checkpoint**. The gap between random and pre-trained *is* the value of the
  generic temporal prior under data scarcity. This design is taken from Gnassounou et al.

**6.4 Enrollment and open-set scoring.** Each driver is represented by the mean
embedding (prototype) of their earliest windows. A query window is assigned to the
nearest prototype; the **distance to that prototype** is the rejection score, so a
window far from every prototype is reported as *unknown*. The threshold is
calibrated on held-out known drivers only — never on the unknown set — and results
are also reported threshold-free as AUROC.

## 7. Evaluation protocol

- **Driver partition.** 36 known / 10 unknown, repeated over 5 random partitions
  stratified by awareness group, reported as mean ± std.
- **Temporal split.** Within each known driver's drive: first 70% train, 5% discarded
  as a gap, final 25% test. Enrollment windows for unknown drivers come from the
  early portion, queries from the late portion.
- **Metrics.** Closed-set top-1/top-2/top-5 among the 36 known (random = 2.8%);
  open-set AUROC for known vs unknown; a learning curve over enrollment size.
- **Preliminary results (leak-free, existing pipeline).** Sector-based RF 33% top-1;
  120 s windows ~50% top-1 / 65% top-2 / 83% top-5 (46-way, 23× random); slow-signal
  subset 15–19%. These stand as the closed-set reference the TSFM must beat.

## 8. Threats to validity

1. **Trip confound (primary).** One drive per driver means "new driver" and "new
   day" are inseparable. An open-set detector may reject a stranger because the
   day's conditions are unfamiliar. Mitigation: the audited signal set removes the
   most direct trip proxies; the limitation is stated explicitly, and KCID — which
   records multiple sessions per driver — is identified as the dataset needed to
   settle it.
2. **Single vehicle, single route.** Results describe one truck on one route; they
   do not establish cross-vehicle generalisation.
3. **Dimensionality.** Channel-independent encoding produces a high-dimensional
   feature vector relative to the number of training windows; mitigated by channel
   adapters, regularisation and dimensionality reduction fitted on training drivers only.
4. **Concentration of the TSFM evidence base.** Much published classification-TSFM
   evidence originates from one research group; independent replications are few.

## 9. Timeline (10 weeks: 22 September – Thanksgiving week, 26 November 2026)

| Phase | Weeks | Dates | Deliverable |
|---|---|---|---|
| Foundation | 1–2 | 22 Sep – 3 Oct | Audited windowed tensor; environment + Mantis running; frozen embeddings extracted |
| Separability + baselines | 3–4 | 6 – 17 Oct | RQ1 measured (KNN / nearest-centroid, t-SNE); RF and Catch22 baselines on the identical split |
| Open-set | 5–6 | 20 – 31 Oct | Prototype enrollment, rejection score, AUROC over 5 partitions (RQ3) |
| Fine-tuning + data efficiency | 7–8 | 3 – 14 Nov | Random vs synthetic vs real pre-training ablation (RQ2); learning curve over enrollment size (RQ4) |
| Analysis + write-up | 9–10 | 17 – 26 Nov | Ablations, error analysis by group, figures, final report and defence slides |

Week 4 is the decision point: if frozen embeddings separate drivers, weeks 7–8 extend
the analysis; if they do not, weeks 7–8 become the fine-tuning effort.

## 10. References

1. Enev, M., Takakuwa, A., Koscher, K., Kohno, T. (2016). Automobile Driver Fingerprinting. *PoPETs* 2016(1):34–51.
2. Kwak, B. I., Woo, J., Kim, H. K. (2017). Know Your Master: Driver Profiling-based Anti-theft Method. arXiv:1704.05223.
3. Gahr, B., et al. (2019). Driver Identification via the Steering Wheel. arXiv:1909.03953.
4. Hu, H., et al. (2023). Driver identification through vehicular CAN bus data: an ensemble deep learning approach. *IET ITS*.
5. Lanigan, T. F., Biggs, T., Gallegos, E. E., Daily, J., Reid, E. J., Powers, S. (2025). Impact of cyber threat awareness on driver response to an unexpected vehicle cyberattack. *Journal of Transportation Security*. doi:10.1007/s12198-025-00303-0
6. Kidmose, B. E., Kidmose, A. B., Zou, C. C. (2025). A Critical Roadmap to Driver Authentication via CAN Bus (KCID). arXiv:2510.25856.
7. Lee, W.-H., Li, K.-Y., Chang, C.-Y. (2025). A Prototypical Network with an Attention-based Encoder for Drivers Identification. arXiv:2510.17250.
8. Feofanov, V., et al. (2025). Mantis: Lightweight Foundation Model for Time Series Classification. arXiv:2502.15637.
9. Gnassounou, T., et al. (2025). Leveraging Generic Time Series Foundation Models for EEG Classification. arXiv:2510.27522.
10. Shin, H., Park, W., Kim, S., Kweon, J., Moon, C. (2025). Driver Identification System Based on a Machine Learning Operations Platform Using CAN Data. *Electronics* 14(6):1138.

*Cited but not reviewed:* Lubba, C. H., et al. (2019). catch22: CAnonical Time-series
CHaracteristics. *Data Mining and Knowledge Discovery* 33:1821–1852. · Goswami, M., et al.
(2024). MOMENT: A Family of Open Time-series Foundation Models. *ICML 2024* (named only as
the large general-purpose alternative that is impractical to fine-tune at this scale).
