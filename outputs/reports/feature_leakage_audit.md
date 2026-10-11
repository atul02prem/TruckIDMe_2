# TruckIDMe — Feature Leakage Audit (Stage-1 convergence check)

**Features:** 558   **Drivers:** 46
**Leak threshold:** η² ≥ 0.9
**Features at/above threshold:** 0
**Max η² across all features:** 0.468

η² here is computed on the exact per-(driver, sector) feature values the
classifier consumes. A feature that is both high-importance and high-η²
is a leak the audit has not yet removed.

**Verdict: CONVERGED — no feature has η² ≥ 0.9.**

## Top 40 features by RF importance (with η²)

| Rank | Feature | Importance | η² |
|---|---|---:|---:|
| 1 | `dstd_51 Engine Throttle Valve 1 Position 1` | 0.00660 | 0.045 |
| 2 | `std_51 Engine Throttle Valve 1 Position 1` | 0.00630 | 0.051 |
| 3 | `dstd_2979 Vehicle Acceleration Rate Limit Status` | 0.00623 | 0.358 |
| 4 | `dmean_51 Engine Throttle Valve 1 Position 1` | 0.00601 | 0.060 |
| 5 | `dmean_2979 Vehicle Acceleration Rate Limit Status` | 0.00595 | 0.305 |
| 6 | `p10_3357 Actual Maximum Available Engine - Percent Torque` | 0.00591 | 0.194 |
| 7 | `dmean_641 Engine Variable Geometry Turbocharger Actuator #1` | 0.00588 | 0.306 |
| 8 | `dstd_641 Engine Variable Geometry Turbocharger Actuator #1` | 0.00577 | 0.253 |
| 9 | `std_2979 Vehicle Acceleration Rate Limit Status` | 0.00562 | 0.315 |
| 10 | `dmean_3357 Actual Maximum Available Engine - Percent Torque` | 0.00520 | 0.193 |
| 11 | `dmean_5398 Estimated Pumping - Percent Torque` | 0.00507 | 0.239 |
| 12 | `dstd_5398 Estimated Pumping - Percent Torque` | 0.00491 | 0.123 |
| 13 | `dmean_2432 Engine Demand – Percent Torque` | 0.00490 | 0.133 |
| 14 | `mean_51 Engine Throttle Valve 1 Position 1` | 0.00487 | 0.046 |
| 15 | `mean_2978 Estimated Engine Parasitic Losses - Percent Torque` | 0.00487 | 0.462 |
| 16 | `median_3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 0.00485 | 0.217 |
| 17 | `dstd_3357 Actual Maximum Available Engine - Percent Torque` | 0.00476 | 0.164 |
| 18 | `dmean_92 Engine Percent Load At Current Speed` | 0.00473 | 0.150 |
| 19 | `dmean_513 Actual Engine - Percent Torque` | 0.00461 | 0.133 |
| 20 | `dmean_1209 Engine Exhaust Bank 1 Pressure 1` | 0.00447 | 0.235 |
| 21 | `min_2978 Estimated Engine Parasitic Losses - Percent Torque` | 0.00444 | 0.468 |
| 22 | `mean_3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 0.00438 | 0.240 |
| 23 | `mean_3216 Engine Exhaust 1 NOx 1` | 0.00430 | 0.179 |
| 24 | `dmean_3226 Aftertreatment 1 Outlet NOx 1` | 0.00428 | 0.206 |
| 25 | `dmean_91 Accelerator Pedal Position 1` | 0.00423 | 0.144 |
| 26 | `mean_3226 Aftertreatment 1 Outlet NOx 1` | 0.00423 | 0.353 |
| 27 | `p90_3216 Engine Exhaust 1 NOx 1` | 0.00410 | 0.175 |
| 28 | `dstd_92 Engine Percent Load At Current Speed` | 0.00410 | 0.084 |
| 29 | `dmean_514 Nominal Friction - Percent Torque` | 0.00410 | 0.190 |
| 30 | `mean_2979 Vehicle Acceleration Rate Limit Status` | 0.00410 | 0.061 |
| 31 | `median_3216 Engine Exhaust 1 NOx 1` | 0.00408 | 0.152 |
| 32 | `dstd_514 Nominal Friction - Percent Torque` | 0.00407 | 0.122 |
| 33 | `dstd_1209 Engine Exhaust Bank 1 Pressure 1` | 0.00404 | 0.128 |
| 34 | `dstd_512 Driver's Demand Engine - Percent Torque` | 0.00401 | 0.077 |
| 35 | `dstd_1242 Instantaneous Estimated Brake Power` | 0.00399 | 0.089 |
| 36 | `p10_2978 Estimated Engine Parasitic Losses - Percent Torque` | 0.00392 | 0.460 |
| 37 | `max_4154 Actual Engine - Percent Torque (Fractional)` | 0.00391 | 0.077 |
| 38 | `dstd_2432 Engine Demand – Percent Torque` | 0.00389 | 0.074 |
| 39 | `dstd_513 Actual Engine - Percent Torque` | 0.00386 | 0.077 |
| 40 | `median_3357 Actual Maximum Available Engine - Percent Torque` | 0.00376 | 0.169 |
