# How Multi-Rate CAN Signals Are Handled — Literature & Standards Review

Deep review of (A) why J1939 signals arrive at different rates, (B) how the
driver-ID literature aligns them, (C) methods that avoid resampling, and
(D) what automotive tooling/industry actually does.

**VERIFIED** = read from primary text. **UNVERIFIED** = search snippet only;
do not cite without locating the source.

---

## A. Why the rates differ — J1939 protocol reality (VERIFIED from SAE J1939-71 Rev MAR2011)

J1939 has **no global sample clock**. Each Parameter Group (PGN) is independently
scheduled by the ECU that owns it, and J1939-71 assigns each its own
*Transmission Repetition Rate*. §5.1.6 groups parameters "with similar update
rates (to minimize unnecessary overhead)". **Multi-rate data is a design output
of the standard, not a logging artifact.**

§5.1.7.1 (verbatim): *"All transmission repetition rates defined in SAE J1939/71
are nominal rates. The actual transmission repetition rate … should be at this
rate plus/minus the 'typical' jitter … The average rate should be the nominal
value."*

### Rate tiers (counted across all 459 rate declarations in Appendix C)

| Rate | Count | Category |
|---|---|---|
| On request | ~124 | config, identification, totalizers |
| 1 s | 86 | thermal, ambient, fluid levels, electrical |
| 500 ms | 65 | intake/exhaust, fluid pressures |
| 100 ms | 38 | vehicle dynamics, driver interface, brakes |
| 50 ms | 21 | pedal / torque demand, tachograph |
| on-change composites | ~26 | switches, discrete states |
| 10 ms | 6 | transmission control |
| 20 ms | 2 (+EEC1 "normal") | engine speed & associated |

→ ~**100× spread (10 ms – 1 s)** among periodic PGNs, plus an unbounded
on-request tail. **Any fixed raster is simultaneously an upsample for some
signals and a downsample for others.**

### PGN cycle times relevant to us

| PGN | Name | J1939-71 rate | Key SPNs |
|---|---|---|---|
| 61444 EEC1 | Electronic Engine Controller 1 | **"engine speed dependent"** | 190 Engine Speed, 513, 512 |
| 61443 EEC2 | Electronic Engine Controller 2 | 50 ms preferred | **91 Accel Pedal**, 92 Load |
| 65265 CCVS1 | Cruise Control / Vehicle Speed | 100 ms | **84 Wheel Speed** |
| 65262 ET1 | Engine Temperature 1 | 1 s | 110 Coolant, 175 Oil |
| 65276 DD | Dash Display | 1 s | **96 Fuel Level** |
| 65269 AMB | Ambient Conditions | 1 s | **108 Barometric, 171 Ambient Temp** |
| 65271 VEP1 | Vehicle Electrical Power | 1 s | **168 Battery Potential** |
| 65272 TRF1 | Transmission Fluids | 1 s | **177 Trans Oil Temp** |
| 61442 ETC1 | Electronic Transmission Ctrl 1 | 10 ms | 161, 191 shaft speeds |
| 65266 LFE1 | Fuel Economy | 100 ms | 183 Fuel Rate, **51 Throttle Valve** |
| **0 TSC1** | **Torque/Speed Control 1** | command-dependent | **898, 518, 4191** |
| 64914 EOI | Engine Operating Information | 250 ms | **3544** Time Remaining |

### EEC1 is genuinely non-uniform — important nuance

J1939-71 gives **no numeric rate** for EEC1; §5.1.7.2: *"At speeds above 500 rpm,
the time from sampling to message transmission shall not exceed 12 ms… Above
1000 rpm… shall range from 5 to 30 ms."* Normal updates every 20 ms, or
**crank-angle-based hybrid scheduling**. So **SPN 190 inter-arrival time can vary
with RPM**. If our data shows RPM-correlated sampling gaps, that is
protocol-correct — *and potentially driver-discriminative, i.e. a leakage risk
worth auditing.*

### Why our bursty SPNs are silent — now standards-justified

**SPNs 898, 518, 4191 all live in PGN 0 = TSC1 (Torque/Speed Control 1)** —
VERIFIED from the standard's byte layout. TSC1 is **not a state broadcast; it is a
command from an external controller overriding the engine** (cruise, PTO, ABS
torque intervention, retarder). It is absent whenever nothing is commanding.

