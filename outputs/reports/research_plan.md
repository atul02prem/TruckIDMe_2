# TruckIDMe — Research Plan & Methodology Log

Driver identification from J1939 CAN behaviour (ORNL dataset, 46 usable drivers,
2014 Kenworth T270). This document is the living methodology record — update it
as decisions are made.

## Core methodological principle

Two questions must be answered with **different tools** and never conflated:

| Question | Right tool | WRONG tool |
|---|---|---|
| **Integrity** — does a signal leak *trip* identity? | Physical reasoning + η² (between-driver / total variance) + per-driver separability | ❌ accuracy delta |
| **Contribution** — does a signal add *behavioural* power? | Ablation / feature importance (on already-cleared signals) | — |

**Why accuracy cannot gate leakage:** leaks are exactly the signals that inflate
accuracy (the leaky model hit 99.86%). Selecting features by "does accuracy go
up" systematically re-admits every leak. Integrity must be settled *before* any
accuracy-based selection.

Each driver drove **once**, so "genuine style" and "trip artifact" are entangled
for any single signal — that is why we lean on physical reasoning + η² for
integrity, not model performance.

## Stage 1 — Leakage elimination (do this FIRST, until satisfied)

Iterative audit loop; eliminate rather than add signals one at a time.

1. Exclude only the unambiguous leaks a priori: **η² ≥ 0.99** (cumulative
   counters, running averages, fuel/DEF levels). Also hold out, for reasons
   orthogonal to leakage: the 4 **bursty** signals (ffill-unreliable, ~92% null)
   and the 2 **protocol constants** (message counter/checksum, zero variance).
2. Regenerate the pipeline once with everything else re-introduced.
3. Train the baseline classifier; inspect the **top-20 feature importances**.
4. For each salient feature, check its signal's η² (already computed) and
   per-driver boxplot. **Any top feature with η² ≳ 0.9 is a trip artifact** →
   add its SPN to the exclusion list.
5. Retrain. Repeat 3–5 until every salient feature is (a) behaviourally
   interpretable and (b) low-η².
6. Record the converged exclusion list and the honest accuracy.

Narrative for the paper: *"We iteratively removed features the model relied upon
that per-driver separability analysis (η²) identified as trip artifacts, until
all salient features were behaviourally interpretable."*

## Stage 2 — Feature engineering (only AFTER Stage 1 converges)

- Richer per-sector aggregates (percentiles p10/p50/p90, first-difference
  "jerkiness") — add only if accuracy plateaus.
- Correlation / VIF pruning among the clean signal pool for parsimony.
- Model comparison (RF vs XGBoost), hyperparameter tuning.
- Cyberattack-window handling; ε sensitivity for sectorization.
- Per-group analysis (G1/G2/G3) — early finding: G3 hardest to separate.

## Pipeline order (scripts, run from project root with `python -m playground.<name>`)

1. `build_processed_data`     raw_data → processed_data (drops EXCLUDE_SPNS)
2. `assign_sectors`           processed GPS → interim_data (GPS + sector_id)
3. `build_master_timeline`    interim + processed CAN → 10 Hz master timeline
4. `build_feature_matrix`     master timelines → per-(driver,sector) features
5. `build_baseline_classifier` feature_matrix → 5-fold CV RF + report
   (audit loop touches only steps 1/3/4/5 — sector map is GPS-only, stable)

Sector map (`build_sector_map`, RDP ε=20 m → 32 waypoints) is GPS-only and
already fixed; it does not change when EXCLUDE_SPNS changes.

## Verification / diagnostic scripts (not in the main chain)

- `verify_canlogger_bridge`         canloggerTime ↔ CAN clock stability
- `verify_column_uniformity`        uniform 46-driver schema
- `inspect_window_alignment`        per-signal null fraction pre-ffill
- `inspect_discrete_signals`        discrete vs continuous classification
- `verification_of_excluded_spn`    η² per excluded SPN (leakage evidence)

## Status log

- Pipeline built end-to-end; leaky baseline (44 SPNs excluded) = 26.9% RF.
- η² verification of all 44 excluded SPNs complete
  (`excluded_spn_verification.md`): natural gap between η²=0.937 and 0.743.

### Fixed experiment parameters (all runs)

- **Stage-2 aggregates = 5**: mean, median, std, min, max (per CAN signal per
  sector). May reduce later; kept fixed at 5 for now so runs are comparable.
- Classifier: Random Forest, 300 trees, 5-fold CV stratified on driver, seed 42.
- Audit loop runs only `build_feature_matrix` + `build_baseline_classifier`
  (feature-stage EXCLUDE_SPNS filter; master timeline holds all 83 signals).

### Stage-1 audit log (5-aggregate series — restarted clean)

Earlier 4-aggregate runs (iter0 99.35%, iter1 70.59%) are superseded; restarting
with 5 aggregates for a consistent record.

- **Iter 0** — EXCLUDE_SPNS = 19 (η²≥0.99 leaks + 4 bursty + 2 protocol), all
  other signals in. 5 aggregates, 415 features. RF = **99.64% ± 0.39%** (leaky
  baseline). Top-17 = same trip artifacts (3721, 5466, 3031, 171, 1172). Adding
  `mean` vs the 4-agg run (99.35%) had negligible effect — leaks dominate.
