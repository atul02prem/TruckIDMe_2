# Value distributions and per-driver constancy — all CAN signals

**All 102 CAN signals over 46 drivers**, raw data.

Flags: 🔴 constant for every driver · 🟡 constant for **only some** drivers, or one value holding ≥ 95% of a typical drive · 🟢 varies normally.

**This report measures only** — no exclusion labels, no recommendation. The decisions that cite it live in `signal_exclusion_decisions.md`.

## Why no other instrument can answer this

η², Cramér's V, Theil's U and mutual information all pool samples across drivers to ask whether drivers differ. None of them can ask whether a signal *moved at all* in a given drive. A signal that is flat in some recordings and active in others carries a driver split in its mere variability — SPN 515 splits this cohort **9 against 37** — and that split is invisible to every pooled effect size, including the within-window spread column added to the continuous report.

`classify_signals.py` reports the signals constant across *every* driver. The **partial** case is reported only here.

## 🟡 Constant for only some drivers — 14 signals

For each of these, *whether the signal varies* is itself a per-driver label. This is the mechanism no pooled statistic can see.

| Flag | SPN | Signal | Constant in | Split | Distinct (min–max) |
|---|--:|---|--:|---|--:|
| 🟡 | 3232 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 19/46 | 19 vs 27 | 1–4 |
| 🟡 | 3229 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | 19/46 | 19 vs 27 | 1–3 |
| 🟡 | 3230 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | 19/46 | 19 vs 27 | 1–3 |
| 🟡 | 3231 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | 19/46 | 19 vs 27 | 1–2 |
| 🟡 | 3239 | `3239 Aftertreatment 2 Intake Dew Point` | 19/46 | 19 vs 27 | 1–2 |
| 🟡 | 236 | `236 Engine Total Idle Fuel Used` | 15/46 | 15 vs 31 | 1–3 |
| 🟡 | 975 | `975 Engine Fan 1 Estimated Percent Speed` | 9/46 | 9 vs 37 | 1–2 |
| 🟡 | 515 | `515 Engine's Desired Operating Speed` | 9/46 | 9 vs 37 | 1–794 |
| 🟡 | 1761 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 6/46 | 6 vs 40 | 1–14 |
| 🟡 | 986 | `986 Engine Fan 1 Requested Percent Speed` | 4/46 | 4 vs 42 | 1–2 |
| 🟡 | 2978 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 4/46 | 4 vs 42 | 1–14 |
| 🟡 | 2945 | `2945 Active Shift Console Indicator` | 3/46 | 3 vs 43 | 1–2 |
| 🟡 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 3/46 | 3 vs 43 | 1–2 |
| 🟡 | 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 2/46 | 2 vs 44 | 1–5 |

- **SPN 3232** constant in: G1S05, G1S15, G1S16, G1S17, G2S01, G2S02, G2S03, G2S04, G2S06, G2S10, G2S16, G3S02, G3S04, G3S05, G3S06, G3S07, G3S08, G3S09, G3S12
- **SPN 3229** constant in: G1S05, G1S15, G1S16, G1S17, G2S01, G2S02, G2S03, G2S04, G2S06, G2S10, G2S16, G3S02, G3S04, G3S05, G3S06, G3S07, G3S08, G3S09, G3S12
- **SPN 3230** constant in: G1S05, G1S15, G1S16, G1S17, G2S01, G2S02, G2S03, G2S04, G2S06, G2S10, G2S16, G3S02, G3S04, G3S05, G3S06, G3S07, G3S08, G3S09, G3S12
- **SPN 3231** constant in: G1S05, G1S15, G1S16, G1S17, G2S01, G2S02, G2S03, G2S04, G2S06, G2S10, G2S16, G3S02, G3S04, G3S05, G3S06, G3S07, G3S08, G3S09, G3S12
- **SPN 3239** constant in: G1S05, G1S15, G1S16, G1S17, G2S01, G2S02, G2S03, G2S04, G2S06, G2S10, G2S16, G3S02, G3S04, G3S05, G3S06, G3S07, G3S08, G3S09, G3S12
- **SPN 236** constant in: G1S05, G1S06, G1S16, G1S17, G2S01, G2S03, G2S05, G2S10, G2S11, G2S12, G2S13, G3S03, G3S05, G3S13, G3S16
- **SPN 975** constant in: G1S06, G1S07, G1S08, G1S09, G1S14, G2S11, G3S03, G3S09, G3S11
- **SPN 515** constant in: G1S15, G2S03, G2S06, G2S16, G3S02, G3S05, G3S06, G3S09, G3S12
- **SPN 1761** constant in: G1S02, G1S03, G1S16, G3S02, G3S03, G3S04
- **SPN 986** constant in: G1S06, G1S07, G1S08, G1S09
- **SPN 2978** constant in: G1S06, G1S07, G1S08, G1S09
- **SPN 2945** constant in: G1S08, G1S15, G2S13
- **SPN 4816** constant in: G1S08, G1S15, G2S13
- **SPN 3031** constant in: G1S16, G3S01