→ Our ~92% silence is **protocol-correct and expected**. Forward-filling them
does not merely "carry a stale value" — it **fabricates a phantom active torque
override**. SPN 3544 (EOI) is a countdown only meaningful in certain engine
operating states. **Our exclusion is standards-justified, a stronger claim than
"empirically bursty."** Their *presence/absence* is a legitimate binary event
feature.

### Sentinel values — a concrete correctness risk

§5.1.4 partitions every SPN range into valid / **error indicator** / **not
available**. §5.2: *"undefined bytes should be sent as 255 (FF₁₆)."* For a 1-byte
SPN, `0xFE` = error, `0xFF` = not available. **These are neither zero nor NaN —
decoding them as physical values silently injects garbage** (a 1-byte temperature
0xFF decodes to ~215 °C).

### No analytics guidance exists in the standard

`grep -ci "logging"` over all of J1939-71 = **0**. The standard gives **zero**
guidance on resampling, alignment, or analytics preparation. A citable gap.
The nearest staleness bound: ACC1's *"timeout … between 2.5 times to 5 times the
update rate"* — generalized from one example, not a normative rule.

---

## B. How the driver-ID literature aligns multi-rate signals (13 papers VERIFIED)

| Paper | Method | Target rate | Nyquist? |
|---|---|---|---|
| **Enev et al. 2016** (PoPETs) | **quadratic interpolation AND decimation** per-signal, then wavelet denoising | 60 Hz, justified by actuation bandwidth | **YES — the only one** |
| Hallac et al. 2016 (ITSC) | linear interpolation (upsample GPS 1→10 Hz) | 10 Hz, no justification | No |
| Gahr et al. 2019 | resample + quadratic interpolation | 10 Hz, *citational* ("consistent with prior research") | No |
| Jafarnejad 2017/2020 | **tried linear upsampling, then REVERSED it** and dropped low-rate drivers | 32 Hz native | No |
| Ezzini et al. 2018 | **mean of every ten samples** (100→10 Hz); timestamp join; dropped unsynced sensors | 1 Hz effective | No |
| Lestyán et al. 2019 | no resampling; sliding-window stats | — | No |
| **CANShield 2023** (IDS) | **forward-fill / ZOH**, defended semantically; multiple decimated "views" | multi-rate by design | No |
| Kidmose et al. 2025 | review; audits rates (0.14–20 Hz), argues too low | — | No |
| Zhang / Ullah / Fanan / Alonso-Fernandez | none needed — single-rate datasets | 1 Hz / 10 Hz | No |
| Torres et al. 2025 (*Sensors*) | **only head-to-head resampling comparison** (energy data, not vehicle) | — | **YES** |

### Key conclusions

1. **A selection effect explains the literature's silence.** Half the corpus uses
   already-uniform datasets (HCRL/OCSLab 1 Hz, single-rate loggers), so those
   papers have no alignment section. **Our J1939 truck data puts us in the
   minority that must actually decide.**
2. **Polynomial interpolation onto one grid is the dominant convention**; 10 Hz is
   the modal target, essentially never justified from signal content.
3. **Enev's ordering is arguably wrong.** He decimates, *then* wavelet-denoises.
   If aliasing is the concern, filtering must precede decimation. **Our
   mean-per-window filters and decimates in one step, in the correct order.**
4. **Forward-fill is the CAN-IDS convention, not the driver-ID one.** CANShield
   (verbatim): *"we adopt a forward-filling technique… We assume that until an ECU
   sends a further CAN message, its signals are still the same as the latest
   reported ones."* This is **literally true of CAN semantics** — a better defense
   for our ffill than statistical imputation arguments.
