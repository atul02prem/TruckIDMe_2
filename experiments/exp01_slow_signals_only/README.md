# exp01 — Driver ID from natively-slow signals only (no resampling)

## Objective
Test whether drivers can be identified using **only CAN signals slow enough to
need no downsampling** (native rate ≤ 5 Hz). This sidesteps the multi-rate /
anti-aliasing question entirely — every feature comes from a signal used at its
native rate. Hypothesis: modest but above-chance accuracy, driven mainly by the
brake / boost / fuel-rail pressures (genuinely behavioural).

## Data built FROM SCRATCH (native, Option B)
Source = `data/processed_data/` (native-rate CAN + `TimeXXX` + `canloggerTime`).
No shared master timeline, no ffill, no 10 Hz grid. Windows are defined on
`canloggerTime`; each signal's raw samples are bucketed into windows by that
signal's own `TimeXXX` (same CAN-logger clock). All 9 aggregates — jerk included —
are computed on genuine native samples.

### Signals (11, native ≤ 5 Hz)
Brake pressures 117 / 118 / 1087 / 1088 (1 Hz); boost 102, fuel-rail 157, oil
100, crankcase 101, DPF 3251 / 3610 (2 Hz); turbo speed 103 (1 Hz).

### Data lineage (dimensions at each stage)
| Stage | What changes it | Shape |
|---|---|---|
| `raw_data/` | 49 driver CSVs (native CAN + Time + GPS + VBOX + Empatica) | ~250k rows × 306 cols |
| `processed_data/` | drop VBOX/Empatica/id + EXCLUDE_SPNS (audited 40) | 46 usable, ~250k × 134 |
| slow-signal filter | keep only signals with native rate ≤ 5 Hz + their Time cols | 11 signals |
| native windowing | bucket each signal's native samples into non-overlapping N-s windows by `TimeXXX`; drop trailing partial window; a signal needs ≥3 samples in a window | ~n windows/driver (≈21 @120 s, ≈87 @30 s) |
| features | 11 signals × 9 aggregates (mean, median, std, min, max, p10, p90, dmean, dstd) | **99 features / window** |
| split | per-driver chronological: train first 70% of windows, 5% gap dropped, test last 25% | X_tr ≈ 690×99, X_te ≈ 230×99 (@120 s) |
| model | RandomForest, 300 trees, seed 42 | 46 classes → top-1/2/5 |

## Reproducibility
- Source: `data/processed_data/` (audited **40-SPN** EXCLUDE_SPNS, **46** usable
  drivers after excluding G1S04, G1S10/11/12).
- Native rate threshold: ≤ 5 Hz (`SLOW_MAX_HZ`). Signal set determined once from
  G1S01 and asserted identical across drivers (`check_channel_uniformity`).
- Split: chronological 70% / 5% gap / 25% per driver. Window sizes 30/60/90/120 s.
- Model: `RandomForestClassifier(n_estimators=300, random_state=42)`, median
  imputation fit on train.

## Reproduce
```bash
python -m experiments.exp01_slow_signals_only.run
```
Writes `results.md` in this folder.

## Comparison points (46 drivers, chronological split)
- Per-tick, all 62 signals: 16.6% top-1.
- Windowed, all 62 signals (random-CV, not chronological): ~50% top-1.
- This exp (11 slow signals only): see `results.md`.

## Results
| Window (s) | Top-1 | Top-2 | Top-5 |
|---:|---:|---:|---:|
| 30 | 14.3% | 23.3% | 42.9% |
| 60 | 15.0% | 25.5% | 43.5% |
| 90 | 19.0% | 29.4% | 47.0% |
| 120 | 14.1% | 25.1% | 42.8% |

**Finding:** 11 slow signals alone → ~15–19% top-1 (7–9× random). Windowing them
barely beats a single instantaneous snapshot of *all* 62 signals (per-tick 16.6%),
so most driver identity lives in the FAST signals (pedal/RPM/torque) that this
experiment excludes. A resampling-free feature set works but costs ~35 pp vs the
full-signal windowed result. Numbers are noisy (≤6 test windows/driver at 120 s,
single split → no error bars).