## 🟡 Near-constant — 4 signals hold one value ≥ 95% of a typical drive

Not zero-variance, so every separability statistic is defined on them, but the information they carry is concentrated in a small fraction of samples.

| Flag | SPN | Signal | Mean dominant share | Constant in | Distinct (min–max) |
|---|--:|---|--:|--:|--:|
| 🟡 | 515 | `515 Engine's Desired Operating Speed` | 99.22% | 9/46 | 1–794 |
| 🟡 | 51 | `51 Engine Throttle Valve 1 Position 1` | 98.35% | 0/46 | 3–73 |
| 🟡 | 2945 | `2945 Active Shift Console Indicator` | 98.31% | 3/46 | 1–2 |
| 🟡 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 98.28% | 3/46 | 1–2 |

## All signals

| Flag | SPN | Signal | Drivers | Constant in | Distinct (min–max) | Mean dominant |
|---|--:|---|--:|--:|--:|--:|
| 🔴 | 4191 | `4191 Engine Requested Torque (Fractional)` | 46 | 46 | 1–1 | 100.00% |
| 🔴 | 4207 | `4207 Message Checksum` | 46 | 46 | 1–1 | 100.00% |
| 🔴 | 4206 | `4206 Message Counter` | 46 | 46 | 1–1 | 100.00% |
| 🔴 | 5015 | `5015 Momentary Engine Maximum Power Enable` | 46 | 46 | 1–1 | 100.00% |
| 🔴 | 3544 | `3544 Time Remaining in Engine Operating State` | 46 | 46 | 1–1 | 100.00% |
| 🟡 | 3231 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | 46 | 19 | 1–2 | 90.01% |
| 🟡 | 3239 | `3239 Aftertreatment 2 Intake Dew Point` | 46 | 19 | 1–2 | 90.00% |
| 🟡 | 3230 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | 46 | 19 | 1–3 | 88.83% |
| 🟡 | 3229 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | 46 | 19 | 1–3 | 88.69% |
| 🟡 | 3232 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 46 | 19 | 1–4 | 88.52% |
| 🟡 | 236 | `236 Engine Total Idle Fuel Used` | 46 | 15 | 1–3 | 82.57% |
| 🟡 | 515 | `515 Engine's Desired Operating Speed` | 46 | 9 | 1–794 | 99.22% |
| 🟡 | 975 | `975 Engine Fan 1 Estimated Percent Speed` | 46 | 9 | 1–2 | 72.83% |
| 🟡 | 1761 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 46 | 6 | 1–14 | 64.36% |
| 🟡 | 986 | `986 Engine Fan 1 Requested Percent Speed` | 46 | 4 | 1–2 | 67.94% |
| 🟡 | 2978 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 46 | 4 | 1–14 | 55.49% |
| 🟡 | 2945 | `2945 Active Shift Console Indicator` | 46 | 3 | 1–2 | 98.31% |
| 🟡 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 46 | 3 | 1–2 | 98.28% |
| 🟡 | 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 46 | 2 | 1–5 | 51.75% |
| 🟡 | 51 | `51 Engine Throttle Valve 1 Position 1` | 46 | 0 | 3–73 | 98.35% |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 46 | 0 | 2–2 | 91.75% |
| 🟢 | 4154 | `4154 Actual Engine - Percent Torque (Fractional)` | 46 | 0 | 3–4 | 90.65% |
| 🟢 | 1029 | `1029 Trip Average Fuel Rate` | 46 | 0 | 2–3 | 76.08% |
| 🟢 | 108 | `108 Barometric Pressure` | 46 | 0 | 3–4 | 72.15% |
| 🟢 | 2979 | `2979 Vehicle Acceleration Rate Limit Status` | 46 | 0 | 2–3 | 66.58% |
| 🟢 | 898 | `898 Engine Requested Speed/Speed Limit` | 46 | 0 | 1806–3406 | 63.11% |
| 🟢 | 574 | `574 Transmission Shift In Process` | 46 | 0 | 2–2 | 59.26% |
| 🟢 | 185 | `185 Engine Average Fuel Economy` | 46 | 0 | 2–5 | 58.46% |
| 🟢 | 168 | `168 Battery Potential / Power Input 1` | 46 | 0 | 5–22 | 58.22% |
| 🟢 | 235 | `235 Engine Total Idle Hours` | 46 | 0 | 2–7 | 51.76% |
| 🟢 | 905 | `905 Relative Speed; Front Axle, Left Wheel` | 46 | 0 | 38–56 | 45.52% |
| 🟢 | 906 | `906 Relative Speed; Front Axle, Right Wheel` | 46 | 0 | 40–59 | 45.28% |
| 🟢 | 512 | `512 Driver's Demand Engine - Percent Torque` | 46 | 0 | 81–101 | 41.74% |
| 🟢 | 91 | `91 Accelerator Pedal Position 1` | 46 | 0 | 205–251 | 40.70% |
| 🟢 | 27 | `27 Engine Exhaust Gas Recirculation 1 Valve Position` | 46 | 0 | 15–29 | 34.29% |
| 🟢 | 2659 | `2659 Engine Exhaust Gas Recirculation 1 Mass Flow Rate` | 46 | 0 | 345–544 | 34.24% |
| 🟢 | 524 | `524 Transmission Selected Gear` | 46 | 0 | 5–7 | 32.90% |
| 🟢 | 526 | `526 Transmission Actual Gear Ratio` | 46 | 0 | 5–7 | 32.85% |
| 🟢 | 523 | `523 Transmission Current Gear` | 46 | 0 | 5–7 | 32.85% |
| 🟢 | 110 | `110 Engine Coolant Temperature` | 46 | 0 | 6–37 | 31.94% |
| 🟢 | 187 | `187 Power Takeoff Set Speed` | 46 | 0 | 3737–4456 | 31.46% |
| 🟢 | 3030 | `3030 Transmission Torque Converter Ratio` | 46 | 0 | 789–789 | 31.26% |
| 🟢 | 1717 | `1717 Actual Maximum Available Retarder - Percent Torque` | 46 | 0 | 13–19 | 30.85% |
| 🟢 | 5398 | `5398 Estimated Pumping - Percent Torque` | 46 | 0 | 12–27 | 30.50% |
| 🟢 | 908 | `908 Relative Speed; Rear Axle #1, Right Wheel` | 46 | 0 | 79–105 | 26.75% |
| 🟢 | 907 | `907 Relative Speed; Rear Axle #1, Left Wheel` | 46 | 0 | 73–119 | 25.83% |
| 🟢 | 514 | `514 Nominal Friction - Percent Torque` | 46 | 0 | 15–27 | 24.69% |
| 🟢 | 96 | `96 Fuel Level 1` | 46 | 0 | 4–20 | 23.76% |
| 🟢 | 3610 | `3610 Aftertreatment 1 Diesel Particulate Filter Outlet Pressure` | 46 | 0 | 46–124 | 19.24% |
| 🟢 | 904 | `904 Front Axle Speed` | 46 | 0 | 921–1209 | 18.72% |
| 🟢 | 1242 | `1242 Instantaneous Estimated Brake Power` | 46 | 0 | 114–180 | 18.49% |
| 🟢 | 184 | `184 Engine Instantaneous Fuel Economy` | 46 | 0 | 5885–8039 | 18.25% |
| 🟢 | 105 | `105 Engine Intake Manifold 1 Temperature` | 46 | 0 | 8–23 | 17.88% |
| 🟢 | 191 | `191 Transmission 1 Output Shaft Speed` | 46 | 0 | 13210–16832 | 17.10% |
| 🟢 | 102 | `102 Engine Intake Manifold #1 Pressure` | 46 | 0 | 47–83 | 16.85% |
| 🟢 | 7319 | `7319 Cruise Control Speed` | 46 | 0 | 3783–4753 | 16.80% |
| 🟢 | 84 | `84 Wheel-Based Vehicle Speed` | 46 | 0 | 3783–4753 | 16.80% |
| 🟢 | 3251 | `3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 46 | 0 | 33–82 | 15.61% |
| 🟢 | 161 | `161 Transmission 1 Input Shaft Speed` | 46 | 0 | 13206–17406 | 14.99% |
| 🟢 | 171 | `171 Ambient Air Temperature` | 46 | 0 | 28–341 | 14.34% |
| 🟢 | 513 | `513 Actual Engine - Percent Torque` | 46 | 0 | 77–94 | 13.93% |
| 🟢 | 92 | `92 Engine Percent Load At Current Speed` | 46 | 0 | 84–110 | 13.83% |
| 🟢 | 2432 | `2432 Engine Demand – Percent Torque` | 46 | 0 | 77–95 | 13.79% |
| 🟢 | 182 | `182 Engine Trip Fuel` | 46 | 0 | 10–14 | 13.68% |
| 🟢 | 250 | `250 Engine Total Fuel Used` | 46 | 0 | 10–15 | 13.39% |
| 🟢 | 183 | `183 Engine Fuel Rate` | 46 | 0 | 511–879 | 13.33% |
| 🟢 | 1088 | `1088 Service Brake Circuit 2 Air Pressure` | 46 | 0 | 22–32 | 10.89% |
| 🟢 | 1087 | `1087 Service Brake Circuit 1 Air Pressure` | 46 | 0 | 22–32 | 10.87% |
| 🟢 | 100 | `100 Engine Oil Pressure 1` | 46 | 0 | 61–72 | 10.61% |
| 🟢 | 518 | `518 Engine Requested Torque/Torque Limit` | 46 | 0 | 85–122 | 10.25% |
| 🟢 | 641 | `641 Engine Variable Geometry Turbocharger Actuator #1` | 46 | 0 | 75–237 | 8.48% |
| 🟢 | 117 | `117 Brake Primary Pressure` | 46 | 0 | 44–64 | 7.47% |
| 🟢 | 118 | `118 Brake Secondary Pressure` | 46 | 0 | 43–62 | 7.34% |
| 🟢 | 247 | `247 Engine Total Hours of Operation` | 46 | 0 | 13–20 | 6.51% |
| 🟢 | 3226 | `3226 Aftertreatment 1 Outlet NOx 1` | 46 | 0 | 626–4970 | 5.05% |
| 🟢 | 244 | `244 Trip Distance` | 46 | 0 | 184–205 | 5.05% |
| 🟢 | 245 | `245 Total Vehicle Distance` | 46 | 0 | 184–205 | 5.04% |
| 🟢 | 5313 | `5313 Commanded Engine Fuel Rail Pressure` | 46 | 0 | 6973–7980 | 3.98% |
| 🟢 | 918 | `918 Trip Distance (High Resolution)` | 46 | 0 | 1795–2237 | 3.95% |
| 🟢 | 3357 | `3357 Actual Maximum Available Engine - Percent Torque` | 46 | 0 | 143–186 | 3.83% |
| 🟢 | 1209 | `1209 Engine Exhaust Bank 1 Pressure 1` | 46 | 0 | 4002–6048 | 2.93% |
| 🟢 | 249 | `249 Engine Total Revolutions` | 46 | 0 | 49–66 | 2.74% |
| 🟢 | 3721 | `3721 Aftertreatment 1 Diesel Particulate Filter Time Since Last Active Regeneration` | 46 | 0 | 1614–3347 | 2.30% |
| 🟢 | 1136 | `1136 Engine ECU Temperature` | 46 | 0 | 145–856 | 2.00% |
| 🟢 | 1172 | `1172 Engine Turbocharger 1 Compressor Intake Temperature` | 46 | 0 | 125–398 | 1.99% |
| 🟢 | 101 | `101 Engine Crankcase Pressure 1` | 46 | 0 | 196–305 | 1.60% |
| 🟢 | 177 | `177 Transmission Oil Temperature 1` | 46 | 0 | 130–968 | 1.49% |
| 🟢 | 5466 | `5466 Aftertreatment 1 Diesel Particulate Filter Soot Load Regeneration Threshold` | 46 | 0 | 450–1559 | 1.37% |
| 🟢 | 3216 | `3216 Engine Exhaust 1 NOx 1` | 46 | 0 | 5969–9881 | 1.04% |
| 🟢 | 4363 | `4363 Aftertreatment 1 SCR Outlet Temperature` | 46 | 0 | 636–1992 | 0.93% |
| 🟢 | 4360 | `4360 Aftertreatment 1 SCR Intake Temperature` | 46 | 0 | 682–1994 | 0.85% |
| 🟢 | 5862 | `5862 Aftertreatment 1 SCR Intermediate Temperature` | 46 | 0 | 683–1994 | 0.85% |
| 🟢 | 412 | `412 Engine Exhaust Gas Recirculation 1 Temperature` | 46 | 0 | 441–984 | 0.84% |
| 🟢 | 132 | `132 Engine Intake Air Mass Flow Rate` | 46 | 0 | 1018–1827 | 0.76% |
| 🟢 | 3246 | `3246 Aftertreatment 1 Diesel Particulate Filter Outlet Temperature` | 46 | 0 | 943–2116 | 0.59% |
| 🟢 | 3241 | `3241 Aftertreatment 1 Exhaust Temperature 1` | 46 | 0 | 1138–1892 | 0.50% |
| 🟢 | 4765 | `4765 Aftertreatment 1 Diesel Oxidation Catalyst Intake Temperature` | 46 | 0 | 1177–1881 | 0.49% |
| 🟢 | 3242 | `3242 Aftertreatment 1 Diesel Particulate Filter Intake Temperature` | 46 | 0 | 996–2143 | 0.49% |
| 🟢 | 103 | `103 Engine Turbocharger 1 Speed` | 46 | 0 | 1867–2508 | 0.41% |
| 🟢 | 5052 | `5052 Transmission Clutch/Converter Input Speed` | 46 | 0 | 8511–10894 | 0.24% |
| 🟢 | 190 | `190 Engine Speed` | 46 | 0 | 9021–12292 | 0.20% |
| 🟢 | 157 | `157 Engine Fuel 1 Injector Metering Rail 1 Pressure` | 46 | 0 | 3401–4335 | 0.19% |

