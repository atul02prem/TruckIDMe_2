# Continuous-signal separability — level, spread, and mutual information

All **81 continuous** signals, measured over **46 drivers** on the raw CAN data. Raw data deliberately: measuring on `processed_data` would make every currently-excluded signal permanently unreviewable.

| Statistic | Question it answers |
|---|---|
| η² raw | does each driver occupy a distinct value band, sample by sample? |
| η² window | the same question about the 120s window mean — the *level* a model reads |
| η² window-std | does each driver show a distinct **spread** within the 120s window? The only column that can see a driver who shares everyone else's average but differs in jitter |
| MI share | fraction of driver-identity entropy the signal resolves; catches non-linear and multimodal separation |

Flags on the **largest** of the four: 🔴 ≥ 0.9 · 🟡 0.5–0.9 · 🟢 < 0.5.

**This report measures only.** It carries no exclusion labels and makes no recommendation. The statistic flags; physics decides; that decision belongs in a separate artifact which cites this one.

## ⚑ Why a spread column exists

η² is defined on group **means**: its numerator is built from each driver's mean. Two drivers with the same average and different jitter therefore give a near-zero numerator *and* an inflated denominator, so **η² falls rather than rises** — at either scale. Mutual information here is computed on window means, so it is blind in the same way. Without this column every statistic in the report is a detector of *level*, and a signal whose driver information lives entirely in within-window variability would score 🟢 on all of them.

Which direction that blindness mattered in is worth being precise about: a high score makes a signal an exclusion *candidate*, and nothing is ever excluded for scoring low. So the missing column could only ever have produced a **false clear** — a leak kept — never a false exclusion.

## ⚑ Why two scales

A signal that *ramps* carries large **within**-driver variance from the ramp itself, which pushes raw η² down, while its per-window **mean** can still separate drivers because each drove on a different day. The window column is the instrument that sees that.

**A correction to the record.** `all_can_eta2.md` states that the thermal family scored 0.08–0.38 on raw η² and still cost 45 points when removed, implying raw η² was blind to it. Measured here over the same 46 drivers, that family spans **0.078 to 0.986**: DEF tank temperature 0.986, ambient air temperature 0.968, turbocharger intake temperature 0.941. The leakiest members were flagged loudly by raw η². The 0.08–0.38 figure describes only the downstream exhaust temperatures. So the 74% → 29% collapse was **not** a failure of the statistic — it was a failure to act on what the statistic already said.

## ⚑ Where the two scales disagree — 11 signals

Window η² exceeds raw η² by at least 0.15. These are the signals whose *level over a window* identifies the drive more than any individual sample does — a drifting or ramping quantity. This is what the second scale buys, and it is the only column that sees it.

| Flag | SPN | Signal | η² raw | η² window | gap | η² win-std | MI share |
|---|--:|---|--:|--:|--:|--:|--:|
| 🟡 | 168 | `168 Battery Potential / Power Input 1` | 0.239 | **0.814** | +0.574 | 0.192 | 0.294 |
| 🟡 | 2978 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 0.244 | **0.665** | +0.421 | 0.427 | 0.165 |
| 🟢 | 515 | `515 Engine's Desired Operating Speed` | 0.023 | **0.366** | +0.343 | 0.442 | 0.051 |
| 🟢 | 4154 | `4154 Actual Engine - Percent Torque (Fractional)` | 0.018 | **0.310** | +0.292 | 0.322 | 0.063 |
| 🟢 | 3216 | `3216 Engine Exhaust 1 NOx 1` | 0.050 | **0.335** | +0.286 | 0.203 | 0.067 |
| 🟢 | 3357 | `3357 Actual Maximum Available Engine - Percent Torque` | 0.064 | **0.327** | +0.263 | 0.162 | 0.056 |
| 🟢 | 3251 | `3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 0.127 | **0.327** | +0.201 | 0.235 | 0.067 |
| 🟢 | 3226 | `3226 Aftertreatment 1 Outlet NOx 1` | 0.098 | **0.288** | +0.190 | 0.125 | 0.029 |
| 🟢 | 907 | `907 Relative Speed; Rear Axle #1, Left Wheel` | 0.018 | **0.195** | +0.178 | 0.043 | 0.045 |
| 🟢 | 641 | `641 Engine Variable Geometry Turbocharger Actuator #1` | 0.053 | **0.227** | +0.173 | 0.159 | 0.059 |
| 🟢 | 908 | `908 Relative Speed; Rear Axle #1, Right Wheel` | 0.010 | **0.163** | +0.153 | 0.044 | 0.023 |

