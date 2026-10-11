# TruckIDMe — Baseline Random Forest Classifier

**Cross-validation:** 5-fold, stratified on driver
**Trees per forest:** 300
**Random seed:** 42
**Features:** 558 CAN-signal aggregates (mean, median, std, min, max, p10, p90, dmean, dstd)
**Drivers:** 46

## Overall accuracy

- Per-fold: 0.3405, 0.3262, 0.3548, 0.3226, 0.3165
- Mean: **0.3321 ± 0.0138**
- Out-of-fold overall accuracy: **0.3321**

## Per-driver F1 (out-of-fold)

| Driver | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `G1S01` | 0.500 | 0.387 | 0.436 | 31 |
| `G1S02` | 0.720 | 0.581 | 0.643 | 31 |
| `G1S03` | 0.185 | 0.167 | 0.175 | 30 |
| `G1S05` | 0.355 | 0.367 | 0.361 | 30 |
| `G1S06` | 0.150 | 0.200 | 0.171 | 30 |
| `G1S07` | 0.289 | 0.367 | 0.324 | 30 |
| `G1S08` | 0.381 | 0.533 | 0.444 | 30 |
| `G1S09` | 0.263 | 0.333 | 0.294 | 30 |
| `G1S13` | 0.318 | 0.233 | 0.269 | 30 |
| `G1S14` | 0.538 | 0.677 | 0.600 | 31 |
| `G1S15` | 0.250 | 0.233 | 0.241 | 30 |
| `G1S16` | 0.400 | 0.333 | 0.364 | 30 |
| `G1S17` | 0.200 | 0.133 | 0.160 | 30 |
| `G2S01` | 0.667 | 0.667 | 0.667 | 30 |
| `G2S02` | 0.344 | 0.355 | 0.349 | 31 |
| `G2S03` | 0.200 | 0.133 | 0.160 | 30 |
| `G2S04` | 0.289 | 0.367 | 0.324 | 30 |
| `G2S05` | 0.429 | 0.300 | 0.353 | 30 |
| `G2S06` | 0.245 | 0.387 | 0.300 | 31 |
| `G2S07` | 0.640 | 0.516 | 0.571 | 31 |
| `G2S08` | 0.622 | 0.767 | 0.687 | 30 |
| `G2S09` | 0.500 | 0.516 | 0.508 | 31 |
| `G2S10` | 0.267 | 0.258 | 0.262 | 31 |
| `G2S11` | 0.350 | 0.452 | 0.394 | 31 |
| `G2S12` | 0.148 | 0.129 | 0.138 | 31 |
| `G2S13` | 0.517 | 0.500 | 0.508 | 30 |
| `G2S14` | 0.286 | 0.267 | 0.276 | 30 |
| `G2S15` | 0.316 | 0.200 | 0.245 | 30 |
| `G2S16` | 0.152 | 0.167 | 0.159 | 30 |
| `G3S01` | 0.167 | 0.138 | 0.151 | 29 |
| `G3S02` | 0.341 | 0.467 | 0.394 | 30 |
| `G3S03` | 0.282 | 0.355 | 0.314 | 31 |
| `G3S04` | 0.571 | 0.400 | 0.471 | 30 |
| `G3S05` | 0.294 | 0.323 | 0.308 | 31 |
| `G3S06` | 0.212 | 0.226 | 0.219 | 31 |
| `G3S07` | 0.111 | 0.067 | 0.083 | 30 |
| `G3S08` | 0.125 | 0.067 | 0.087 | 30 |
| `G3S09` | 0.500 | 0.742 | 0.597 | 31 |
| `G3S10` | 0.143 | 0.133 | 0.138 | 30 |
| `G3S11` | 0.548 | 0.742 | 0.630 | 31 |
| `G3S12` | 0.297 | 0.367 | 0.328 | 30 |
| `G3S13` | 0.250 | 0.133 | 0.174 | 30 |
| `G3S14` | 0.214 | 0.200 | 0.207 | 30 |
| `G3S15` | 0.087 | 0.067 | 0.075 | 30 |
| `G3S16` | 0.038 | 0.033 | 0.036 | 30 |
| `G3S17` | 0.212 | 0.233 | 0.222 | 30 |

## Per-group breakdown

| Group | n drivers | Mean per-driver F1 |
|---|---:|---:|
| G1 | 13 | 0.3449 |
| G2 | 16 | 0.3688 |
| G3 | 17 | 0.2609 |

## Top 20 features by RF importance (mean across folds)

| Rank | Feature | Importance |
|---|---|---:|
| 1 | `std_51 Engine Throttle Valve 1 Position 1` | 0.00617 |
| 2 | `dstd_2979 Vehicle Acceleration Rate Limit Status` | 0.00610 |
| 3 | `dmean_641 Engine Variable Geometry Turbocharger Actuator #1` | 0.00598 |
| 4 | `dstd_51 Engine Throttle Valve 1 Position 1` | 0.00594 |
| 5 | `dmean_51 Engine Throttle Valve 1 Position 1` | 0.00592 |
| 6 | `dmean_2979 Vehicle Acceleration Rate Limit Status` | 0.00589 |
| 7 | `p10_3357 Actual Maximum Available Engine - Percent Torque` | 0.00577 |
| 8 | `dstd_641 Engine Variable Geometry Turbocharger Actuator #1` | 0.00551 |
| 9 | `mean_2978 Estimated Engine Parasitic Losses - Percent Torque` | 0.00520 |
| 10 | `std_2979 Vehicle Acceleration Rate Limit Status` | 0.00514 |
| 11 | `dmean_3357 Actual Maximum Available Engine - Percent Torque` | 0.00502 |
| 12 | `dmean_5398 Estimated Pumping - Percent Torque` | 0.00496 |
| 13 | `mean_51 Engine Throttle Valve 1 Position 1` | 0.00484 |
| 14 | `dmean_1209 Engine Exhaust Bank 1 Pressure 1` | 0.00470 |
| 15 | `dmean_2432 Engine Demand – Percent Torque` | 0.00469 |
| 16 | `dstd_5398 Estimated Pumping - Percent Torque` | 0.00462 |
| 17 | `dmean_92 Engine Percent Load At Current Speed` | 0.00456 |
| 18 | `median_3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 0.00448 |
| 19 | `p90_3216 Engine Exhaust 1 NOx 1` | 0.00443 |
| 20 | `dstd_3357 Actual Maximum Available Engine - Percent Torque` | 0.00433 |
