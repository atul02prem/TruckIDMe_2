# TruckIDMe — Pipeline & Settled Decisions (methods reference)

Driver identification from J1939 CAN-bus behaviour, ORNL Driver Identification
Dataset (2014 Kenworth T270, Class 6, Fort Collins CO). This document records the
**validated, bulletproof parts of the pipeline** — the work that turns raw ORNL
SQLite/CSV into a trustworthy tensor a model can consume. Experimental/in-flux
work lives in `experiments/` and `outputs/reports/research_plan.md`.

Source paper: Lanigan et al., *Impact of Cyber Threat Awareness on Driver
Response to an Unexpected Vehicle Cyberattack* (`data/external_data/3002667.pdf`).

---

## 0. Data lineage (dimensions at each stage)

| Stage | Script | What changes it | Shape |
|---|---|---|---|
| `raw_data/` | — | 49 driver CSVs (native-rate CAN + `TimeXXX` + SparkFun GPS + VBOX + Empatica) | ~250k rows × ~306 cols |
| `processed_data/` | `build_processed_data` | keep CAN (≤ SPN 84) + SparkFun; drop VBOX/Empatica/`id`; drop `190…CAN0` dup; drop EXCLUDE_SPNS | 46 usable, ~250k × 134 |
| `interim_data/` (master timeline) | `assign_sectors` → `build_master_timeline` | GPS+`sector_id`, then CAN aligned to 10 Hz `canloggerTime` grid | 46, ~26k × 74 (mean-only) / 154 (with within-100ms aggs) |
| feature matrix | `build_feature_matrix` / windowed builders | per (driver, sector-or-window): 9 aggregates × signal | ~1,400 × 558 (sector) ; ~1,000 × 558 (120 s windows) |

46 usable drivers = 50 participants − G1S04 (excluded upstream by ORNL) −
G1S10/G1S11/G1S12 (see §2).

---

## 1. Data-source decisions (settled)

- **GPS = SparkFun (Teensy 4 + NEO-M9N), not VBOX.** VBOX is missing for 4 drivers
  (G1S15, G1S16, G2S13, G3S13); SparkFun has uniform coverage. For per-driver ID,
  uniform coverage > VBOX's sub-metre precision.
- **Master clock = `canloggerTime`.** It is the CAN-logger clock snapshotted into
  every SparkFun GPS row, so it is the one timestamp that speaks the CAN clock and
  is paired with GPS. Verified a stable bridge: `gpsTime − canloggerTime` std =
  0.023–0.046 s across all 46 drivers, 0 CAN-time columns out of range
  (`verify_canlogger_bridge`).
- **`gpsTime` is satellite UTC; `canloggerTime` is CAN-logger local (MDT).** Use
  `gpsTime` only to *validate* the clock (independent reference); use
  `canloggerTime` to *align* data (shared axis with CAN).
- **Column blocks selected by name, not position.** Raw layout is
  `[CAN … 84 Wheel Speed][VBOX][SparkFun][Empatica]`, but G3_Subject6 has SparkFun
  and VBOX swapped — so selection is by the known SparkFun column names.

## 2. Driver exclusions (settled) — `EXCLUDE_DRIVERS`

- **G1S04** — low CAN sampling frequency (ORNL flags it; the file's CAN rate is
  far below others).
- **G1S10 / G1S11 / G1S12** — `canloggerTime` defaulted to **2022-05-01** (Teensy
  RTC never synced) and GPS rows are duplicated. The J1939 clock itself is fine,
  but the canloggerTime bridge is unusable. Confirmed: all three stamped the same
  wrong date; real drive dates (from `gpsTime`/`Time91`) are 2024.

## 3. Signal exclusion & leakage audit (the core contribution)

**Principle — two questions, different tools, never conflated:**
- *Integrity* (does a signal leak **trip** identity?) → physical reasoning + **η²**
  (between-driver variance / total) + per-driver separability. **Never accuracy.**