## 🟢 Nothing is seen only in the spread (none ≥ 0.5 while both level columns are below it)

The spread column changed no verdict. Recorded as a negative result: the blind spot was real, and measuring it found nothing hiding there.

## Strongly separating — 18 signals at ≥ 0.9

| Flag | SPN | Signal | η² raw | η² window | η² win-std | MI share |
|---|--:|---|--:|--:|--:|--:|
| 🔴 | 249 | `249 Engine Total Revolutions` | 1.000 | 1.000 | 0.083 | 1.000 |
| 🔴 | 182 | `182 Engine Trip Fuel` | 1.000 | 1.000 | 0.014 | 1.000 |
| 🔴 | 247 | `247 Engine Total Hours of Operation` | 1.000 | 1.000 | 0.073 | 1.000 |
| 🔴 | 250 | `250 Engine Total Fuel Used` | 1.000 | 1.000 | 0.017 | 1.000 |
| 🔴 | 1029 | `1029 Trip Average Fuel Rate` | 0.999 | 1.000 | 0.708 | 1.000 |
| 🔴 | 235 | `235 Engine Total Idle Hours` | 1.000 | nan | nan | nan |
| 🔴 | 918 | `918 Trip Distance (High Resolution)` | 1.000 | 1.000 | 0.034 | 0.996 |
| 🔴 | 244 | `244 Trip Distance` | 1.000 | 1.000 | 0.034 | 0.996 |
| 🔴 | 245 | `245 Total Vehicle Distance` | 1.000 | 1.000 | 0.034 | 0.996 |
| 🔴 | 236 | `236 Engine Total Idle Fuel Used` | 1.000 | nan | nan | nan |
| 🔴 | 185 | `185 Engine Average Fuel Economy` | 0.999 | 1.000 | 0.138 | 0.923 |
| 🔴 | 1761 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 0.998 | 0.998 | 0.171 | 0.823 |
| 🔴 | 96 | `96 Fuel Level 1` | 0.998 | 0.998 | 0.121 | 0.823 |
| 🔴 | 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 0.986 | 0.986 | 0.025 | 0.559 |
| 🔴 | 171 | `171 Ambient Air Temperature` | 0.968 | 0.969 | 0.082 | 0.518 |
| 🔴 | 5466 | `5466 Aftertreatment 1 Diesel Particulate Filter Soot Load Regeneration Threshold` | 0.948 | 0.950 | 0.057 | 0.700 |
| 🔴 | 1172 | `1172 Engine Turbocharger 1 Compressor Intake Temperature` | 0.941 | 0.944 | 0.089 | 0.381 |
| 🔴 | 3721 | `3721 Aftertreatment 1 Diesel Particulate Filter Time Since Last Active Regeneration` | 0.937 | 0.939 | 0.044 | 0.762 |

## All continuous signals

