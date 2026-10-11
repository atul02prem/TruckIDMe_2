# TruckIDMe — Discrete vs Continuous Signal Classification

**Source driver:** `G1_Subject1.csv`
**Threshold:** signals with fewer than 32 unique values are flagged as DISCRETE candidates.
**Signals analysed:** 83 (after applying EXCLUDE_SPNS)
**DISCRETE candidates:** 30
**Continuous:** 53

Discrete signals (state flags, gear values, mode indicators) must not be
mean-aggregated per 100 ms window — their values at transitions become
fractional and physically meaningless. Mode aggregation or last-value
would be more appropriate for these.

## DISCRETE candidates (sorted by n_unique ascending)

| # | Signal | n_unique | n_non_null | min | max | Sample values |
|---|---|---:|---:|---:|---:|---|
| 1 | `5015 Momentary Engine Maximum Power Enable` | 1 | 261,210 | 1 | 1 | 1 |
| 2 | `2945 Active Shift Console Indicator` | 2 | 26,190 | 0 | 1 | 0, 1 |
| 3 | `3239 Aftertreatment 2 Intake Dew Point` | 2 | 130,574 | 0 | 1 | 0, 1 |
| 4 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 2 | 2,617 | 60.4 | 60.8 | 60.4, 60.8 |
| 5 | `986 Engine Fan 1 Requested Percent Speed` | 2 | 5,243 | 0 | 100 | 0, 100 |
| 6 | `975 Engine Fan 1 Estimated Percent Speed` | 2 | 2,621 | 0 | 100 | 0, 100 |
| 7 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | 2 | 52,285 | 1 | 11 | 1, 11 |
| 8 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 261,210 | 0 | 1 | 0, 1 |
| 9 | `574 Transmission Shift In Process` | 2 | 261,210 | 0 | 1 | 0, 1 |
| 10 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 261,210 | 0 | 1 | 0, 1 |
| 11 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 3 | 2,617 | 5 | 7 | 5, 6, 7 |
| 12 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | 3 | 52,285 | 0 | 11 | 0, 1, 11 |
| 13 | `2979 Vehicle Acceleration Rate Limit Status` | 3 | 183,099 | 0 | 11 | 0, 1, 11 |
| 14 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | 3 | 52,285 | 0 | 11 | 0, 1, 11 |
| 15 | `4154 Actual Engine - Percent Torque (Fractional)` | 3 | 130,524 | 0 | 125 | 0, 13, 125 |
| 16 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 4 | 52,285 | 10011 | 11111 | 10011, 10111, 11011, 11111 |
| 17 | `168 Battery Potential / Power Input 1` | 5 | 5,100 | 13.95 | 14.15 | 13.95, 14, 14.05, 14.1, 14.15 |
| 18 | `526 Transmission Actual Gear Ratio` | 6 | 26,208 | 0 | 3.102 | 0, 0.712, 1, 1.406, 1.81, 3.102 |
| 19 | `523 Transmission Current Gear` | 6 | 26,208 | 0 | 5 | 0, 1, 2, 3, 4, 5 |
| 20 | `524 Transmission Selected Gear` | 6 | 26,208 | 0 | 5 | 0, 1, 2, 3, 4, 5 |
| 21 | `96 Fuel Level 1` | 8 | 2,399 | 83.2 | 86 | 83.2, 83.6, 84, 84.4, 84.8, 85.2, 85.6, 86 |
| 22 | `110 Engine Coolant Temperature` | 8 | 2,615 | 86 | 93 | 86, 87, 88, 89, 90, 91, 92, 93 |
| 23 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 8 | 130,574 | 0 | 7 | 0, 1, 2, 3, 4, 5, 6, 7 |
| 24 | `105 Engine Intake Manifold 1 Temperature` | 16 | 5,241 | 31 | 46 | 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46 |
| 25 | `1717 Actual Maximum Available Retarder - Percent Torque` | 18 | 26,150 | -82 | -65 | (many) |
| 26 | `27 Engine Exhaust Gas Recirculation 1 Valve Position` | 24 | 25,959 | 0 | 38.265 | (many) |
| 27 | `1088 Service Brake Circuit 2 Air Pressure` | 26 | 2,430 | 680 | 880 | (many) |
| 28 | `1087 Service Brake Circuit 1 Air Pressure` | 26 | 2,430 | 680 | 880 | (many) |
| 29 | `5398 Estimated Pumping - Percent Torque` | 27 | 130,728 | 0 | 26 | (many) |
| 30 | `514 Nominal Friction - Percent Torque` | 27 | 130,574 | 7 | 33 | (many) |

## Continuous signals (full count for reference)

Remaining 53 signals have ≥ 32 unique values and are treated as continuous — mean-aggregation is appropriate for these.

