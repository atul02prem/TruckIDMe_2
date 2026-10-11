# Paper Notes — capstone literature survey

The user's own reading notes per paper, captured under five fixed headings so the
papers stay comparable, with a short critical read added where useful. Source of content for `capstone_proposal.md` §2 and the
lit-survey slides.

Status legend: ⬜ not yet discussed · 🔄 notes being added · ✅ done

---

## Dataset inventory — every dataset named across the survey (swept 2026-09-19)

Built by sweeping the full text of all 10 papers for dataset names, driver counts and
"N subjects/participants". **VERIFIED** = read in the paper's own text.
**SECONDARY** = described inside a paper's related work; the original was not read.

### A. Public driver-identification datasets

| Dataset | Drivers | Vehicles | Data type | Rate | Route | Source / status |
|---|---|---|---|---|---|---|
| **ORNL Driver ID** (**ours**) | 50 (**46 usable**) | 1 truck (Kenworth T270) | raw J1939 → SPNs | native (10 ms–1 s) | fixed 20-mi | VERIFIED; **1 session/driver**; public (OSTI 2513388) |
| **CIAIR** (Nagoya; "CAAIR/CAIR" in Enev) | **274** | 1 van (Toyota Regius) | speech + video + vehicle sensors | — | naturalistic + dialogue tasks | SECONDARY (via Enev); 76.8% cepstral ID (Miyajima/Nishiwaki); largest driver pool in the field |
| **KCID** (2025) | 16 (14 in the big traces) | 4 | **raw CAN** | 1,000–2,500 Hz | daily + fixed | VERIFIED; demographics; multi-session |
| **HCRL / OCSLab** (2016) | 10 (A–J) | 1 (Kia Soul) | decoded OBD-II (CarbigsP) | 1 Hz | 4 paths, 23 km, Seoul | VERIFIED (Kwak = origin); 94,401 records; 2 round trips each |
| **Barreto dailyRoutes** (2018) | 14 | 14 (2003–2016) | decoded OBD-II | **0.14 Hz** | daily driving | SECONDARY (via KCID); Bluetooth ELM327 → latency + packet loss |
| **Barreto 19drivers** (2018) | 19 | 1 (Chevrolet S10) | decoded OBD-II | **0.14 Hz** | fixed | SECONDARY (via KCID); github.com/cephasax/OBDdatasets |
| **AEGIS Big Data** (2019) | 3 | 1 (unknown) | decoded OBD-II + GPS | 20 Hz | not specified | SECONDARY (via KCID); highest rate among decoded sets |
| **This Car is Mine!** (2019) | 4 | 1 (Hyundai YF Sonata) | decoded OBD-II | 1 Hz | fixed | SECONDARY (via KCID / P-AttEnc) |
| **UK Driving: 19 Drivers** (2021) | 19 | 1 (Mercedes CLS) | decoded OBD-II | 1 Hz | fixed | SECONDARY (via KCID); **only public set with demographics**; ~10 h total ⇒ **~32 min/driver** |
| **Vehicular data trace** | 10 | — | CAN-bus | not stated | naturalistic | SECONDARY (via P-AttEnc); 28 h, 36 journeys |
| **hciLab driving** | 10 | — | GPS + 3-axis accel | not stated | — | SECONDARY (via P-AttEnc); 0.5 h only; no CAN |

### B. Private / not-publicly-released real-world datasets

| Study | Drivers | Vehicles | Data | Notes |
|---|---|---|---|---|
| Enev et al. 2016 | 15 (+1 for stability) | 1 (2009 sedan) | stock sensors via CAN, 60 Hz | VERIFIED; the stability set = 1 driver × 5 round trips, different days/roads (91%) |
| Lestyán et al. | **33** | 8 | **raw CAN** | SECONDARY (via KCID); raw-CAN precedent, **not public** |
| Hallac et al. 2016 | **64** | 10 | real-world sensors | SECONDARY (via Shin Table 1); single turn: 76.9% (2 drivers) → **50.1% (5 drivers)** |
| Hu et al. own (2023) | 20 | 1 | 8 CAN signals | VERIFIED; urban-road naturalistic; + HCRL as the open comparison |
| Jeong et al. / Xun et al. | 20 | — | CAN | SECONDARY (via Hu); CNN |
| Rahim et al. | 25 | — | CAN events | SECONDARY (via Hu); RF 95.89% |
| Shin et al. own (2025) | 3 + 1 intruder | 1 (Hyundai Ioniq 5) | ~300 CAN columns, 1 Hz | VERIFIED; 2023 vs 2024 sessions; ~1.4 M s/vehicle |
| Kim (2023) | — | 1 | CAN **+ LiDAR** | SECONDARY (via Shin Table 1); Recurrence-Plot images |
| Choi et al. | 9 | — | CAN | SECONDARY (via Enev); HMM, **31.45%** — attentiveness study |
| Dong et al. (ARNet) | **50** | — | **GPS** (not CAN) | SECONDARY (via P-AttEnc); **40.4% top-1 / 78.3% top-5** — closest published comparator to our scale |
| Sánchez et al. | 25 | — | acceleration → 2-D | SECONDARY (via P-AttEnc); ResNet50+GRU 71.89%; Siamese verification F1 74.09% |
| Dang et al. | — | — | — | SECONDARY (via P-AttEnc); Siamese **verification**, AUC 0.753 |

### C. Simulator datasets (not real driving — flag when comparing)

| Study | Subjects | Notes |
|---|---|---|
| Wakita et al. | **30** | SECONDARY (via Enev); follow-a-guide-vehicle task, 73% |
| Zhang et al. | 20 male | SECONDARY (via Enev); **multiple day-sessions**, same route, ~30 min each, HMM **85%** — a rare multi-session design |
| Miyajima et al. (simulator arm) | 11 | SECONDARY (via Enev); 86% cepstral |
| Driver2vec / Nervtech (Yang 2020) | — | SECONDARY (via Shin Table 1); 83.1% |
| Lee et al. 2022 | 7 | SECONDARY (via Shin Table 1); CNN + sliding window, +19.94% |

### D. Other modalities (context only)

Van Ly et al. — 2 drivers, phone inertial sensors (via Enev) · Ahmad et al. — smartphone
series → spectrogram + ResNet/GRU (via Hu) · Song (2022) — camera-based, 88.7% (via Shin).

### E. Benchmark suites used by the foundation-model papers

**Mantis / MOMENT:** UCR (128 univariate), UEA (30 multivariate; 27 used), MOMENT's
**Time Series Pile** for pre-training, plus forecasting sets (ETT, Electricity, Weather,
M3, M4, Monash, Informer).
**Human activity (Mantis):** Ego4D, HHAR (ID + OOD splits), UCI-HAR, EMOPain, MP8, MP50.
**EEG (Mantis + EEG paper):** CAP, SEDFx, Epilepsy-EEG, FingerMovements,
SelfRegulationSCP1/2, PCL, Blink; EEG paper adds PhysioNet-MI (109 subjects), SHU-MI
(25), and 8 sleep datasets (ABC, CCSHS, CFS, CHAT, HOMEPAP, MROS, SHHS, SOF — via NSRR)
plus MASS; CBraMod pre-trained on **TUEG** (1.1 M EEG samples). Mantis v2 pre-trains on
**CauKer** synthetic data.

### What the inventory tells us (for the proposal)

1. **Driver-pool size:** only CIAIR (274, speech corpus), Hallac (64), ORNL (**46 usable**),
   Lestyán (33), Wakita (30, simulator) and Dong/ARNet (50, GPS) exceed 20 drivers.
   **Among real-world CAN-only datasets, ORNL is the largest public one.**