5. **An unacknowledged disagreement:** Jafarnejad *reversed* interpolation
   (verbatim: *"resampling and interpolating … are prone to introducing noise …
   later this decision was reversed"*) and Ezzini dropped unsynced sensors. Two
   groups chose **data loss over interpolation artifacts**, contradicting the
   Enev/Gahr/Hallac convention. Neither camp cites the other.
6. **NO paper in driver ID compares resampling strategies.** The field sweeps
   *window length* obsessively but treats resampling as fixed, unexamined
   preprocessing. **Aliasing is mentioned by exactly one paper (Enev) out of 13.**

---

## C. Methods that avoid resampling (VERIFIED) — and the CAN gap

GRU-D (Che et al. 2018, *Sci Rep* 8:6085) · Latent ODE/ODE-RNN (Rubanova et al.,
NeurIPS 2019) · Neural CDE (Kidger et al., NeurIPS 2020) · mTAND (Shukla & Marlin,
ICLR 2021) · SeFT (Horn et al., ICML 2020) · IP-Nets (ICLR 2019) · Raindrop
(ICLR 2022) · STraTS (TKDD 2022) · ContiFormer (NeurIPS 2023) · MGP-RNN
(Futoma et al., ICML 2017). Survey: Shukla & Marlin 2020, arXiv:2012.00168.

**Applied to CAN driver ID: essentially zero papers.** 8 documented search
intersections, all negative. A real gap — *but verify on Scopus before claiming it.*

**Critical caveat — CAN irregularity ≠ EHR irregularity.** In MIMIC-III, *when* a
lab is drawn is a clinician decision, so missingness is informative — that is why
GRU-D works. In J1939, PGN rates are **fixed by spec: multi-rate and asynchronous
but deterministic-periodic**, carrying no per-driver information. The honest
framing is *not* "healthcare methods transfer to CAN" but: **"CAN is a multi-rate
asynchronous source the driver-ID literature universally flattens to a uniform
grid; here is what that costs."** Genuine informative missingness exists only in
the **event-driven PGNs** — i.e. exactly our TSC1 family.

**Does resampling hurt?** Mixed. For: mTAND +9.4 AUC over impute-then-RNN;
Neural CDE +4–12 pts and flat across dropout; removing observation-intensity cost
**10.4 AUC pts** on PhysioNet sepsis. Against: Liu et al. 2025 (arXiv:2501.15330)
found irregularity cost **<3%** on human-activity data and continuous-time models
showed **no clear advantage**; SeFT loses to GRU-D on MIMIC; ViTST (series as
*images*) beats several native methods. **Do not oversell.**

Survey quote framing our exact tradeoff: *"As the discretization windows become
larger, the volume of missing data will generally decrease. However, more values
will potentially also fall within the same discretization window leading to more
aggregation. This may remove information needed…"* — **no window size avoids
both.**

**No paper systematically sweeps discretization granularity and reports the
accuracy curve.** We already have `window_sweep.md` — a cheap second contribution.

---

## D. Automotive tooling & industry practice (VERIFIED)

### ASAM MDF — the automotive standard refuses to pick a rate

MDF v4.3.0 spec (verbatim): *"ASAM MDF supports non-equidistant sampling rates and
multiple rates per file. Master channels are used for synchronization, which can
be time, angle, distance or simply index related."* Each channel group carries its
own master channel; **alignment is deferred to the consumer.** The *angle* master
domain exists precisely for crank-angle-scheduled signals (J1939-71 §5.1.7.2).

### The de-facto convention lives in the tooling — and it is TYPED

**asammdf defaults:** `integer_interpolation=0` (**repeat previous sample**),
`float_interpolation=1` (**linear**). MATLAB Vehicle Network Toolbox
`VariableContinuity`: `continuous`→linear, `step`→previous value,
`event`→**do not fill (leave missing)**.

| Signal type | Convention | Endorsed by |
|---|---|---|
| Continuous physical (temp, pressure, speed, RPM) | **linear interpolation** | asammdf default; MATLAB `continuous` |
| Discrete / state / switch | **repeat previous (ZOH)** | asammdf default; MATLAB `step` |
| Sporadic / command / event | **do not fill** | MATLAB `event`; asammdf `empty_channels='skip'` |

**Our single global `ffill` across all signal types is out of step with this
convention.**

### Industry does not use fixed grids either

- **Samsara** (verbatim): *"Samsara stores each vehicle stat as a separate
  timeseries. Each stat updates at a different frequency."* Mostly **change-
  triggered** (coolant ~every 1 °C, fuel ~every 1 %, ambient ~every 1 °C).
  Alignment primitive = `decorations`, *"the value of one stat at the time of
  another"* — an **as-of join**, not a grid.
- **Geotab** rejects fixed-rate logging: samples accelerometer at 100 Hz then
  applies **Ramer–Douglas–Peucker** curve logging (the same algorithm we use for
  sectorization). SDK: *"we cannot specify a fixed logging rate."*
- **FMS-Standard v05** (ACEA/OEM consortium) renormalizes J1939 onto a fixed tier
  set **{20 ms, 50 ms, 100 ms, 1 s, 10 s}** — direct precedent that **100 ms is a
  real standard tier**. It flattens EEC1's speed-dependent rate to 20 ms and
  converts some on-request PGNs to 1 s periodic.
- **NREL Fleet DNA** (largest public heavy-duty J1939 dataset, >2,700 vehicles):
  *"1-Hz data broadcasted over the vehicle CAN bus according to SAE J1939
  standards"* — resamples a 10 ms–1 s bus to a **flat 1 Hz**, and treats time gaps
  and engine-off values as preprocessing. **Our 100 ms is 10× finer than the
  applied-research standard.**
- **InfluxDB** downsampling aggregates: mean/sum/min/max/median/count/stddev/
  first/last. Their CAN case study notes intra-second resolution is required for
  some CAN use cases; 10 s aggregation "becomes useless."
- **UBI/insurance:** window lengths, rates, and thresholds are **proprietary and
  unpublished**. The leading survey (Arumugam & Bhargavi 2019, *J Big Data* 6:86)
  tabulates only *which* of {speed, accel, braking, cornering} each vendor uses —
  **no Hz, no windows, no statistics.** Cite fleet telematics or academia instead.
- **Library support:** only **asammdf** provides multi-rate alignment
  (`resample()`, `to_dataframe(raster=)`). `cantools`, `python-can`, `SavvyCAN`
  provide **none** — the stack expects decode → pandas.

---

## Bottom line for TruckIDMe

1. **TSC1 exclusion is standards-justified.** SPNs 898/518/4191 = PGN 0 TSC1, a
   *command* message; absence is the modal state; ffill fabricates a phantom
   override. Reframe from "empirically bursty" to the protocol argument.
2. **Check for 0xFE/0xFF sentinel leakage.** Our biggest leakage family (~45 pp,
   thermal/ambient) sits on exactly the 1 s PGNs (ET1, AMB) most likely to report
   *not available*. A driver-session that decoded 0xFF as physical would be a
   per-driver constant masquerading as signal. **Worth a verification script.**
3. **Our fill rule should be typed, not global.** Continuous → linear; discrete →
   ZOH; event → leave missing. A 1 s signal ffilled onto a 100 ms grid becomes a
   10-sample-wide constant a tree can memorize per drive — a plausible leakage
   vector in its own right.
4. **Our mean-binning is defensible and better-ordered than Enev's** (filter
   before decimate, not after) and has precedent in Ezzini's mean-of-ten.
