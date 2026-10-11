# Literature Review — Temporal Aggregation & Downsampling of High-Frequency CAN Signals for Driver ID

How does the driver-identification / driver-behavior literature handle unifying
multi-rate CAN signals onto a common grid, and does it justify the rate via
Nyquist / human-control bandwidth? Compiled from web + primary-source research.
Claims are marked **VERIFIED** (read from primary text) or **UNVERIFIED**
(paywalled; from search summaries — do not cite without locating the source).

## Executive summary

- **Method:** The dominant published approach for putting multi-rate CAN on a
  uniform grid is **interpolation (linear or quadratic) + decimation to a common
  rate** (usually **10 Hz**; Enev et al. used 60 Hz), **not** mean-per-fixed-bin
  aggregation. Our mean-per-100 ms approach is defensible but has no exact
  driver-ID precedent that *describes* it — the common ground is "resample to
  10 Hz, the lowest signal rate."
- **Justification:** Explicit Nyquist / human-actuation-bandwidth reasoning is
  **rare but precedented** — **Enev et al. (2016)** is the clearest example and
  directly supports our argument. Human-motor-control literature independently
  pins voluntary control bandwidth at **~1–2 Hz closed-loop, ~4–6 Hz ballistic
  ceiling**, and measured driving control spectra sit **below ~1 Hz**. So "high-
  frequency CAN variation is largely not voluntary driver behavior" is
  well-supported, even though most ML papers don't invoke it.
- **Bottom line:** The literature **supports** mean-downsampling to 10 Hz on
  bandwidth grounds. Preserving within-100 ms variance is not standard and would
  mostly capture sub-behavioral (non-voluntary) content — consistent with the
  bandwidth argument. Enev even *wavelet-denoises the high-frequency content away*.

## A. How multi-rate CAN is put on a uniform grid

| Paper | Signals & rate | Unification method | Model | Notes |
|---|---|---|---|---|
| Enev et al. 2016 | many sensors → **60 Hz** | **quadratic interpolation + decimation**, then wavelet denoising | RF / SVM etc. | 3 s windows, 48 features; explicit Nyquist (see B) |
| Martin et al. 2019 (*Sensors*) | OBD-II **1 Hz** | z-score + sliding windows (60–90 samples); **no resampling method stated** | deep learning | signal-processing "black box"; rate incidental |
| Hu et al. 2023 (*IET ITS*) | CAN+GPS → **10 Hz** | "resampled and interpolated at 10 Hz, the lowest among signals" (UNVERIFIED) | ensemble DL | rate justified by convenience, not Nyquist |
| Multi-scale CNN-LSTM papers (2025–26) | CAN | linear interpolation + forward-fill for **gaps** (UNVERIFIED) | CNN-LSTM | imputation of missing samples, not primary regularization |
| CAN IDS papers (You & Olufowobi; *Sensors* 2023) | per CAN-ID | **time windows over message timing/counts**, not signal values | IDS | different paradigm — contrast only |

**Takeaway:** driver-ID pipelines converge on **interpolation-to-a-common-rate
(usually 10 Hz)**. Fixed-bin **mean** aggregation is **not** the described norm —
our approach is legitimate but closer to "decimation with an implicit boxcar
anti-alias filter" than to what papers report.

## B. Nyquist / human-motor-bandwidth justification

### Papers that explicitly argue bandwidth / Nyquist

- **Enev, Takakuwa, Koscher, Kohno (2016), "Automobile Driver Fingerprinting,"
  PoPETs 2016(1):34–51.** VERIFIED quotes from the PDF:
  - "we resample each sensor to 60Hz by applying **quadratic interpolation and
    decimation**… we smooth each sensor stream by applying **wavelet denoising to
    remove high frequency artifacts**."
  - "the emphasis of capturing the raw values of lower frequencies was based on
    the **expected rate of actuation (highly unlikely that drivers perform many
    actions at a rate higher than 10 times per second)**. … we resample at 60Hz,
    so any data over 30Hz is a harmonic (**Nyquist criterion**)."
  - FFT features bucket power as 0–10 / 10–20 / 20–70 / >70 Hz, treating the low
    band as behaviorally informative.
  - **This is the methodological anchor for our argument.**

### Human-motor-control primary literature (supports the premise)

- **Neilson, P.D. (1972), "Speed of response or bandwidth of voluntary system
  controlling elbow position in intact man," Med. & Biol. Eng. 10(4):450–459.**
  VERIFIED: coherent closed-loop (kinaesthetic-feedback) elbow control tops out
  at **2 Hz**; **2–6 Hz** movements "must be **open-loop** (ballistic)"; voluntary
  oscillation ceiling **~4–6 Hz**, limited by muscle damping/limb inertia.