2. **Sampling rate:** everything public except KCID and ORNL is decoded OBD-II at
   0.14–20 Hz. ORNL's native rates are second only to KCID's raw bus.
3. **Data per driver:** the UK 19-driver set averages **~32 min/driver** — our ~40 min is
   *typical*, not unusually small. Useful rebuttal if asked why we don't just collect more.
4. **Sessions per driver:** HCRL (2 round trips), KCID (multi-session), Shin (2023 + 2024),
   Zhang's simulator study (multi-day) and Enev's stability set all have repeat sessions.
   **ORNL has exactly one.** This is our sharpest limitation, and now we can name precisely
   who else has what we lack.
5. **Nothing overlaps our setting:** no public dataset combines heavy-duty J1939, native
   rates, and >20 drivers. That is the positioning claim, and it now rests on a full sweep
   rather than on the six datasets KCID happened to review.

## 1. Lanigan et al. (2025) — Impact of Cyber Threat Awareness on Driver Response ✅
*J. Transportation Security, doi:10.1007/s12198-025-00303-0; the ORNL dataset paper.
`literature_survey/3002667.pdf`*

**Published:** *Journal of Transportation Security*, 2025 (peer-reviewed). doi:10.1007/s12198-025-00303-0. Also OSTI preprint 3002667.

**1. Claim.** Awareness of a cyber threat is *not* sufficient on its own: drivers
given an explicit response protocol (an SOP) respond faster and stop reliably.
Clear response guidelines, not mere warning, change behaviour.

**2. Data.** 50 participants, Fort Collins CO, one drive each on an identical
**20-mile / 50-minute** route (major + minor roads, rural and urban). Speed limits
20–40 mph; the attack road was posted 40 mph. Vehicle: 2014 Kenworth T270 (Class 6).
Sample: 39 male / 10 female / 1 non-binary; ages 19–69 (M = 34.8, SD = 15.6); 18
(36%) held a current CDL. 3 × 2 design: awareness (Control 17 / Aware 16 /
Aware+Protocol 17) × experience (Standard / Professional).

**3. Method.** A man-in-the-middle Arduino Teensy behind the instrument cluster
injected messages so the speedometer and tachometer dropped to zero, every warning
light lit, and a 2 Hz tone sounded. **The attack hit only the instrument-cluster CAN
and the audio system — no control system (brakes, steering, power) was affected**,
because the cluster sits on a different bus from the J1939 main bus. The attack fired
at the same location for everyone — roughly halfway, on a low-traffic one-mile
stretch with a continuous shoulder — lasting 60 s, or ≥5 s after a stop.
Three dependent variables: Stop Event (speed = 0 for ≥5 s), Distance Traveled during
the attack, Reaction Time (attack onset → full accelerator release, measured on SPN 91).

**4. Result + evaluation.** Stop rates — Control: 9.09% Standard (1/11), 83.3%
Professional (5/6); Aware: 30% Standard, 100% Professional; **Aware+Protocol: 100%
for both**. Reaction time: 7.53 s (Aware+Protocol) vs 16.12 s (Aware) vs 30.29 s
(Control). Analysis: **Firth's penalized logistic regression** for Stop Event,
ANCOVA + Tukey HSD for Distance and Reaction Time. Data were **downsampled to 1 s**,
VBOX and CAN synchronised by cross-correlation, analysed in R 4.4.2.

*Why Firth's regression?* 100% of the Aware+Protocol group stopped, so group
perfectly predicts the outcome — "perfect separation". Ordinary logistic regression
diverges there (coefficients run to infinity, standard errors explode). Firth's
method adds a penalty to the likelihood that pulls estimates back toward zero,
producing finite, less biased estimates in small samples and under separation
(Puhr et al., 2017).

**5. Limitations → meaning for us.** The authors list: one road condition for all
participants; possible Hawthorne effect (a researcher rode in the passenger seat);
**one attack type only** (cluster + audio, not steering/brakes/power); limited sample
size and demographic diversity; and no study of how protocol content should be
delivered. For this project: (a) the attack leaves J1939 behaviour signals truthful,
so no attack-window masking is needed; (b) their 1 Hz downsampling is coarser than
our native-rate pipeline; (c) one drive per driver is the source of our trip
confound.

**My read (additions and one correction to the notes as given).**