- **Iter 1** — EXCLUDE_SPNS = 24 (cut the 5 η²≥0.9 leaks). 5 aggregates, 390
  features. RF = **74.18% ± 2.66%**. Top-19 = thermal/ambient/electrical STATE
  family (battery 168, barometric 108, ECU/oil/intake temps); first behavioural
  feature (2979 accel-rate-limit std) at rank 20. Per-group G1 0.847 > G2 0.713 >
  G3 0.678.
- **Iter 2** — EXCLUDE_SPNS = 40 (cut thermal/ambient/electrical-state family:
  12 temps + 108 barometric + 168 battery + 975/986 fans; pressures for
  brake/boost/fuel-rail retained). 5 aggregates, 310 features. RF = **29.27% ±
  1.44%** (13.5× the 2.17% random floor). **The thermal family was worth ~45 pp
  of leakage.** Top features now behavioural: throttle valve (51), accel-rate
  (2979), engine torque (3357/4154), air-flow (132), VGT (641). Remaining
  questionable signals (NOx 3216/3226, DPF ΔP 3251) all low-η² (0.05–0.24) — not
  leaks. Per-group G1 0.317, G2 0.329, G3 0.219 (G3 still lowest).
  **Stage 1 essentially converged** — dominant leaks gone, accuracy stable.
- **CONVERGENCE CHECK (feature_leakage_audit.md)** — η² computed per feature on
  the exact values the classifier consumes. **0 features ≥ 0.9; max η² = 0.468**
  (2978 parasitic losses). Top features all behavioural (throttle 51, pedal 91,
  torque 3357/512, air-flow 132, VGT 641, wheel speeds). **Stage 1 CONVERGED.**

## Stage-1 outcome (final)

- Final EXCLUDE_SPNS = 40 (cumulative counters, running averages, fuel/DEF
  levels, bursty, protocol, DPF-state, and the full thermal/ambient/electrical
  family). Honest leak-free RF baseline = **29.27% ± 1.44%** (13.5× random).
- Watch in Stage 2: 2978 parasitic losses (η²0.47, derived accessory/thermal —
  purity-cut candidate).

### Stage-2 log

- **9 aggregates** (added p10, p90, dmean, dstd) → 558 features. RF = **33.21% ±
  1.38%** (+3.9 pp over the 5-aggregate 29.27%). Leakage audit re-run: still
  CONVERGED (max η² 0.468, 0 ≥ 0.9) — new aggregates didn't leak. **Finding:
  jerkiness (dmean/dstd) dominates — ~13 of top-20 features. Driving smoothness
  (throttle/torque/load modulation rate) is the strongest fingerprint.**
  Per-group G1 0.345, G2 0.369, G3 0.261 (G3 still lowest). Modest overall lift
  → nearing the ceiling of per-sector + RF; next levers are model & evidence-
  pooling, not more aggregates.

- **Windowed feasibility sweep** (fixed-duration windows, not sectors) —
  accuracy vs window: 30s 42.0%, 60s 45.8%, 90s 47.1%, 120s 49.8% (all ~20× the
  2.2% random floor). **~50% top-1 from 2 min, 42% from 30 s, among 46 drivers.**
  Gentle slope → fingerprint appears within ~30 s. **Fixed windows beat
  route-sectors (49.8% vs 33.2%)** — uniform window size gives more stable
  features than variable-length sectors. Windowed approach is now the primary ID
  method; sectors retained for cyberattack/route analysis.
- **Top-k (confidence check)** — top-2 sits ~15pp above top-1 at every window
  (proves features work): 30s 42/57/77 (top1/2/5), 120s **50/65/83**. From 2 min:
  true driver in top-5 candidates 83% of the time; from 30s, 77%. Error is
  fine-grained confusion among a few similar drivers (top-5 ≫ top-1) → next
  levers are stronger model (XGBoost) + confusion-matrix analysis, not features.
- **Extended curve (30–300s)** — top-1 SATURATES by ~120s: 30→42, 60→46, 90→47,
  120→50, 180→51, 240→50, 300→51%. Flat past 2 min (240/300 within CV noise; std
  grows 2.4%→4.9% as windows/driver drop 23→9). **2 min = sweet spot: near-ceiling
  accuracy with stable estimates.** Ceiling (~50/65/83 top-1/2/5) is set by
  model+features, not data duration → raise it via model, not longer windows.
  Figure: outputs/figures/window_sweep_curve.png.

## Next Stage-2 levers

1. Final clean regen from raw with the 40-SPN list (hygiene — make processed/
   master physically match config, not just the feature-stage filter).
2. Correlation / VIF pruning (many correlated: NOx variants, torque variants).
3. Richer aggregates (percentiles, first-difference "jerkiness").
4. Model comparison (RF vs XGBoost) + hyperparameter tuning.
5. Cyberattack-window handling; per-group (G1/G2/G3) deep-dive.

## Experiments (experiments/ folder, per run-experiment skill)

- **exp01_slow_signals_only** — driver ID from 11 native ≤5 Hz signals only
  (brake/boost/fuel-rail/oil pressures + turbo), native windowing, no resampling,
  chronological split. Top-1 ~15–19% (7–9× random), ~43–47% top-5. Barely beats
  per-tick-all-62 (16.6%) → fast signals carry most of the fingerprint; a
  resampling-free set costs ~35 pp. See experiments/exp01_slow_signals_only/.