- **McRuer crossover model (McRuer & Jex 1967; reviews).** Partially verified:
  human operator holds −20 dB/dec near crossover **ω_c ≈ 4.3 rad/s ≈ 0.68 Hz**,
  delay τ ≈ 0.14 s; manual-control crossover typically **~0.3–1 Hz**. (Numeric
  values from review papers, not the 1967 original — representative, not
  universal.)
- **Feng, Bao, Sayer, LeBlanc (2016), "Spectral Power Analysis of Drivers' Gas
  Pedal Control…," Proc. HFES 60(1).** VERIFIED (1,461 × 90 s car-following
  segments): gas-pedal control power **peaks at 0.033 Hz**; **cutoff ≈ 0.94 Hz**
  (95th-pct where cumulative PSD hits 95%). Pedal control energy is essentially
  **all below ~1 Hz** — the empirical driving-specific number.
- **Steering neuromuscular / admittance studies** (Cole et al.; MDPI/Springer).
  UNVERIFIED specifics: steering perturbation excitation 0.1–1.93 Hz; arm/steering
  admittance well-fit up to ~6 Hz; some steering-assist filters use a **1 Hz
  cutoff**. Consistent: voluntary steering content ≲ a few Hz.

### Rate choices with NO bandwidth argument (contrast)
- Martin 2019: 1 Hz, no justification. Hu 2023: 10 Hz "lowest common rate."
  Field convention "resample to 10 Hz" is pragmatic, not principled.

## Bottom line for our project

1. **Our premise is well-supported.** "Drivers can't voluntarily actuate much
   above ~2 Hz closed-loop (~4–6 Hz ballistic)" — Neilson 1972, McRuer (~0.7 Hz),
   and driving-specific Feng 2016 (pedal < ~0.94 Hz).
2. **The exact move we make — Nyquist + human actuation rate to justify a CAN
   resample rate and treat higher content as noise — is precedented by Enev et
   al. (2016).** Cite it as our anchor. They go further and wavelet-denoise the
   high band away, which is stronger than our implicit boxcar filter.
3. **So mean-downsampling to 10 Hz is defensible, and preserving within-100 ms
   variance is unlikely to add driver signal** — that band is sub-voluntary
   (sensor/engine dynamics), which Enev explicitly discards. If we run the
   within-100 ms-variance ablation, the bandwidth evidence predicts little/no
   gain.
4. **Caveat to state in the paper:** mean-per-100 ms bin is decimation with an
   *implicit boxcar anti-alias filter* — cruder than a proper low-pass before
   decimation. Most driver-ID papers use interpolation and don't foreground
   anti-aliasing at all, so we can claim our approach is *more* signal-processing-
   principled than the norm, while noting a formal low-pass would be cleaner.
5. **Gap / opportunity:** no located driver-ID paper uses fixed-bin **mean**
   aggregation and justifies it via anti-aliasing. Either frame it as a minor
   methodological contribution, or switch to interpolation-to-10 Hz to match
   precedent exactly.

## C. Deep-learning driver-ID literature (context for our numbers)

**Critical framing (Kidmose et al. 2025 review, arXiv:2510.25856):** the datasets
that dominate this field (HCRL / OcsLab, KIA Soul) are **1 Hz decoded OBD-II**, and
this review explicitly critiques it — "sampling rates as low as 0.14 Hz
fundamentally fail to capture fine-grained driving behaviours" and decoded OBD-II
"introduces significant latency and information loss" vs raw CAN. **Our ORNL data
at native CAN rates is higher-resolution than most of this corpus** — a genuine
methodological advantage to state in the paper.

| Paper (year) | Drivers | Rate | Window | Model | Accuracy |
|---|---|---|---|---|---|
| Girma et al. 2019 (ICTAI) | 4–10 | 1 Hz | 16 samples, 50% overlap | 2-layer LSTM | >97% F1 |
| Zhang et al. 2019 (*Sensors*) | 10 | 1 Hz | 60–90 s, small stride | DeepConvGRU-Attention | 98.36% |
| El Mekki et al. 2019 (*IEEE TVT*) | ~10 | 1 Hz | UNVERIFIED | CNN+LSTM | ~98% (partial) |
| RCN / Ben Amor 2021 (*RAS*) | 10 | 1 Hz | UNVERIFIED | 1D ResNet | 99.3% |
| Hu et al. 2020 (*IET ITS*) | 10 | 1 Hz | UNVERIFIED | 1D CNN | UNVERIFIED |
| **Gahr et al. 2019** (arXiv) | **15 / 72** | **10 Hz** | **3.5 s (autocorr-chosen), non-overlap** | BiGRU + voting | **76% / 36%** |
| Jafarnejad et al. 2017 (ITSC) | 5/15/35 | CAN | sliding-window stat+cepstral | AdaBoost | 95/89/82% |