- Your "stoppage distance could leak identity" instinct is worth keeping, but it is
  not leakage in the η² sense — distance travelled during the attack is *behaviour*,
  not a trip artifact. The sharper risk is **group leakage**: if a classification
  window overlaps the 60-second attack, the model can read the group's response
  pattern (G3 stops, G1 mostly doesn't) rather than the individual.
- **A likely explanation for our own G3 result.** Our baseline consistently finds G3
  (Aware+Protocol) hardest to identify. This paper shows G3 had a 100% stop rate —
  the protocol makes everyone behave the same way. Homogenised behaviour means weaker
  individual fingerprints. That connection is worth stating in the proposal.
- The attack is also **auditory**, not only visual; worth one word in the slides.
- Professionals in the Control group already stopped 83% of the time, so experience
  partly substitutes for a protocol. Their experience labels exist in the survey data
  and we have not used them — a candidate covariate for our "G3 is hardest" finding.

**Use in proposal:** §5 (dataset description, 3×2 design, attack scope), §8 (threats
to validity: single route, one drive per driver).

## 2. Kidmose et al. (2025) — KCID: A Critical Roadmap to Driver Authentication via CAN Bus ✅
*arXiv:2510.25856. `literature_survey/2510.25856v2.pdf` — **user's 3rd paper discussed***

**Published:** arXiv:2510.25856 — v1 29 Oct 2025, v2 1 Nov 2025. **Preprint, not peer-reviewed.**

**1. Claim.** Existing open-access driver-fingerprinting datasets are not good enough
to build deployable systems, for five specific reasons; the paper introduces KCID to
fix them, and frames driver authentication as **anti-theft defence-in-depth** (against
both organised theft and unauthorised/underage joyriding).

**2. Data.** A review of 6 public datasets (see tracker above) plus KCID itself: 16
drivers, **4 vehicles**, **raw CAN**, daily driving *and* a fixed-route experiment,
with demographics (age band, sex), multiple sessions, and sampling of
**1,000–2,500 Hz** on three of the vehicles.

**3. Method.** Dataset review → new dataset → an anti-theft framework with a
proof-of-concept on a single-board computer, validated in live road trials on an
unmodified vehicle.

**4. Result + evaluation.** Two deliverables rather than an accuracy number: the
comparative dataset review (Table 1) and the demonstration that CAN-based driver
authentication can run on cheap hardware in a real vehicle.

**5. Limitations → meaning for us.** 16 drivers; raw CAN needs reverse engineering;
no standard benchmark protocol proposed. For us, the value is the **critique**: it
gives us citable language for why native-rate J1939 with 46 drivers is a strong
basis, and for the limitations we must declare.

**Raw CAN vs decoded diagnostic data (§2.3) — their argument in brief.**
*Advantages of raw CAN:* **coverage** — diagnostics return only what standardised
queries ask for, while raw CAN carries every ECU message, exposing behaviour the
query set never touches; **temporal coverage** — decoded sets sample every 0.5–7 s
while a modern bus carries thousands of messages per second, so transient control
adjustments survive only in raw data; **fidelity** — diagnostic pipelines filter,
convert and aggregate, averaging out subtle differences.
*Challenges of raw CAN:* **signal relevance** — raw traffic is noisy (periodic status
messages, ECU chatter unrelated to driving) and can drown the useful signal; they
recommend filtering/feature engineering, or PCA / clustering / autoencoders;
**interpretability** — manufacturer-specific hex frames need reverse engineering.
*Also:* **Bluetooth collection (ELM327 and similar) introduces significant latency
and packet loss**, affecting both Barreto datasets and the UK 19-driver dataset;
and the diagnostic query-response cycle itself adds latency.

**Their five research gaps (§2.2.6), verbatim in substance.**
1. All public sets use **decoded OBD-II**, not raw CAN → latency and information loss.
2. **Insufficient temporal resolution** — rates as low as 0.14 Hz cannot capture
   fine-grained behaviour.
3. **Unrealistic experimental design** — fixed routes are artificial, since an
   unauthorised driver would not follow the owner's route, so route-dependent
   features are unreliable in deployment.
4. **Limited vehicle diversity** — mostly single-vehicle datasets.
5. **No demographic information** (only the UK set has it) — so nobody can test the
   hard case: distinguishing two drivers with *similar* profiles rather than a young
   man from an older woman.

**My read — one correction and two additions.**
- ⚠️ **Correction (important before this reaches a slide).** KCID does **not** use the
  terms "closed-set" or "open-set", and makes **no claim that accuracy has saturated**
  (VERIFIED by search of the full text). What it does provide is the *motivation* for
  open-set work: the anti-theft framing, plus gap 3 — authentication must work on a
  driver who does not follow the owner's route. Cite it for the motivation, and attribute
  the open-set framing to yourself, not to them. Their gap 2 also implies the opposite
  of saturation: they argue the reported accuracies rest on data too coarse to trust.
- **Their signal-relevance point is our leakage audit under another name.** They say
  raw CAN is noisy and recommend filtering or PCA. Our η² + physics audit is a stronger,
  behaviour-aware version of that step — worth positioning explicitly as a contribution.
- **Gap 3 cuts against us as well as for us.** ORNL is a fixed-route study, exactly what
  KCID calls unrealistic. Declare it: our route is constant across drivers, so the
  fingerprint we measure is style *within a shared route*, and cross-route
  generalisation remains untested. Gap 5 partly applies too: ORNL has survey
  demographics, but skewed (39 M / 10 F / 1 non-binary, one city).

**Use in proposal:** §2c (dataset critique), §3 (gap + motivation for open-set), §8
(threats: fixed route, single vehicle, demographics, one session per driver).

## 3. Enev et al. (2016) — Automobile Driver Fingerprinting ✅
*PoPETs 2016(1):34–51. `literature_survey/Automobile_Driver_Fingerprinting.pdf` — **user's 6th paper discussed***

**Published:** *Proceedings on Privacy Enhancing Technologies* 2016(1):34–51
(peer-reviewed; received Apr 2015, accepted Jul 2015). The foundational CAN-based
driver-fingerprinting paper.

**1. Claim.** Framed as a **privacy** question, not security: how much can in-car
sensor data reveal about *who* is driving? Answer: a great deal — drivers are
distinguishable from stock sensors, with little data and few sensors.

**2. Data.** 15 participants (8 male / 7 female, ages ~unspecified–47), one **2009
sedan**, each driving three segments: **parking-lot maneuvers** (7.65 min, 0.42 mi —
parallel park ×2, forward weave ×2, 3-point turn ×2, reverse weave ×2), then a
**~50-mile open-road loop** (~2 h) through Seattle covering interstate (13.8 mi),
highway (7.1 mi), shopping-mall and residential/city segments. All drives started at
the same time of day (12:30 / 13:00 PST) to normalise traffic.

**3. Method.** **Quadratic interpolation + decimation to 60 Hz**, then wavelet
denoising to strip high-frequency artifacts; sliding windows; **48 features per
sensor per window**; ensemble of SVM / Random Forest / Naive Bayes / KNN. Windows on
the 90/10 split boundary are **discarded** to stop overlapping windows leaking across
the split.

**4. Result + evaluation (their Table 3, % identification accuracy among 15 drivers):**

| Sensor(s) | Parking lot | Drive part 1 (~15 min) | Drive part 2 (~1.5 h) | All data |
|---|---:|---:|---:|---:|
| **Brake pedal alone** | 50.00 | **87.33** | **100** | 100 |
| Max torque | 75.33 | 60.67 | 100 | 91.33 |
| Steering angle | 31.33 | 64.67 | 83.33 | 86.67 |
| Accelerator pedal | 15.33 | 18.00 | 30.00 | 31.33 |
| Top 5 sensors | 84.67 | 99.33 | 100 | 100 |
| All sensors | 91.33 | 100 | 100 | 100 |

Top features across all sensors: **min, std, max, range, 4th quartile** — i.e. *range*
statistics dominate. Random Forest beat the other classifiers in 97.33% of test cases.

**5. Limitations → meaning for us.** 15 drivers, one vehicle, same time of day, no
leakage audit (see below). But the design lessons are the ones we already follow:
decimation with an anti-alias argument, discarding boundary windows, and reporting
per-sensor ablations.

**My read — answers to the user's questions.**
- ✅ **The brake-pedal claim is real, and stronger than expected:** 87.33% from ~15
  minutes of open-road driving using **one signal**, rising to 100% over the 1.5-hour
  segment. Their explanation: the brake pedal is the most *direct* record of a driver's
  action and captures the most individual execution strategy. Caveat for us: 15 drivers,
  and our brake signals are pressures (117/118/1087/1088), not pedal position — SPN 91
  is our closest direct-action analogue.
- **Maneuvers vs open-road loop — the answer to your question.** Technical maneuvers in
  a parking lot are **worse** for identification than ordinary driving: brake pedal 50%
  (lot) vs 87–100% (road); all sensors 91.33% vs 100%. Two reasons: the lot segment is
  short (7.65 min vs 15 min / 1.5 h), and prescribed maneuvers *constrain* behaviour —
  everyone parallel-parks roughly the same way — while free driving lets style express
  itself. They also showed **training on the closed course and testing on open road (and
  vice versa) still worked**, concluding that traffic context does not dominate style.
  Direct implication for us: don't expect "interesting" events (the cyberattack, sharp
  turns) to beat plain sustained driving — the opposite is likelier, and it also argues
  against over-weighting the attack window.