| Flag | SPN | Signal | η² raw | η² window | η² win-std | MI share | Windows |
|---|--:|---|--:|--:|--:|--:|--:|
| 🔴 | 249 | `249 Engine Total Revolutions` | 1.000 | 1.000 | 0.083 | 1.000 | 962 |
| 🔴 | 182 | `182 Engine Trip Fuel` | 1.000 | 1.000 | 0.014 | 1.000 | 1081 |
| 🔴 | 247 | `247 Engine Total Hours of Operation` | 1.000 | 1.000 | 0.073 | 1.000 | 962 |
| 🔴 | 250 | `250 Engine Total Fuel Used` | 1.000 | 1.000 | 0.017 | 1.000 | 1081 |
| 🔴 | 1029 | `1029 Trip Average Fuel Rate` | 0.999 | 1.000 | 0.708 | 1.000 | 887 |
| 🔴 | 235 | `235 Engine Total Idle Hours` | 1.000 | nan | nan | nan | 0 |
| 🔴 | 918 | `918 Trip Distance (High Resolution)` | 1.000 | 1.000 | 0.034 | 0.996 | 1098 |
| 🔴 | 244 | `244 Trip Distance` | 1.000 | 1.000 | 0.034 | 0.996 | 1102 |
| 🔴 | 245 | `245 Total Vehicle Distance` | 1.000 | 1.000 | 0.034 | 0.996 | 1102 |
| 🔴 | 236 | `236 Engine Total Idle Fuel Used` | 1.000 | nan | nan | nan | 0 |
| 🔴 | 185 | `185 Engine Average Fuel Economy` | 0.999 | 1.000 | 0.138 | 0.923 | 1102 |
| 🔴 | 1761 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 0.998 | 0.998 | 0.171 | 0.823 | 1098 |
| 🔴 | 96 | `96 Fuel Level 1` | 0.998 | 0.998 | 0.121 | 0.823 | 1098 |
| 🔴 | 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 0.986 | 0.986 | 0.025 | 0.559 | 1098 |
| 🔴 | 171 | `171 Ambient Air Temperature` | 0.968 | 0.969 | 0.082 | 0.518 | 1098 |
| 🔴 | 5466 | `5466 Aftertreatment 1 Diesel Particulate Filter Soot Load Regeneration Threshold` | 0.948 | 0.950 | 0.057 | 0.700 | 1098 |
| 🔴 | 1172 | `1172 Engine Turbocharger 1 Compressor Intake Temperature` | 0.941 | 0.944 | 0.089 | 0.381 | 1098 |
| 🔴 | 3721 | `3721 Aftertreatment 1 Diesel Particulate Filter Time Since Last Active Regeneration` | 0.937 | 0.939 | 0.044 | 0.762 | 1098 |
| 🟡 | 168 | `168 Battery Potential / Power Input 1` | 0.239 | 0.814 | 0.192 | 0.294 | 1100 |
| 🟡 | 108 | `108 Barometric Pressure` | 0.743 | 0.807 | 0.144 | 0.215 | 1098 |
| 🟡 | 105 | `105 Engine Intake Manifold 1 Temperature` | 0.731 | 0.755 | 0.121 | 0.193 | 1100 |
| 🟡 | 2978 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 0.244 | 0.665 | 0.427 | 0.165 | 1102 |
| 🟡 | 1136 | `1136 Engine ECU Temperature` | 0.569 | 0.568 | 0.122 | 0.207 | 1098 |
| 🟢 | 515 | `515 Engine's Desired Operating Speed` | 0.023 | 0.366 | 0.442 | 0.051 | 1102 |
| 🟢 | 177 | `177 Transmission Oil Temperature 1` | 0.378 | 0.372 | 0.171 | 0.149 | 1098 |
| 🟢 | 3216 | `3216 Engine Exhaust 1 NOx 1` | 0.050 | 0.335 | 0.203 | 0.067 | 1086 |
| 🟢 | 3251 | `3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 0.127 | 0.327 | 0.235 | 0.067 | 1100 |
| 🟢 | 3357 | `3357 Actual Maximum Available Engine - Percent Torque` | 0.064 | 0.327 | 0.162 | 0.056 | 1102 |
| 🟢 | 4154 | `4154 Actual Engine - Percent Torque (Fractional)` | 0.018 | 0.310 | 0.322 | 0.063 | 1102 |
| 🟢 | 3226 | `3226 Aftertreatment 1 Outlet NOx 1` | 0.098 | 0.288 | 0.125 | 0.029 | 996 |
| 🟢 | 641 | `641 Engine Variable Geometry Turbocharger Actuator #1` | 0.053 | 0.227 | 0.159 | 0.059 | 1102 |
| 🟢 | 3610 | `3610 Aftertreatment 1 Diesel Particulate Filter Outlet Pressure` | 0.025 | 0.101 | 0.208 | 0.017 | 1100 |
| 🟢 | 512 | `512 Driver's Demand Engine - Percent Torque` | 0.010 | 0.070 | 0.202 | 0.005 | 1102 |
| 🟢 | 412 | `412 Engine Exhaust Gas Recirculation 1 Temperature` | 0.136 | 0.196 | 0.098 | 0.064 | 1098 |
| 🟢 | 907 | `907 Relative Speed; Rear Axle #1, Left Wheel` | 0.018 | 0.195 | 0.043 | 0.045 | 1101 |
| 🟢 | 3242 | `3242 Aftertreatment 1 Diesel Particulate Filter Intake Temperature` | 0.164 | 0.183 | 0.047 | 0.040 | 1100 |
| 🟢 | 183 | `183 Engine Fuel Rate` | 0.010 | 0.089 | 0.177 | 0.007 | 1102 |
| 🟢 | 27 | `27 Engine Exhaust Gas Recirculation 1 Valve Position` | 0.020 | 0.126 | 0.171 | 0.040 | 1102 |
| 🟢 | 102 | `102 Engine Intake Manifold #1 Pressure` | 0.016 | 0.080 | 0.171 | 0.012 | 1100 |
| 🟢 | 1242 | `1242 Instantaneous Estimated Brake Power` | 0.008 | 0.080 | 0.171 | 0.007 | 1102 |
| 🟢 | 3246 | `3246 Aftertreatment 1 Diesel Particulate Filter Outlet Temperature` | 0.166 | 0.170 | 0.033 | 0.036 | 1100 |
| 🟢 | 91 | `91 Accelerator Pedal Position 1` | 0.009 | 0.061 | 0.167 | 0.003 | 1102 |
| 🟢 | 5398 | `5398 Estimated Pumping - Percent Torque` | 0.042 | 0.148 | 0.166 | 0.035 | 1102 |
| 🟢 | 908 | `908 Relative Speed; Rear Axle #1, Right Wheel` | 0.010 | 0.163 | 0.044 | 0.023 | 1101 |
| 🟢 | 2659 | `2659 Engine Exhaust Gas Recirculation 1 Mass Flow Rate` | 0.016 | 0.134 | 0.158 | 0.025 | 1102 |
| 🟢 | 101 | `101 Engine Crankcase Pressure 1` | 0.014 | 0.075 | 0.155 | 0.011 | 1100 |
| 🟢 | 132 | `132 Engine Intake Air Mass Flow Rate` | 0.019 | 0.082 | 0.147 | 0.009 | 1102 |
| 🟢 | 2432 | `2432 Engine Demand – Percent Torque` | 0.005 | 0.061 | 0.146 | 0.005 | 1102 |
| 🟢 | 513 | `513 Actual Engine - Percent Torque` | 0.005 | 0.060 | 0.146 | 0.004 | 1102 |
| 🟢 | 5862 | `5862 Aftertreatment 1 SCR Intermediate Temperature` | 0.142 | 0.144 | 0.077 | 0.032 | 1100 |
| 🟢 | 4360 | `4360 Aftertreatment 1 SCR Intake Temperature` | 0.142 | 0.144 | 0.077 | 0.032 | 1100 |
| 🟢 | 92 | `92 Engine Percent Load At Current Speed` | 0.004 | 0.060 | 0.138 | 0.006 | 1102 |
| 🟢 | 1209 | `1209 Engine Exhaust Bank 1 Pressure 1` | 0.035 | 0.133 | 0.129 | 0.033 | 1102 |
| 🟢 | 514 | `514 Nominal Friction - Percent Torque` | 0.036 | 0.132 | 0.120 | 0.031 | 1102 |
| 🟢 | 4363 | `4363 Aftertreatment 1 SCR Outlet Temperature` | 0.127 | 0.128 | 0.091 | 0.027 | 1100 |
| 🟢 | 3241 | `3241 Aftertreatment 1 Exhaust Temperature 1` | 0.088 | 0.122 | 0.040 | 0.045 | 1100 |
| 🟢 | 4765 | `4765 Aftertreatment 1 Diesel Oxidation Catalyst Intake Temperature` | 0.088 | 0.122 | 0.040 | 0.045 | 1100 |
| 🟢 | 110 | `110 Engine Coolant Temperature` | 0.078 | 0.102 | 0.110 | 0.082 | 1098 |
| 🟢 | 1717 | `1717 Actual Maximum Available Retarder - Percent Torque` | 0.013 | 0.066 | 0.109 | 0.013 | 1102 |
| 🟢 | 5052 | `5052 Transmission Clutch/Converter Input Speed` | 0.016 | 0.064 | 0.097 | 0.007 | 1102 |
| 🟢 | 184 | `184 Engine Instantaneous Fuel Economy` | 0.006 | 0.068 | 0.096 | 0.000 | 1102 |
| 🟢 | 103 | `103 Engine Turbocharger 1 Speed` | 0.019 | 0.070 | 0.085 | 0.014 | 1098 |
| 🟢 | 5313 | `5313 Commanded Engine Fuel Rail Pressure` | 0.011 | 0.058 | 0.080 | 0.010 | 1101 |
| 🟢 | 157 | `157 Engine Fuel 1 Injector Metering Rail 1 Pressure` | 0.012 | 0.059 | 0.080 | 0.006 | 1100 |
| 🟢 | 190 | `190 Engine Speed` | 0.014 | 0.062 | 0.073 | 0.018 | 1102 |
| 🟢 | 51 | `51 Engine Throttle Valve 1 Position 1` | 0.001 | 0.040 | 0.050 | 0.067 | 1102 |
| 🟢 | 100 | `100 Engine Oil Pressure 1` | 0.017 | 0.066 | 0.053 | 0.019 | 1100 |
| 🟢 | 117 | `117 Brake Primary Pressure` | 0.009 | 0.021 | 0.063 | 0.000 | 1098 |
| 🟢 | 118 | `118 Brake Secondary Pressure` | 0.009 | 0.022 | 0.063 | 0.000 | 1098 |
| 🟢 | 1087 | `1087 Service Brake Circuit 1 Air Pressure` | 0.009 | 0.022 | 0.062 | 0.000 | 1098 |
| 🟢 | 1088 | `1088 Service Brake Circuit 2 Air Pressure` | 0.010 | 0.022 | 0.062 | 0.000 | 1098 |
| 🟢 | 161 | `161 Transmission 1 Input Shaft Speed` | 0.018 | 0.062 | 0.036 | 0.001 | 1102 |
| 🟢 | 187 | `187 Power Takeoff Set Speed` | 0.015 | 0.055 | 0.037 | 0.017 | 1102 |
| 🟢 | 3030 | `3030 Transmission Torque Converter Ratio` | 0.023 | 0.055 | 0.034 | 0.000 | 1102 |
| 🟢 | 526 | `526 Transmission Actual Gear Ratio` | 0.017 | 0.052 | 0.037 | 0.009 | 1102 |
| 🟢 | 7319 | `7319 Cruise Control Speed` | 0.018 | 0.044 | 0.042 | 0.008 | 1102 |
| 🟢 | 84 | `84 Wheel-Based Vehicle Speed` | 0.018 | 0.044 | 0.042 | 0.008 | 1102 |
| 🟢 | 191 | `191 Transmission 1 Output Shaft Speed` | 0.018 | 0.044 | 0.042 | 0.008 | 1102 |
| 🟢 | 904 | `904 Front Axle Speed` | 0.018 | 0.044 | 0.041 | 0.006 | 1101 |
| 🟢 | 905 | `905 Relative Speed; Front Axle, Left Wheel` | 0.000 | 0.008 | 0.031 | 0.000 | 1101 |
| 🟢 | 906 | `906 Relative Speed; Front Axle, Right Wheel` | 0.000 | 0.008 | 0.031 | 0.000 | 1101 |