### How our project compares (important for positioning)

- **The 97–99% figures are on only 10 drivers at 1 Hz** — a much easier regime,
  and (critically) **none of those papers do a leakage audit** like ours. Our own
  pipeline hit 99.6% *before* we removed leaks. High headline accuracies in this
  literature should be read with that caveat.
- **Gahr et al. is the closest honest analog:** larger driver pool, 10 Hz,
  non-overlapping windows *specifically to avoid train/test leakage*, and accuracy
  reported as a multiple of random. Their **72 drivers → 36% (25× random)**; our
  **46 drivers → 50% top-1 from 2 min (~23× random)** sits in the same regime and
  is competitive.
- **Window selection:** the field tunes window length **empirically**; only Gahr
  derives it (autocorrelation of the signal → ~3.6 s). Our fixed sweep
  (30–300 s) with a saturation curve is more systematic than most.
- **Non-overlapping windows:** Gahr uses them to avoid leakage — same instinct as
  our stratified split; worth citing as precedent for our methodology.

**Bottom line C:** our contribution is differentiated not by beating 99% (that's a
10-driver / 1 Hz / un-audited number) but by being **honest at scale** — 46
drivers, native CAN, a rigorous leakage audit, and a feasibility-vs-duration
curve. Cite Gahr (10 Hz, non-overlap, per-random reporting) and Kidmose 2025
(1 Hz is inadequate) as our anchors; frame the 1 Hz / 10-driver / 99% papers as
the un-audited status quo.

## References
- Enev, Takakuwa, Koscher, Kohno (2016). Automobile Driver Fingerprinting. *PoPETs*
  2016(1):34–51. https://www.autosec.org/pubs/fingerprint.pdf
- Martin et al. (2019). A Deep Learning Framework for Driving Behavior
  Identification on In-Vehicle CAN-BUS Sensor Data. *Sensors* 19(6):1356.
  https://www.mdpi.com/1424-8220/19/6/1356
- Hu et al. (2023). Driver identification through vehicular CAN bus data: an
  ensemble deep learning approach. *IET Intelligent Transport Systems*.
  https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/itr2.12311  (UNVERIFIED specifics)
- Neilson, P.D. (1972). Speed of response or bandwidth of voluntary system
  controlling elbow position in intact man. *Med. & Biol. Eng.* 10(4):450–459.
  https://link.springer.com/article/10.1007/BF02474193
- McRuer & Jex (1967). A Review of Quasi-Linear Pilot Models. *IEEE Trans. Human
  Factors in Electronics.* (numeric values via secondary reviews)
- Feng, Bao, Sayer, LeBlanc (2016). Spectral Power Analysis of Drivers' Gas Pedal
  Control during Steady-state Car-following. *Proc. HFES* 60(1).
  https://journals.sagepub.com/doi/10.1177/1541931213601167
- Girma, Yan, Homaifar (2019). Driver Identification Based on Vehicle Telematics
  Data using LSTM-RNN. *IEEE ICTAI 2019*. https://arxiv.org/abs/1911.08030
- Zhang et al. (2019). A Deep Learning Framework for Driving Behavior
  Identification on In-Vehicle CAN-BUS Sensor Data. *Sensors* 19(6):1356.
- El Mekki, Bouhoute, Berrada (2019). Improving Driver Identification for the
  Next-Generation of In-Vehicle Software Systems. *IEEE TVT* 68(8):7406–7415.
- Ben Amor et al. (2021). Driver identification using only CAN-Bus data through an
  RCN deep learning approach. *Robotics and Autonomous Systems*. (authors UNVERIFIED)
- Hu, Liu, Gao, Wang (2020). Driver identification using 1D CNNs with vehicular
  CAN signals. *IET ITS* 14(13):1799–1809.
- Gahr et al. (2019). Driver Identification via the Steering Wheel. arXiv:1909.03953
- Jafarnejad, Castignani, Engel (2017). Towards a Real-Time Driver Identification
  Mechanism Based on Driving Sensing Data. *IEEE ITSC 2017*.
- Kidmose et al. (2025). Review of driver identification datasets. arXiv:2510.25856

_Verification: Enev, Feng, Martin, Neilson verified from primary text. Hu 2023,
steering-admittance figures, and the "10 Hz adequately captures pedal/steering/
brake" claim are UNVERIFIED (paywalled / untraced) — locate before citing._