- ✅ **Decimation — confirmed and already ours.** They resample to 60 Hz by *quadratic
  interpolation and decimation*, justified by human actuation bandwidth ("unlikely that
  drivers perform many actions at a rate higher than 10 times per second… any data over
  30 Hz is a harmonic (Nyquist)"). Our mean-per-100 ms bin is decimation with an implicit
  boxcar anti-alias filter — applied **before** decimation, whereas they denoise
  **after**, which is the weaker ordering. This is our one clean signal-processing
  contribution over the foundational paper.
- ⚠️ **A leakage smell worth noting (and not repeating).** Their scaling value is computed
  **from the test data** in each cross-validation slice and applied to train and test
  alike. Mild, but it is test-set information entering training. Our normalisation must be
  fitted on training drivers only.
- ✅ **Fingerprint stability — an important counterweight to Shin et al.** One driver was
  re-recorded on 5 round trips on a **different road, on different days**, and was still
  identified at **91% accuracy** against the original training database. So identity
  survives session change at least for one driver — evidence that fingerprints are not
  purely session artifacts. Cite this alongside Shin's drift result; the two disagree, and
  saying so is good survey writing.
- **Figure to imitate (user's note):** their Figure 6 overlays **velocity, brake pedal and
  accelerator pedal** across a drive for three subjects, chosen as the two most similar
  and the most different pair in the dataset. Our version: speed (SPN 84) + pedal (91) +
  brake pressure (117) for two similar and two dissimilar drivers over the same route
  stretch, with the cyberattack window marked. One glance shows what "style" means.
- **CAIR = CIAIR** (Center for Integrated Acoustic Information Research, Nagoya
  University) — an in-car **speech/multimedia** corpus collected from 1999 in an
  instrumented Toyota Regius (12 microphones, 3 cameras, plus speed, RPM, pedal pressures,
  steering). Miyajima/Nishiwaki (2006–07) used it for **cepstral** driver identification:
  **76.8% among 274 subjects** — still the largest driver pool in this literature — and 86%
  among 11 subjects in a simulator. Enev's critique: expensive, uncommon instrumentation
  and prompted-dialogue tasks, unlike stock sensors in natural driving.

**Use in proposal:** §2a (foundational result; Nyquist/decimation argument), §6.2
(anti-aliasing ordering), §7 (per-sensor ablation precedent), §8 (their stability
result vs Shin's drift).

## 4. Kwak et al. (2017) — Know Your Master: Driver Profiling-based Anti-theft Method ✅
*arXiv:1704.05223. `literature_survey/1704.pdf` — **user's 7th paper; read by Claude***

**Published:** arXiv:1704.05223, 18 Apr 2017 (preprint; the work also appears in the
IEEE PST 2016 line of papers by the same group, Korea University / Soonchunhyang).

**1. Claim.** Driver verification can serve as an **anti-theft** layer: profile the
owner's driving, and alert when the current driver doesn't match. Two sub-claims —
mechanical/engine features excluded by earlier work are discriminative, and
**statistical features over a sliding window** substantially improve accuracy.

**2. Data — this paper *is* the origin of the HCRL / OCSLab dataset.** 10 drivers
(labelled A–J), one recent KIA model (Soul), **4 paths in Seoul totalling 23 km**
across three road types (city way, motor way, parking space), driven **8–11 p.m. on
weekdays** to control for time-of-day, **two round trips per driver**, from 28 July
2015. Collected over **OBD-II with a CarbigsP scanner at 1 Hz**: **51 features**,
94,401 records, 16.7 MB. Public at ocslab.hksecurity.net.

**3. Method — the feature-processing chain (the reusable part).**
1. **Redundancy removal** — drop identical/derived duplicates (e.g. engine torque vs
   its correction) and highly correlated features.
2. **Feature selection** — 51 → **15 features**, ranked by `InfoGainAttributeEval`
   (Weka Ranker, i.e. univariate mutual-information ranking).
3. **Min–max normalisation** to [0, 1] (needed because KNN uses distances).
4. **Statistical features per sliding window** — mean, median, std for each of the 15
   signals (median specifically for skewed ones) → **15 original + 45 statistical = 60
   features** per record.
5. **Sliding window of 60 s advancing 1 s at a time** (so ~59 s overlap between
   consecutive samples).
6. Classifiers: Decision Tree, Random Forest, KNN, MLP (Weka), **10-fold CV**.
7. **Verification by threshold** — a driver is accepted if similarity exceeds a
   threshold set at **0.97**; otherwise the system alerts the owner.

**4. Result + evaluation.**

| Road type | Decision Tree | Random Forest | KNN | MLP |
|---|---:|---:|---:|---:|
| City way | 0.987 | 0.963 | **0.998** | 0.948 |
| Vehicle (motor) way | 0.990 | 0.984 | **0.998** | 0.989 |
| Parking lot | 0.978 | 0.925 | **0.993** | 0.956 |

**Statistical features are worth a lot** (their Table IV): original features alone →
DT 0.938 / RF 0.844 / KNN 0.961 / MLP 0.747; adding statistical features → 0.984 /
0.957 / 0.996 / 0.964. Window size 60 s chosen as the accuracy/latency trade-off;
120 s is more accurate but slower to alert. Parking-lot accuracy is lowest, matching
Enev's finding that constrained low-speed maneuvering discriminates least.

**5. Limitations → meaning for us.** 10 drivers, 1 Hz, one vehicle, one city.

**My read — two serious methodological problems, and they are *our* argument.**
- 🔴 **Their two most discriminative features are textbook leaks by our criteria.**
  They name **"Long Term Fuel Trim Bank1"** and **"Transmission oil temperature"** as
  the most visually separating features — and then write that these are hard to defeat
  *"because the driver can not manipulate these data"*. That sentence is the whole
  problem in one line: **if the driver cannot manipulate a signal, it is not driving
  behaviour.** Transmission oil temperature belongs to the exact thermal family whose
  removal cost our own pipeline ~45 percentage points, and long-term fuel trim is a
  slow ECU adaptation value — both are session/trip state, not style. With two round
  trips per driver recorded back-to-back in one evening, these values identify the
  *session*.
- 🔴 **Temporal leakage in the evaluation.** Features are computed on 60 s windows
  advancing **1 second** at a time, then split by **10-fold cross-validation over
  records**. Adjacent samples share 59 of 60 seconds, so near-duplicates sit on both
  sides of every fold. Enev (2016) explicitly discarded boundary windows to prevent
  this; this paper does not. Together with the previous point, the >99% accuracies are
  not evidence about driver behaviour.
- ✅ **Prior art for threshold-based rejection (relevant to our open-set claim).** Their
  verification step already sets an acceptance **threshold (0.97)** on similarity, and
  alerts otherwise. So thresholded rejection in CAN driver ID dates to 2016–17; our
  contribution must be the *calibration* of that threshold (fitted on known drivers,
  never on the unknown set), a threshold-free metric (AUROC), and scale.
- ✅ **Reusable feature-processing steps.** The chain redundancy-removal → univariate
  ranking → normalisation → per-window statistics is essentially our own pipeline. Two
  concrete borrowings: (a) `InfoGain`-style univariate ranking as a *contribution*
  tool (never for integrity); (b) their finding that **median matters for skewed
  signals** — we already compute median, p10 and p90, which covers it.

**Use in proposal:** §2a (feature-engineering lineage; origin of the HCRL dataset),
§3 (leakage is rarely audited — this is the cleanest published example), §6.1b
(univariate ranking as a contribution tool).

## 5. Gahr et al. (2019) — Driver Identification via the Steering Wheel ⬜
*arXiv:1909.03953. (not in folder — obtain if cited)*

**Published:** arXiv:1909.03953, 2019 (preprint). **[VERIFY venue — check for a peer-reviewed version]**

**User's points**

**1. Claim:**

**2. Data:** (drivers / rate / sessions per driver / route)

**3. Method:**

**4. Result + evaluation:** (accuracy, split, chance level)

**5. Limitation → meaning for us:**

**My read:**

**Use in proposal:** honest large-N comparator, non-overlapping windows (§2b).

---

## 6. Hu et al. (2023) — Driver identification through vehicular CAN bus data: an ensemble deep learning approach ✅
*IET Intelligent Transport Systems. `literature_survey/IET.pdf` — **user's 4th paper discussed***

**Published:** *IET Intelligent Transport Systems*, 2023 (peer-reviewed). Received
10 Feb 2022, revised 26 Sep 2022, accepted 26 Oct 2022. doi:10.1049/itr2.12311

**1. Claim.** An **ensemble** of two deep models — a modified 1-D CNN (inception
blocks + global average pooling) and a **bidirectional LSTM** — identifies drivers
more accurately and more stably than either alone, and **four data-augmentation
methods** make it work when training data is scarce.

**2. Data.** Their own dataset of **20 drivers** (8 signals: throttle position,
engine speed, engine torque, vehicle speed, longitudinal acceleration, lateral
acceleration, steering-wheel speed, +1), normalised to [0, 1], segmented by sliding
time window. Split: ~60% train (3,145 samples) / 10% validation (350) / **last 30%
test (1,497)** — a chronological test tail. Also validated on a public CAN dataset
(HCRL, Korea University round trips, ~23 h).

**3. Method.** Bagging ensemble of M 1-D CNN + BLSTM base learners. **No attention
mechanism anywhere** (VERIFIED — confirming the user's note).

**4. Result + evaluation.** Ensemble mean accuracy **0.9595** over 7 trials (vs
0.9475 M 1-D CNN, 0.9133 BLSTM), std 0.0093 — the ensemble's gain is mostly
*stability*. On the public dataset with all four augmentations: 1-D CNN 0.8629,
LSTM 0.8146, SVM 0.5917, KNN 0.7294.

**Parameter counts (their Table 3) — useful for the architecture comparison:**

| Model | Parameters | Accuracy @50 epochs |
|---|---:|---:|
| MLP | 761,520 | 0.8094 |
| ResNet | 514,324 | 0.9349 |
| FCN | 276,500 | 0.9169 |
| **M 1-D CNN** | **89,876** | **0.9604** |
| 1-D CNN | 72,365 | 0.8971 |
| LSTM | **6,164** | 0.8639 |

**5. Limitations → meaning for us.** 20 drivers, 8 hand-picked signals (no selection
rule given, no leakage audit), single vehicle. But two things transfer directly: the
**chronological test tail** (same instinct as our split) and the **augmentation
results under data scarcity** (below).

### Data augmentation — the four methods (VERIFIED) and the scarcity result

| Method | What it does | Their implementation |
|---|---|---|
| **Up-sampling (sliding window)** | more segments from the same drive | denser/overlapping sliding windows |
| **Adding noise** | perturbs values | Gaussian, mean = 0, std = 1 |
| **Data reversal** | reverses the timeline of a segment | straight time-flip |
| **Random drifting** | adds a smooth wandering offset | controlled by max drift + number of drift points |

Training sets: **A** = original + sliding window; **B** = original + noise/reverse/drift
(3,145 + 3,145×3 = 12,580); **C** = all four (15,725).

**The result that matters to us — augmentation pays most when data is scarce:**

| Training data | Original | + sliding window | Gain |
|---|---:|---:|---:|
| 3% (1 min) | 0.2943 | 0.4464 | **+0.152** |
| 10% (3 min) | 0.7199 | 0.8158 | +0.096 |
| 30% (10 min) | 0.8892 | 0.9035 | +0.014 |
| 50% (15 min) | 0.9288 | 0.9414 | +0.013 |

**Ranked by ease of application to ORNL (easiest first) — my assessment:**
1. **Up-sampling / sliding window — easiest and highest value.** One parameter (stride)
   in our existing windowing code. ⚠️ Overlapping windows must never straddle the
   train/test boundary; generate overlap *within* the train split only, and keep the
   test tail non-overlapping.
2. **Random drifting — second, and unusually well-matched to our problem.** A smooth
   low-frequency offset is physically plausible (sensor drift), and training against it
   should make the model *invariant to slow trip-state offsets* — the exact family that
   caused our 45-point leakage. Potentially a leakage-robustness tool, not just
   augmentation.
3. **Adding noise — easy but needs care.** Their "std = 1" on [0,1]-normalised data would
   swamp the signal, so either the noise is applied pre-normalisation or the description
   is imprecise (**unclear in the paper — do not copy the number**). For us, scale noise
   per signal (e.g. a fraction of each SPN's std), since our channels have different
   physical units.
4. **Data reversal — hardest to justify, do last.** Time-flipping turns braking into
   acceleration and, on a fixed route, reverses the direction of travel. It may still
   preserve style statistics, but it breaks causality and the physical story we rely on
   for the leakage argument. Also note Mantis is pre-trained with Random Crop Resize, so
   crop/resize-style augmentation is already in its training distribution.

### Architecture comparison (for the slide) — their numbers + general properties

| Family | Parameters | Sequence handling | Speed |
|---|---|---|---|
| MLP | very large (761k here) | none — ignores order | fast but weakest |
| 1-D CNN | small (72–90k here) | local patterns, parallel over time | fast |
| ResNet / FCN | large (276–514k) | deeper local patterns | slower |
| LSTM / GRU | small per cell (6k here) | **sequential** — step *t* waits for *t−1* | slow to train, hard to parallelise |
| BLSTM | 2× LSTM | both directions | 2× the cost |
| Attention / transformer | moderate; P-AttEnc reports **87.6% fewer** than CNN+RNN baselines and 44–79% faster inference | all positions at once, long-range | **highly parallel** across the sequence; cost grows with window length² |

**My read — answers to the user's questions.**
- ✅ **"No attention here" — correct.** CNN + BLSTM ensemble only.
- ⚠️ **NCAE is not this paper.** The non-negativity-constrained autoencoder is
  **Chen et al. [20]**, cited in their related work (also cited by P-AttEnc), used to
  pick the optimal window length. The interpretability property you like comes from the
  non-negativity constraint encouraging sparse, part-based representations. Cite Chen
  et al. directly, not Hu et al.
- **Sector-wise episodic learning — good idea, but as a second experiment, not the
  first.** Building episodes from *the same sector across drivers* would force the model
  to separate drivers under a matched road context — "apples to apples", which is exactly
  the concern in `open_questions.md` Q1. Three cautions: (a) our sector assignment is
  known-unreliable on the out-and-back overlap (12↔19) and the 33 m sector 15; (b) short
  sectors give few windows per driver, and some drivers miss sectors entirely (G3S01);
  (c) sector-conditioned training bakes in the fixed route, which is precisely what KCID
  calls unrealistic — so it strengthens interpretability while weakening the deployment
  story. Also remember episodic training needs *trainable* weights: a frozen encoder
  cannot learn from episodes.

**Use in proposal:** §2b (deep-learning state of the art), §6.3 (augmentation under
scarcity), §6.2 (chronological split precedent).

## 7. Lee et al. (2025) — P-AttEnc: Prototypical Network + Attention Encoder ✅
*arXiv:2510.17250. `literature_survey/2510.17250v1.pdf` — **user's 2nd paper discussed***

**Published:** arXiv:2510.17250v1, 20 Oct 2025. **Preprint, not peer-reviewed.**

**1. Claim.** Driver identification is a **multivariate time-series classification**
problem. Two contributions: (a) AttEnc, an attention-only encoder that drops the
CNN/RNN stack and so needs far fewer parameters (they report 87.6% fewer on average,
44–79% faster inference); (b) P-AttEnc, which wraps that encoder in a **prototypical
network** so it works with very little data per driver and can handle drivers absent
from training. Motivation for data shortage matches ours: collecting per-driver
driving data is hard.

**2. Data.** Three public datasets, **10 drivers each**: OcsLab (CAN-bus, 23 hrs,
46 km), Vehicular data trace (CAN-bus, 28 hrs, 36 journeys), hciLab (GPS + 3-axis
acceleration, 0.5 hrs, 23.6 km). All are naturalistic-driving datasets on prescribed
routes. **No sampling rate is stated anywhere in the paper** (VERIFIED by search).

**3. Method.** MinMax normalisation; **30 s windows with 50% overlap**; 16-head
multi-head attention + feed-forward, one block. Stage 2: N-way K-shot episodes —
support set → mean embedding per driver = **prototype**; query points classified by
**Euclidean distance** to the nearest prototype, softmaxed; trained by minimising
negative log-probability.

**4. Result + evaluation.** Stage 1 (closed-set, 80/20 split, 5-fold CV): 99.3%
(OcsLab), 99.9% (Vehicular), 99.0% (hciLab). Stage 2 experiment I (test drivers **were**
in training): best 93.4% at 5-way 10-shot (OcsLab), 98.7% (hciLab); 10-way 1-shot
69.8%. Experiment II (test drivers **not** in training; train 6/7/8-way, test
**2-way**): 65.7% at 1-shot — **chance is 50%** on a 2-way test.

**5. Limitations → meaning for us.** 10 drivers per dataset; overlapping windows
under a random split (near-duplicate windows can sit on both sides); no leakage
audit; the unknown-driver evidence is a 2-way test. But the *mechanism* — prototypes
from embeddings — is directly reusable: **Mantis embeddings → per-driver prototype →
nearest-prototype matching**, which is our planned design.

**My read — answers to the user's questions.**
1. **"No feature engineering presented" — half right, and the paper says so
   explicitly.** For CAN-bus data they state *"There is no preprocessing if the data
   source is CAN-bus because it is assumed that CAN-bus data have sufficient features
   for the model to learn."* For GPS + acceleration they *do* hand-engineer (min, max,
   mean, 25th/50th/75th percentiles). So feature engineering is delegated to the model
   **only for CAN**, and on an *assumption*, not evidence. Their own results support
   your suspicion: the hciLab embeddings (hand-made statistical features) were **more
   distinctive** than OcsLab's raw-CAN embeddings — i.e. the hand features helped.
2. **Channel selection / filtering — confirmed absent.** The paper never reports how
   many channels are used, which signals, or any selection rule. Nothing on excluding
   leaky or cumulative signals.
3. **Multi-rate / multi-phase — confirmed not addressed.** No rate is mentioned at
   all, so alignment never arises: the datasets arrive pre-aligned and single-source.
   **This is a genuine gap we occupy** — ORNL J1939 is multi-rate (10 ms–1 s) and must
   be aligned before any model sees it.
4. **"First to use attention for CAN driver ID" — no, correct this before it reaches a
   slide.** Their own Related Works cites J. Zhang et al. using CNN+RNN+**attention**
   on OcsLab (98.36%), plus three further attention works. P-AttEnc's novelty is
   attention *alone* (no CNN/RNN, hence fewer parameters) **plus** few-shot prototypes —
   not attention itself.
5. **"How much junk can attention absorb before collapsing?"** Not answered by this
   paper, and it can't be: with no channel selection and no leakage audit, they never
   vary input quality. It is a legitimate open question — and closer to *our*
   contribution, since we can compare audited vs unaudited channel sets.
6. **Is the generalisation claim justified?** *Partly.* Supported: it works across
   three datasets of different modalities, and accuracy rises with more training
   drivers (they note more classes during training improves unseen-driver accuracy).
   Not supported: (a) the unseen-driver test is 2-way, barely above chance; (b) all
   datasets have 10 drivers; (c) **there is no cross-dataset transfer experiment** —
   training on one dataset and testing on another is the real generalisation test, and
   it is absent; (d) the parameter/latency savings are *efficiency*, not
   generalisation, but are cited in the same breath. Verdict for your slide: "promising
   mechanism, weak evidence — the generalisation claim outruns the experiments."
7. **Episodic learning (keyword noted).** Training proceeds in *episodes*: each episode
   samples N drivers × K windows as a support set, builds prototypes, and is scored on a
   query set. The model learns *how to tell drivers apart*, rather than a fixed roster.
8. **Related-work number worth stealing.** Dong et al.'s ARNet: **50 drivers → 40.4%
   top-1, 78.3% top-5**. That is the closest published comparator to our scale; our
   46-driver 50% top-1 / 83% top-5 from 2 min stands up well against it.

**Use in proposal:** §2d (few-shot lineage), §6.4 (enrollment + prototypes), §3 (gap:
no channel selection, no multi-rate handling, no leakage audit).

## 8. Goswami et al. (2024) — MOMENT — ⛔ DROPPED from the survey (2026-09-18)

User decision: leave MOMENT out of the reviewed set. Retained only as a one-line mention
in the proposal — the large general-purpose alternative that the EEG authors excluded
because its size makes fine-tuning impractical. Notes below kept for reference.

### (former entry)
*ICML 2024. `literature_survey/MOMENT_2402.03885.pdf`*

**Published:** *ICML 2024*, PMLR 235:16115–16152 (peer-reviewed). arXiv:2402.03885v3, 10 Oct 2024.

**User's points**

**1. Claim:**

**2. Data:** (drivers / rate / sessions per driver / route)

**3. Method:**

**4. Result + evaluation:** (accuracy, split, chance level)

**5. Limitation → meaning for us:**

**My read:**

**Use in proposal:** TSFM background; frozen-embedding classification (§2e, §6.3).

---

## 9. Feofanov et al. (2025/26) — Mantis: Lightweight Foundation Model for Time Series Classification ✅
*arXiv:2502.15637. `literature_survey/Mantis_2502.15637.pdf` — **user's 8th paper discussed***

**Published:** arXiv:2502.15637 — v1 Feb 2025, **v2 29 Jun 2026**. Preprint, not
peer-reviewed. Authors at Huawei Noah's Ark Lab + TU Munich; carries a
conflict-of-interest disclosure.

**1. Claim.** A **small** foundation model built specifically for time-series
**classification** beats larger general/forecasting foundation models when the encoder
is frozen, and can be used out of the box with minimal tuning.

**2. Data (pre-training).** v2 is pre-trained **exclusively on synthetic time series**
generated by CauKer (~1M sequences), deliberately avoiding overlap with the UCR/UEA
evaluation suites. v1 used 1.89M real series. Evaluated on UCR-128, UEA-27, 7 human
activity datasets and 11 EEG datasets.

**3. Method.** 4.2M parameters (2.2M after layer pruning). Input **resized to 512
steps → exactly 32 tokens**. Tokeniser combines, per patch: instance-normalised
signal, its **first-order difference**, and **unnormalised patch mean/std** encoded by
a multi-scaled scalar encoder. 6 transformer layers, 8 heads, RoPE, [CLS] token.
Pre-trained **contrastively** with Random Crop Resize augmentation. Test-time tricks:
use an **intermediate layer** rather than the final one, concatenate [CLS] with the
mean of other tokens (256 → 512 dims), self-ensembling over multiple resize lengths.

**4. Result + evaluation (frozen encoder + logistic regression / random forest).**
UCR 0.820 (vs MOMENT 0.779, Chronos-2 0.800, TiRex 0.801, NuTime 0.773, Catch22+
0.797); UEA-27 0.742 (next best NuTime 0.720); HAR average 0.756; EEG average 0.736.
**Out-of-distribution sensor transfer (HHAR-OOD): Mantis 0.582, NuTime 0.560,
Catch22+ 0.481, MOMENT 0.308.**

**5. Limitations → meaning for us.** Univariate pre-training; fixed 512-step input;
benchmarks run by the authors; classification only (no forecasting). For us it is the
primary candidate: classification-native, small enough to fine-tune, and the strongest
frozen-feature performance available.

**User's observations (recorded).**
> Mantis learns one channel at a time; the encoder runs separately on each signal and
> never sees two signals at once. True zero-shot is not possible, and open-set rejection
> needs a separate rejection score.

**My read.**
- ✅ **Channel independence — correct, and it is explicit** (§3.1): for multivariate
  input each channel goes through the encoder independently and the embeddings are
  concatenated, so the classifier input is R^(d×q). Cross-channel relationships are
  modelled only at the head. The authors defend this by citing Chronos-2 (Fig. 4a) that
  gains from cross-channel modelling "do not appear significant", and offer **channel
  adapters** (PCA or a trainable linear map, d → 10) to mix channels *before* the
  encoder — which also cuts the feature count. Adapters improved every one of 10
  multivariate datasets tested.
- ⚠️ **"True zero-shot not possible" — right conclusion, but note the terminology clash.**
  The paper *calls* its frozen-encoder setting **"zero-shot feature extraction"**, while
  still training a classifier (StandardScaler + logistic regression) on labels. So when
  we write "zero-shot" in the proposal we must say which sense we mean. A 2026 paper
  (TIC-FM, arXiv:2602.00620) argues exactly this point — that a trained classifier
  "violates the training-free premise of zero-shot".
- ✅ **Open-set rejection needs its own score — correct, and nothing in Mantis provides
  one.** The paper's entire evaluation is closed-set accuracy. The rejection rule is ours
  to design (distance to nearest prototype/centroid, calibrated on known drivers, reported
  by AUROC).
- **Three design details that matter for our pipeline.**
  1. **Input is resized, not truncated** — any window length is interpolated to 512 steps.
     A 120 s window at 10 Hz (1,200 steps) becomes ~4.3 Hz effective; a 51 s window fits
     natively. Both are worth testing.
  2. **The tokeniser already encodes first-order differences** — the same "jerkiness"
     our 9-aggregate RF found dominant (dmean/dstd ≈ 13 of the top 20 features). The model
     bakes in the feature family our own experiments identified. Good line for the proposal.
  3. ⚠️ **It also encodes *unnormalised* patch mean and std** to preserve measurement
     scale. That is a **leakage channel for us**: absolute levels are exactly how trip-state
     signals (temperatures, fuel level) identify a session. Instance normalisation alone
     would strip them; this design deliberately keeps them. Our audited signal list is
     therefore still required, and this is worth one sentence in the threats section.
- **Practical note:** best results come from an **intermediate** layer, not the last —
  so our first experiment should sweep layers rather than defaulting to the final one.

**Use in proposal:** §6.3 (primary model; channel adapters; layer choice), §8
(unnormalised scale encoding as a leakage channel), §2e (TSFM background).

## 10. Gnassounou et al. (2025) — Leveraging Generic Time Series Foundation Models for EEG Classification ✅
*arXiv:2510.27522. `literature_survey/EEG_TSFM_2510.27522.pdf` — **user's 9th paper; read by Claude***

**Published:** arXiv:2510.27522v1, 31 Oct 2025, marked "Preprint. Under review".
Not peer-reviewed. Shares authors (Feofanov, Redko, Xie) with the Mantis paper — so
it is **not independent evidence** for Mantis.

**1. Claim.** A **generic** time-series foundation model (Mantis), pre-trained on
non-neural or even purely synthetic data, transfers to EEG well enough to beat both a
standard CNN baseline (EEGNet) and **CBraMod**, a foundation model built specifically
for EEG.

**2. Data.** Two task families, all split **by subject**. BCI motor imagery:
PhysioNet-MI (109 subjects, 64 channels, 160 Hz; train subj 1–70 / val 71–89 / test
90–109) and SHU-MI (25 subjects, 32 channels, 250 Hz). Sleep staging: 8 public
datasets (ABC, CCSHS, CFS, CHAT, HOMEPAP, MASS, PhysioNet, SOF), 30-second epochs
labelled Wake/N1/N2/N3/REM, 60/20/20 subject split, **2-channel** setup. Everything
resampled to 200 Hz.

**3. Method.** **Fine-tuning**, not frozen features: Mantis + a fixed 3-layer MLP head
(ELU, dropout). AdamW, batch 64, weight decay 0.01, lr 1e-4 (5e-4 for SHU-MI), cosine
schedule with 20% warmup, gradient clipping at 1.0, early stopping (patience 3 for
BCI, 5 for sleep), max 20/50 epochs. Three initialisations compared: **random**,
**real-data pre-training**, **synthetic (CauKer) pre-training**.

**4. Result + evaluation.**
*BCI:* PhysioNet-MI balanced accuracy — EEGNet 58.14, CBraMod 64.17, Mantis 64.43
(real pre-train). SHU-MI AUC-PR — EEGNet 62.83, CBraMod 69.88, **Mantis 72.15
(synthetic pre-train)**.
*Sleep staging (weighted F1, 8 datasets):* Mantis wins every dataset, e.g. MASS
84.09 vs CBraMod 81.12 vs EEGNet 79.85; gains range from **0.3 points (CCSHS) to ~3
points (MASS)**.
*Pre-training ablation (the important one):* Mantis random-init vs pre-trained —
PhysioNet-MI 60.76 → 64.43; MASS 79.06 → 84.09; CCSHS 88.55 → 88.85. The authors'
own summary: **"the performance gains are modest, indicating substantial room for
improvement"**. Pre-training also improved **stability** — random init hit the 5-hour
limit (NaN) on CHAT, pre-trained runs did not.

**5. Limitations → meaning for us.** No open-set evaluation; same-author bias; and
their conclusion notes zero-shot on EEG remains unsolved, suggesting specialised
normalisation (Monge alignment) as future work.

### Fine-tuning vs zero-shot — the finding that shapes our plan

> "in our preliminary experiments, we have found that **freezing the encoder for EEG
> data leads to a huge decrease in performance, so fine-tuning is necessary** in this
> context. This is why we have not considered MOMENT, which is very difficult to
> fine-tune due to its large model size."

Two consequences:
1. **Frozen embeddings are unlikely to be enough on an unfamiliar signal type.** CAN
   is as far from the pre-training corpus as EEG is. Plan for fine-tuning; treat the
   frozen result as a *measurement*, not the deliverable.
2. **Model size is a capability, not a detail.** They dropped MOMENT purely because it
   was too big to fine-tune. Mantis at 4.2M parameters is fine-tunable on one GPU —
   which is why it is our primary model.

### Proposed adoption — use Mantis the way the EEG paper used it

| Their choice | Our equivalent |
|---|---|
| Fine-tune Mantis + fixed 3-layer MLP head (ELU, dropout) | Same head on our window embeddings |
| AdamW, lr 1e-4, batch 64, wd 0.01, cosine + 20% warmup, clip 1.0 | Same starting recipe — no hyper-parameter search needed for run 1 |
| Early stopping, patience 3–5 | Same |
| Compare **random init vs real pre-train vs synthetic pre-train** | **Adopt this directly** — it is the cleanest test of our core hypothesis (does a generic temporal prior help under data scarcity?) |
| Channel-independent encoding, even for 64-channel EEG | Same for our ~62 CAN signals |
| Resample everything to a common rate, then resize to 512 | 10 Hz grid → 51 s or 120 s windows → resize to 512 |

### Issues we could face (from this paper's evidence)

| Risk | Why | Mitigation |
|---|---|---|
| 🔴 **Frozen embeddings fail on CAN** | Explicit finding for EEG; e-nose paper agrees | Budget GPU time for fine-tuning in week 3; keep frozen as the cheap baseline |
| 🔴 **Their evidence is about transfer, not identity** | In EEG, subject identity is a *nuisance* — they split **by subject** so the model generalises *across* people. We do the opposite: identity **is** the label | Do not claim their results predict ours; they support "Mantis handles unfamiliar signals", not "Mantis separates individuals" |
| 🟡 **Pre-training gains may be small** | Their own ablation: +0.3 to +5 points over random init | Set expectations in the proposal; report the random-init arm honestly — a small gain is still a result |
| 🟡 **Channel count and feature blow-up** | Sleep used 2 channels, BCI up to 64; we have ~62, each giving ~512 dims | PCA channel adapter; L2-regularised head |
| 🟢 **Aggressive temporal resizing is survivable** | They compress 30 s at 200 Hz (**6,000 samples**) to 512 — a 12× squeeze — and still beat specialists | Our 120 s at 10 Hz (1,200 → 512, 2.3×) is far gentler than what already works |
| 🟢 **Synthetic pre-training is competitive** | Synthetic beat real on SHU-MI | Use the synthetic checkpoint — no overlap concerns with any benchmark |

**Use in proposal:** §2e (cross-domain transfer evidence), §6.3 (fine-tuning recipe and
the random/real/synthetic ablation), §8 (transfer-is-not-identity caveat).

## 11. Shin et al. (2025) — Driver Identification System Based on an MLOps Platform Using CAN Data ✅
*Electronics 14(6):1138. `literature_survey/electronics-14-01138.pdf` — **user's 5th paper discussed***

**Published:** *Electronics* (MDPI), vol. 14, no. 6, art. 1138, **14 March 2025** —
a peer-reviewed **journal**, not a conference. Received 10 Feb, accepted 13 Mar 2025.
doi:10.3390/electronics14061138

**1. Claim.** Driving behaviour **drifts over time**, so a static model decays; a
cloud MLOps pipeline that continuously retrains keeps accuracy up. CAN series are
turned into **Markov Transition Field (MTF)** images and classified with ResNet-18.

**2. Data.** Own collection from a **Hyundai Ioniq 5**, ~300 CAN columns (steering
angle, speed, yaw, battery state, following distance), **1 Hz**, collected over
90–120 days (~1.4 M seconds per vehicle). 3 registered drivers (A, B, C) + 1
unregistered (D). Historical data Jan–Apr 2023; recent data Sep–Dec 2024.

**3. Method.** Segment into **10 s blocks with 9 s overlap** (sliding-window
augmentation — confirms the user's point that this is a staple); classify each block
into six driving conditions (left turn, right turn, U-turn, start, stop, straight);
convert to MTF images; ResNet-18 on GCP with Pub/Sub + Composer + Vertex AI;
auto-deploy only models above 70% validation accuracy.

**4. Result + evaluation.** Two experiments.
*(a) Unregistered-driver detection:* trained on A/B/C only, evaluated on D (700
images). Only **left turn, right turn and U-turn** exceeded 70% accuracy; **start,
stop and straight failed** — MTF images of near-constant signals are static and
featureless. Decision uses **multi-maneuver voting** — a single misclassification
raises no alert; consistent misclassification across turns does.
*(b) Retraining / drift:* two models evaluated on the same recent set (Recent A, 400 images).

| Model | Left turn | Right turn | U-turn |
|---|---:|---:|---:|
| Past Included (Past A 2023 + Recent B/C) | 33.50% | 48.75% | 39.50% |
| Recent Only (Recent A/B/C) | **66.50%** | **72.50%** | **78.00%** |

**5. Limitations → meaning for us.** 3–4 drivers; 1 Hz; own non-public dataset;
turns only, so most of a drive is discarded.

**My read — checks against the source.**
- ⚠️ **Correction 1 (venue).** MDPI *Electronics* is a journal, not a conference.
- ⚠️ **Correction 2 (drift magnitude) — the opposite of your note.** The measured
  effect is **large, not low**: accuracy roughly doubles (33–49% → 67–78%). But
  *what* it measures is contestable, and this is the more interesting reading: the
  "Past Included" model contains **no recent data for Driver A** (it has Past A from
  2023 plus Recent B/C), and is tested on Recent A from 2024. The "Recent Only"
  model trains on Recent A from the **same collection period** as the test images.
  So the comparison is really **cross-session vs same-session identification**, with a
  ~20-month gap on one side. It confounds behavioural drift with ordinary session
  variability (vehicle state, season, route mix).
- ✅ **Why that matters more than drift for us.** It is a rare published quantification
  of the same-session advantage: **~35–49% cross-session vs ~67–78% same-session**.
  Our dataset has **one session per driver**, so every number we report is
  same-session — i.e. an upper bound. This is the strongest citation available for our
  trip-confound limitation, and it also implies that same-session accuracies across this
  literature are optimistic.
- ✅ **"Structure at the cost of precision"** — your phrasing, and it is right. MTF
  buckets values into quantile bins and encodes transition probabilities between them,
  so absolute magnitudes are traded for a 2-D pattern. That buys access to the CNN /
  ImageNet ecosystem and bakes in transitions the model would otherwise have to learn.
  The paper's own failure mode proves the cost: constant-value driving (straight, stop)
  produces featureless images.
- ✅ **Sliding window as a staple** — confirmed: 9 s overlap on 10 s blocks here, and
  the same technique appeared in Hu et al. (2023) and P-AttEnc (50% overlap).
- ❗ **Prior art for open-set (important for our novelty claim).** This paper *does*
  detect unregistered drivers, and P-AttEnc tests unknown drivers too. So "nobody does
  open-set on CAN" is **too strong**. What remains genuinely open: a **distance-based
  rejection score with a calibrated threshold, reported by AUROC, at 46-driver scale,
  on audited leak-free signals** — rather than a 4-class softmax over 3 drivers with
  maneuver voting, on 3 registered drivers at 1 Hz.
- ✅ **Their conclusion is citable as the user proposed:** models retrained on recent
  data identify drivers more accurately than those trained with older data.
- **t-SNE suggestion — yes, and make it do double duty.** Plot Mantis embeddings twice:
  coloured **by driver** (does identity cluster?) and coloured **by time-within-drive or
  thermal state** (does the embedding cluster by trip phase instead?). The second plot is
  a *visual leakage check*, which nothing in this literature does. Precedent exists:
  MOMENT shows class separation in embedding space, and P-AttEnc t-SNEs prototypes.

**Datasets referenced in their Table 1 (added to the tracker):** Hallac et al. 2016
(real-world, 10 vehicles / 64 drivers, single turn, 76.9% for 2 drivers → 50.1% for 5);
Driver2vec (Yang et al. 2020, **simulator**, 83.1%); Lee et al. 2022 (**simulator**, 7
drivers, CNN + sliding window, +19.94% over plain CNN); Kim 2023 (real-world CAN +
LiDAR, Recurrence Plot visualisation).

**Use in proposal:** §2b (deep learning; image conversion), §3 (prior art for
unregistered-driver detection — adjust novelty claim), §8 (same-session vs
cross-session evidence), §6 (t-SNE embedding + leakage visualisation).

## Cited in methods only

### Lubba et al. (2019) — catch22 ⬜
*Data Mining and Knowledge Discovery 33:1821–1852.*

**Published:** *Data Mining and Knowledge Discovery* 33:1821–1852, 2019 (peer-reviewed).

**User's points**

**1. Claim:**

**2. Data:** (drivers / rate / sessions per driver / route)

**3. Method:**

**4. Result + evaluation:** (accuracy, split, chance level)

**5. Limitation → meaning for us:**

**My read:**