- *Contribution* (does a signal add behaviour?) → ablation/importance, only on
  already-cleared signals.

Accuracy cannot gate leakage: leaks are exactly what inflate accuracy (the leaky
model hit 99.6%). Each driver drove once, so "style" and "trip artifact" are
entangled per signal — hence η² + physics for integrity.

**Audit loop (converged):** exclude η²≥0.99 a priori → regenerate → inspect top
feature importances → cut any top feature whose signal has η²≳0.9 → repeat until
all salient features are behavioural and low-η². Convergence check
(`verify_feature_leakage`): **0 features with η² ≥ 0.9, max feature η² = 0.468.**

**Final `EXCLUDE_SPNS` = 40**, grouped by reason:
- Cumulative counters (η²≈1.0): 245/244/918/250/182/247/235/249/236.
- Running averages (η²≈1.0): 185, 1029.
- Trip-state levels (η²≈1.0): 96 fuel, 1761 DEF.
- Ambient (weather/day): 171, 108.
- **Bursty command PGNs — standards-justified**: 898/518/4191 (PGN 0 = TSC1,
  an *external torque/speed command*, absent ~92% of the time; ffill fabricates a
  phantom override), 3544 (EOI, state-conditional countdown).
- Protocol constants: 4206 counter, 4207 checksum.
- DPF-state / thermal / ambient / electrical family (all vehicle *state*, proxy
  trip timing, not driver behaviour): 3721, 5466, 3031, 1172, 105, 110, 177, 412,
  1136, 3241, 3242, 3246, 4360, 4363, 4765, 5862, 168 battery, 975/986 fans.
- Pressures tied to driver action (brake 117/118/1087/1088, boost 102, fuel-rail
  157) are **KEPT**.

**Leakage headline:** the thermal/ambient/electrical family alone was worth ~45
percentage points of leaked accuracy (74% → 29% when removed).

## 4. Multi-rate alignment to 10 Hz (settled)

`build_master_timeline` puts every CAN signal on the `canloggerTime` 10 Hz grid:
- **Fast signals (native ≥ 30 Hz)** → **mean per 100 ms window** (downsample). The
  mean *is* a boxcar anti-alias filter applied *before* decimation — the correct
  order (Enev et al. denoise after, which is weaker). Optional experiment adds
  within-100 ms std/min/max for these (found to add ~nothing — sub-100 ms is below
  human control bandwidth).
- **Slow signals (native ≤ 10 Hz)** → **forward-fill (zero-order hold)**. This is
  literally CAN semantics — a signal holds its last value until the ECU resends
  (matches CANShield, asammdf `integer_interpolation=0`). Repetition does not
  change mean/std/min/max/median/percentiles; only jerk (`dmean/dstd`) is
  artifactual for ffilled signals.
- **Uniform schema by construction:** the fast-signal set is decided **once** from
  the reference driver (G1S01) and applied to all — never per-driver — so column
  counts never drift. `check_channel_uniformity` asserts this at every
  driver-stacking point.