## Value tables — flagged signals

Only signals with at most 64 distinct values appear here; above that a value table carries no information.

### SPN 975 — `975 Engine Fan 1 Estimated Percent Speed`

2 distinct values · 129,318 samples

| Value | Samples | Share |
|--:|--:|--:|
| `0.0` | 64,904 | 50.1895% |
| `100.0` | 64,414 | 49.8105% |

### SPN 986 — `986 Engine Fan 1 Requested Percent Speed`

2 distinct values · 258,450 samples

| Value | Samples | Share |
|--:|--:|--:|
| `0.0` | 174,707 | 67.5980% |
| `100.0` | 83,743 | 32.4020% |

### SPN 2945 — `2945 Active Shift Console Indicator`

2 distinct values · 1,293,219 samples

| Value | Samples | Share |
|--:|--:|--:|
| `0.0` | 1,271,100 | 98.2896% |
| `1.0` | 22,119 | 1.7104% |

### SPN 2978 — `2978 Estimated Engine Parasitic Losses - Percent Torque`

14 distinct values · 6,465,503 samples

| Value | Samples | Share |
|--:|--:|--:|
| `0.0` | 3,241,937 | 50.1421% |
| `2.0` | 1,216,678 | 18.8180% |
| `4.0` | 707,149 | 10.9373% |
| `3.0` | 515,655 | 7.9755% |
| `5.0` | 491,272 | 7.5984% |
| `6.0` | 161,044 | 2.4908% |
| `7.0` | 66,045 | 1.0215% |
| `8.0` | 36,010 | 0.5570% |
| `9.0` | 17,376 | 0.2687% |
| `10.0` | 6,393 | 0.0989% |
| _4 further values_ | 5,944 | 0.0919% |