## How to read a disagreement between the columns

- **raw high, window high** — separates drivers at every scale. A fingerprint unless physics says the quantity is genuinely behavioural.
- **raw low, window high** — a ramp or a drifting level. The signal moves a lot *within* a drive, which hides it from raw η², while its level still identifies the drive. The thermal family's signature.
- **raw high, window low** — rare; a signal whose per-sample spread is driver-specific but whose average is not.
- **level columns low, spread column high** — drivers share an average but differ in how much the signal moves within a window. This is jitter, smoothness or aggression, and the spread column is the only one that can see it.
- **η² low, MI high** — drivers share a mean but differ in distribution shape in some other way. MI is the only column that would see that.

**What MI actually contributed here: nothing.** No signal has MI ≥ 0.5 while both η² columns sit below 0.5. MI is systematically *lower* than η² on this data (SPN 3031: η² = 0.986, MI = 0.559), so it behaves as a weaker detector rather than a complementary one. It is kept in the table as a negative result worth recording, not as a criterion that earned its place.

## Caveat

Mutual information is estimated by a k-nearest-neighbour method that adds small noise to break ties; the seed is pinned (`MI_SEED = 0`) so the number is reproducible. It is computed on window means rather than raw samples, both because that is the scale the model reads and because a k-NN estimate over millions of autocorrelated samples would measure sampling density as much as dependence.