5. **100 ms is a standard tier** (FMS-Standard) and 10× finer than NREL's 1 Hz.
6. **Nobody compares resampling strategies, and only Enev mentions aliasing** —
   both are open contributions we are positioned to make.

## Key references
- SAE J1939-71 Rev MAR2011 (cite J1939-71/J1939DA formally)
- FMS-Standard Truck Interface Description v05, 07.07.2024 — fms-standard.com
- ASAM MDF File Format Specification V4.3.0 — asam.net
- Enev et al. 2016, *Automobile Driver Fingerprinting*, PoPETs 2016(2):34–51
- Hallac et al. 2016, IEEE ITSC; arXiv:1708.04636
- Gahr et al. 2019, arXiv:1909.03953
- Jafarnejad 2017 IEEE ITSC; PhD thesis 2020, Univ. Luxembourg
- Ezzini, Berrada, Ghogho 2018, *J Big Data* 5:9, doi:10.1186/s40537-018-0118-7
- Shahriar et al. 2023 (CANShield), IEEE IoT-J; arXiv:2205.01306
- Torres, Altinses, Schwung 2025, *Sensors* 25(15):4759
- Kidmose et al. 2025, arXiv:2510.25856
- Che et al. 2018 (GRU-D), *Sci Rep* 8:6085 · Rubanova et al. NeurIPS 2019 ·
  Kidger et al. NeurIPS 2020 · Shukla & Marlin ICLR 2021 · Horn et al. ICML 2020
- Shukla & Marlin 2020 survey, arXiv:2012.00168
- Liu et al. 2025, arXiv:2501.15330 (counter-evidence)
- NREL Fleet DNA, OSTI 1865320
- Arumugam & Bhargavi 2019, *J Big Data* 6:86