- Residual null < 0.4% (leading nulls before a slow signal's first sample).

## 5. Feature aggregation (settled)

Per (driver, sector-or-window), for each kept CAN signal, **9 aggregates**:
`mean, median, std, min, max, p10, p90, dmean, dstd` (dmean/dstd = mean/std of the
absolute first difference = "jerkiness"). **Finding: jerkiness dominates feature
importance** — driving *smoothness* (throttle/torque/load modulation rate) is the
strongest fingerprint.

## 6. Evaluation / split design (settled)

- **Closed-set, driver-stratified.** NOT leave-one-driver-out (that's open-set;
  with one drive/driver it yields 0% by construction).
- **Two protocols in use:**
  - 5-fold stratified-on-driver CV (windows/sectors random) — earlier feasibility
    sweep; slightly optimistic (adjacent windows can straddle folds).
  - **Per-driver chronological (preferred): train first 70%, 5% gap discarded,
    test last 25%.** Train and test cover different route positions → the model
    must fingerprint *behaviour*, not memorise position; the gap kills
    temporal-adjacency leakage. This is the honest protocol.
- **Non-overlapping windows** (no shared ticks between train/test).
- Metrics: top-1 / top-2 / top-5 (random floor = 1/46 = 2.2%).

## 7. Sectorization (built; ID-optional; needs a fix for behavioural use)

`build_sector_map` (RDP, ε = 20 m, equirectangular projection → 32 waypoints from
G1S01) + `assign_sectors` (scipy KDTree on a 5 m-densified polyline → per-row
`sector_id` + `sector_dist_m`; median dist ~3 m). **Known limitation:** nearest-
neighbour assignment cannot disambiguate an **out-and-back on the same road**
(sectors 12↔19 overlap) or a very short segment (sector 15) — so `sector_id` is
unreliable on those. Fix = heading-aware assignment (`headingDegree` is available).
**Not used for driver ID** (fixed time windows beat sectors, 50% vs 33%); retained
for the cyberattack/route sub-study.

## 8. Guards & data-QC (settled)

- `check_channel_uniformity` (in `build_feature_matrix`) — fails loudly, naming the
  driver, if any schema drifts. Wired into every driver-stacking loader.
- `null_report` (`playground/dataqc.py`, uses `missingno`) — missingno matrix +
  bar + per-column null-% table, run after every data-altering stage.
- Experiments are self-contained in `experiments/expNN_*/` with a documented
  data-lineage README (see `.claude/skills/run-experiment/SKILL.md`).

## 9. Key corrections / facts (settled)

- **The cyberattack does NOT corrupt the J1939 data we use.** It hit only the
  *instrument-cluster CAN* (a separate bus) via a MITM Teensy; the J1939 main bus
  (SPN 84 wheel speed, 190 engine speed, 91 pedal, torque…) is **truthful
  throughout**. Confirmed: no 60 s zero-window in either 190 channel on a Control
  driver. **No attack-window masking is needed for ID.** (Earlier "spoofs speed to
  0, use GPS" guidance was wrong.)
- **The study is a 3×2 design:** awareness {Control/Aware/Aware+Protocol =
  G1/G2/G3, n=17/16/17} × experience {Standard 31 / Professional 19; professional =
  CDL or >5000 mi/yr or trained, incl. 8 firefighters}. **Experience labels are in
  the survey data and not yet used** — a candidate confounder for "G3 hardest to
  classify."
- The source paper's own analysis downsampled to **1 Hz**; we work at native CAN
  rates — higher resolution than the paper itself.

## 10. Honest results so far (leak-free)

- Sector-based RF, 9 aggregates: **~33% top-1** (46-way; 15× random).
- Windowed 120 s (random-CV): **~50% top-1 / 65% top-2 / 83% top-5** from 2 min;
  42% top-1 from 30 s; saturates by ~2 min.
- Per-tick (one 100 ms snapshot, chronological split): **16.6% top-1**.
- exp01 slow-signals-only (11 native ≤5 Hz signals, chronological): **~15–19%
  top-1** — most identity lives in the fast (resampling-requiring) signals.
- Within-100 ms aggregates: **negligible** (~+0.2 pp) — sub-100 ms is below the
  ~2 Hz human-control bandwidth (Enev/Neilson/Feng).

## 11. Open items / not-yet-bulletproof

- Controlled per-tick-vs-windowed comparison under the *same* chronological split
  (windowed number above used random CV).
- Reconcile a 98-SPN drop list the user was given (collapses data to 4 signals) vs
  the audited 40 — do NOT apply wholesale.
- Heading-aware sector assignment (if sectors are used for behaviour).
- Deep sequence model (1D-CNN/TCN) on the clean `(window, timesteps, channels)`
  tensor as a learned-feature comparison to RF.
- Open-set / cross-route evaluation (where the field is weak) — the real
  publishable frontier.