### SPN 3031 — `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1`

28 distinct values · 129,321 samples

| Value | Samples | Share |
|--:|--:|--:|
| `28.0` | 14,027 | 10.8467% |
| `29.0` | 9,851 | 7.6175% |
| `26.0` | 9,293 | 7.1860% |
| `25.0` | 8,825 | 6.8241% |
| `24.0` | 8,253 | 6.3818% |
| `20.0` | 8,131 | 6.2875% |
| `23.0` | 7,915 | 6.1204% |
| `22.0` | 6,671 | 5.1585% |
| `21.0` | 6,205 | 4.7981% |
| `27.0` | 5,984 | 4.6272% |
| _18 further values_ | 44,166 | 34.1522% |

### SPN 3229 — `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature`

3 distinct values · 2,586,413 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1.0` | 2,298,514 | 88.8688% |
| `11.0` | 254,360 | 9.8345% |
| `0.0` | 33,539 | 1.2967% |

### SPN 3230 — `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable`

3 distinct values · 2,586,413 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1.0` | 2,302,047 | 89.0054% |
| `11.0` | 254,360 | 9.8345% |
| `0.0` | 30,006 | 1.1601% |

### SPN 3231 — `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable`

2 distinct values · 2,586,413 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1.0` | 2,332,053 | 90.1655% |
| `11.0` | 254,360 | 9.8345% |

### SPN 3232 — `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI`

4 distinct values · 2,586,413 samples

| Value | Samples | Share |
|--:|--:|--:|
| `10011.0` | 2,294,054 | 88.6964% |
| `11111.0` | 254,360 | 9.8345% |
| `10111.0` | 25,051 | 0.9686% |
| `11011.0` | 12,948 | 0.5006% |

### SPN 3239 — `3239 Aftertreatment 2 Intake Dew Point`

2 distinct values · 6,465,503 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1.0` | 5,829,285 | 90.1598% |
| `0.0` | 636,218 | 9.8402% |

### SPN 3544 — `3544 Time Remaining in Engine Operating State`

1 distinct values · 86,902 samples

| Value | Samples | Share |
|--:|--:|--:|
| `64255.0` | 86,902 | 100.0000% |

### SPN 4191 — `4191 Engine Requested Torque (Fractional)`

1 distinct values · 1,077,166 samples

| Value | Samples | Share |
|--:|--:|--:|
| `138.0` | 1,077,166 | 100.0000% |

### SPN 4206 — `4206 Message Counter`

1 distinct values · 1,077,166 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1111.0` | 1,077,166 | 100.0000% |

### SPN 4207 — `4207 Message Checksum`

1 distinct values · 1,077,166 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1111.0` | 1,077,166 | 100.0000% |

### SPN 4816 — `4816 Transmission Torque Converter Lockup Transition in Process`

2 distinct values · 12,931,907 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1` | 12,706,918 | 98.2602% |
| `0` | 224,989 | 1.7398% |

### SPN 5015 — `5015 Momentary Engine Maximum Power Enable`

1 distinct values · 12,931,907 samples

| Value | Samples | Share |
|--:|--:|--:|
| `1` | 12,931,907 | 100.0000% |

