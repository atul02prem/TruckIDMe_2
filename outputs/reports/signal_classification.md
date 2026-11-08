# Signal classification — the three standard automotive signal types

All **102 CAN signals** in the raw data, value sets pooled over 46 drivers. This report describes only what each signal *is*. Whether a signal is kept, and whether our aggregation of it is correct, are separate questions answered elsewhere.

| Type | Count | Correct handling | Convention |
|---|---:|---|---|
| continuous | 81 | linear interpolation; mean / std / percentiles | asammdf `float_interpolation=1`, MATLAB `continuous` |
| step | 15 | repeat previous value (ZOH), or mode per window | asammdf `integer_interpolation=0`, MATLAB `step` |
| event | 6 | **do not fill** — absence is the normal state | MATLAB `event`, asammdf `empty_channels='skip'` |

The taxonomy follows MATLAB Vehicle Network Toolbox's `VariableContinuity` property and asammdf's interpolation defaults, as recorded in `literature_multirate_can.md`. We add no categories of our own.

## Data-quality note

**5 signals are constant** — one single value across every sample of every one of the 46 drivers. Not a signal type but a defect: with zero variance they carry no information, no separability statistic is defined on them (η² and mutual information are both 0/0), and they cannot contribute to any model.

| Flag | SPN | Signal | Value held | Samples | Coverage |
|---|--:|---|--:|--:|--:|
| 🔴 | 4191 | `4191 Engine Requested Torque (Fractional)` | `138` | 1,077,166 | 8.6% |
| 🔴 | 4207 | `4207 Message Checksum` | `1111` | 1,077,166 | 8.6% |
| 🔴 | 4206 | `4206 Message Counter` | `1111` | 1,077,166 | 8.6% |
| 🔴 | 3544 | `3544 Time Remaining in Engine Operating State` | `64255` | 86,902 | 16.4% |
| 🔴 | 5015 | `5015 Momentary Engine Maximum Power Enable` | `1` | 12,931,907 | 99.6% |

The coverage column separates two cases. **4 are constant *and* sporadic** (SPN 4191, SPN 4207, SPN 4206, SPN 3544): transmitting on under half the drive and sending the same value each time. **1 is constant while transmitting steadily** (SPN 5015): present on essentially the whole drive, always the same value.

### ⚑ Open item — three of these values are not physically valid

The measurement above (zero variance) is certain. The *reason* is not, and the values themselves raise a separate question that is not about leakage at all:

| Flag | SPN | Value | Why it is suspect |
|---|--:|--:|---|
| 🟡 | 3544 | `64255` | `0xFAFF` is the largest value a 2-byte J1939 parameter may legally carry — i.e. a saturation / top-of-range sentinel, not a reading |
| 🔴 | 4206 | `1111` | published as a 4-bit message counter, which cannot exceed 15 |
| 🔴 | 4207 | `1111` | published as a 4-bit checksum, which cannot exceed 15 — and is *identical* to the counter above, which a real counter/checksum pair cannot be |
| 🔴 | 4191 | `138` | published as a 3-bit fractional torque field, which cannot reach 138 |

These values fall outside the ranges the SPN definitions allow, so the likeliest explanation is a **decoding artifact in the CSV export, not a bus condition**. This cannot be confirmed from anything in this repository: no DBC or decoder specification is checked in, and the widths above are quoted from the J1939-71 definitions rather than verified against whatever DBC produced these files. **Action: obtain the DBC and re-check.** If the decode is wrong for these columns it may be wrong for others, which is a question about the whole dataset rather than about these five signals.

### Why this matters now

`SPN 5015` is currently one of the audited channels fed to the models, so a zero-information column is occupying an input slot. Dropping a constant column is a data-quality fix rather than a leakage judgement: with no variance there is no behaviour in it to lose, whatever the underlying cause turns out to be.

## All signals

| SPN | Signal | Type | Coverage | Distinct | Integer | Accumulator |
|--:|---|---|--:|--:|:-:|:-:|
| 4154 | `4154 Actual Engine - Percent Torque (Fractional)` | continuous | 99.9% | 4 | yes | — |
| 108 | `108 Barometric Pressure` | continuous | 99.9% | 7 | no | — |
| 526 | `526 Transmission Actual Gear Ratio` | continuous | 100.0% | 7 | no | — |
| 2978 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | continuous | 99.9% | 14 | yes | — |
| 1717 | `1717 Actual Maximum Available Retarder - Percent Torque` | continuous | 100.0% | 19 | yes | — |
| 168 | `168 Battery Potential / Power Input 1` | continuous | 98.2% | 23 | no | — |
| 5398 | `5398 Estimated Pumping - Percent Torque` | continuous | 100.0% | 27 | yes | — |
| 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | continuous | 100.0% | 28 | yes | — |
| 514 | `514 Nominal Friction - Percent Torque` | continuous | 99.9% | 29 | yes | — |
| 1087 | `1087 Service Brake Circuit 1 Air Pressure` | continuous | 99.5% | 32 | yes | — |
| 1088 | `1088 Service Brake Circuit 2 Air Pressure` | continuous | 99.5% | 32 | yes | — |
| 1029 | `1029 Trip Average Fuel Rate` | continuous | 98.1% | 33 | no | — |
| 27 | `27 Engine Exhaust Gas Recirculation 1 Valve Position` | continuous | 99.9% | 39 | no | — |
| 105 | `105 Engine Intake Manifold 1 Temperature` | continuous | 100.0% | 39 | yes | — |
| 110 | `110 Engine Coolant Temperature` | continuous | 100.0% | 42 | yes | — |
| 905 | `905 Relative Speed; Front Axle, Left Wheel` | continuous | 99.9% | 62 | no | — |
| 117 | `117 Brake Primary Pressure` | continuous | 99.7% | 64 | yes | — |
| 118 | `118 Brake Secondary Pressure` | continuous | 99.7% | 64 | yes | — |
| 906 | `906 Relative Speed; Front Axle, Right Wheel` | continuous | 99.9% | 67 | no | — |
| 185 | `185 Engine Average Fuel Economy` | continuous | 100.0% | 74 | no | — |
| 100 | `100 Engine Oil Pressure 1` | continuous | 100.0% | 78 | yes | — |
| 236 | `236 Engine Total Idle Fuel Used` | continuous | 99.7% | 81 | no | yes |
| 102 | `102 Engine Intake Manifold #1 Pressure` | continuous | 100.0% | 84 | yes | — |
| 513 | `513 Actual Engine - Percent Torque` | continuous | 99.9% | 94 | yes | — |
| 3251 | `3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | continuous | 100.0% | 94 | no | — |
| 2432 | `2432 Engine Demand – Percent Torque` | continuous | 99.9% | 95 | yes | — |
| 1761 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | continuous | 100.0% | 100 | no | — |
| 512 | `512 Driver's Demand Engine - Percent Torque` | continuous | 99.9% | 101 | yes | — |
| 92 | `92 Engine Percent Load At Current Speed` | continuous | 100.0% | 112 | yes | — |
| 51 | `51 Engine Throttle Valve 1 Position 1` | continuous | 100.0% | 130 | no | — |
| 908 | `908 Relative Speed; Rear Axle #1, Right Wheel` | continuous | 99.9% | 147 | no | — |
| 3610 | `3610 Aftertreatment 1 Diesel Particulate Filter Outlet Pressure` | continuous | 100.0% | 150 | no | — |
| 907 | `907 Relative Speed; Rear Axle #1, Left Wheel` | continuous | 99.9% | 175 | no | — |
| 235 | `235 Engine Total Idle Hours` | continuous | 99.7% | 178 | no | yes |
| 1242 | `1242 Instantaneous Estimated Brake Power` | continuous | 100.0% | 180 | yes | — |
| 3357 | `3357 Actual Maximum Available Engine - Percent Torque` | continuous | 100.0% | 213 | no | — |
| 96 | `96 Fuel Level 1` | continuous | 99.5% | 215 | no | — |
| 641 | `641 Engine Variable Geometry Turbocharger Actuator #1` | continuous | 100.0% | 253 | no | — |
| 91 | `91 Accelerator Pedal Position 1` | continuous | 100.0% | 279 | no | — |
| 101 | `101 Engine Crankcase Pressure 1` | continuous | 100.0% | 375 | no | — |
| 182 | `182 Engine Trip Fuel` | continuous | 99.9% | 528 | no | yes |
| 250 | `250 Engine Total Fuel Used` | continuous | 99.9% | 530 | no | yes |
| 2659 | `2659 Engine Exhaust Gas Recirculation 1 Mass Flow Rate` | continuous | 100.0% | 662 | no | — |
| 247 | `247 Engine Total Hours of Operation` | continuous | 99.2% | 758 | no | yes |
| 3030 | `3030 Transmission Torque Converter Ratio` | continuous | 50.4% | 789 | no | — |
| 515 | `515 Engine's Desired Operating Speed` | continuous | 99.9% | 801 | no | — |
| 171 | `171 Ambient Air Temperature` | continuous | 99.9% | 1053 | no | — |
| 183 | `183 Engine Fuel Rate` | continuous | 100.0% | 1095 | no | — |
| 1172 | `1172 Engine Turbocharger 1 Compressor Intake Temperature` | continuous | 100.0% | 1100 | no | — |
| 904 | `904 Front Axle Speed` | continuous | 99.9% | 1213 | no | — |
| 1136 | `1136 Engine ECU Temperature` | continuous | 100.0% | 1494 | no | — |
| 412 | `412 Engine Exhaust Gas Recirculation 1 Temperature` | continuous | 100.0% | 1524 | no | — |
| 177 | `177 Transmission Oil Temperature 1` | continuous | 99.9% | 1835 | no | — |
| 132 | `132 Engine Intake Air Mass Flow Rate` | continuous | 100.0% | 2171 | no | — |
| 249 | `249 Engine Total Revolutions` | continuous | 99.2% | 2649 | yes | yes |
| 4765 | `4765 Aftertreatment 1 Diesel Oxidation Catalyst Intake Temperature` | continuous | 100.0% | 3114 | no | — |
| 3241 | `3241 Aftertreatment 1 Exhaust Temperature 1` | continuous | 100.0% | 3165 | no | — |
| 4363 | `4363 Aftertreatment 1 SCR Outlet Temperature` | continuous | 100.0% | 3823 | no | — |
| 4360 | `4360 Aftertreatment 1 SCR Intake Temperature` | continuous | 100.0% | 3994 | no | — |
| 5862 | `5862 Aftertreatment 1 SCR Intermediate Temperature` | continuous | 100.0% | 3994 | no | — |
| 3242 | `3242 Aftertreatment 1 Diesel Particulate Filter Intake Temperature` | continuous | 100.0% | 4071 | no | — |
| 3246 | `3246 Aftertreatment 1 Diesel Particulate Filter Outlet Temperature` | continuous | 100.0% | 4162 | no | — |
| 7319 | `7319 Cruise Control Speed` | continuous | 100.0% | 4984 | no | — |
| 84 | `84 Wheel-Based Vehicle Speed` | continuous | 100.0% | 4984 | no | — |
| 187 | `187 Power Takeoff Set Speed` | continuous | 100.0% | 5572 | no | — |
| 3226 | `3226 Aftertreatment 1 Outlet NOx 1` | continuous | 99.8% | 6486 | no | — |
| 1209 | `1209 Engine Exhaust Bank 1 Pressure 1` | continuous | 100.0% | 7698 | no | — |
| 245 | `245 Total Vehicle Distance` | continuous | 100.0% | 8607 | no | yes |
| 244 | `244 Trip Distance` | continuous | 100.0% | 8611 | no | yes |
| 5313 | `5313 Commanded Engine Fuel Rail Pressure` | continuous | 100.0% | 10335 | no | — |
| 103 | `103 Engine Turbocharger 1 Speed` | continuous | 99.9% | 11245 | yes | — |
| 5052 | `5052 Transmission Clutch/Converter Input Speed` | continuous | 53.0% | 14246 | no | — |
| 190 | `190 Engine Speed` | continuous | 99.9% | 15103 | no | — |
| 157 | `157 Engine Fuel 1 Injector Metering Rail 1 Pressure` | continuous | 100.0% | 17031 | no | — |
| 3216 | `3216 Engine Exhaust 1 NOx 1` | continuous | 99.9% | 17226 | no | — |
| 191 | `191 Transmission 1 Output Shaft Speed` | continuous | 99.6% | 17307 | no | — |
| 161 | `161 Transmission 1 Input Shaft Speed` | continuous | 99.6% | 20402 | no | — |
| 184 | `184 Engine Instantaneous Fuel Economy` | continuous | 100.0% | 25845 | no | — |
| 5466 | `5466 Aftertreatment 1 Diesel Particulate Filter Soot Load Regeneration Threshold` | continuous | 100.0% | 30207 | no | — |
| 3721 | `3721 Aftertreatment 1 Diesel Particulate Filter Time Since Last Active Regeneration` | continuous | 100.0% | 70727 | yes | yes |
| 918 | `918 Trip Distance (High Resolution)` | continuous | 100.0% | 89752 | yes | yes |
| 4191 | `4191 Engine Requested Torque (Fractional)` | event | 8.6% | 1 | yes | — |
| 4207 | `4207 Message Checksum` | event | 8.6% | 1 | yes | — |
| 4206 | `4206 Message Counter` | event | 8.6% | 1 | yes | — |
| 3544 | `3544 Time Remaining in Engine Operating State` | event | 16.4% | 1 | yes | — |
| 518 | `518 Engine Requested Torque/Torque Limit` | event | 8.6% | 127 | yes | — |
| 898 | `898 Engine Requested Speed/Speed Limit` | event | 8.6% | 14414 | no | — |
| 5015 | `5015 Momentary Engine Maximum Power Enable` | step | 99.6% | 1 | yes | — |
| 2945 | `2945 Active Shift Console Indicator` | step | 100.0% | 2 | yes | — |
| 3231 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | step | 99.8% | 2 | yes | — |
| 3239 | `3239 Aftertreatment 2 Intake Dew Point` | step | 99.9% | 2 | yes | — |
| 975 | `975 Engine Fan 1 Estimated Percent Speed` | step | 100.0% | 2 | yes | — |
| 986 | `986 Engine Fan 1 Requested Percent Speed` | step | 96.1% | 2 | yes | — |
| 574 | `574 Transmission Shift In Process` | step | 99.6% | 2 | yes | — |
| 573 | `573 Transmission Torque Converter Lockup Engaged` | step | 99.6% | 2 | yes | — |
| 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | step | 99.6% | 2 | yes | — |
| 3229 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | step | 99.8% | 3 | yes | — |
| 3230 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | step | 99.8% | 3 | yes | — |
| 2979 | `2979 Vehicle Acceleration Rate Limit Status` | step | 99.9% | 3 | yes | — |
| 3232 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | step | 99.8% | 4 | yes | — |
| 523 | `523 Transmission Current Gear` | step | 100.0% | 7 | yes | — |
| 524 | `524 Transmission Selected Gear` | step | 100.0% | 7 | yes | — |

## 🟢 Threshold audit — the code-book boundary

The step rule turns on an arbitrary number: at most 16 distinct integer values. This section audits every signal close enough to that cutoff that **the threshold, rather than the data, decides its type**.

The band is integer-valued signals with 4–64 distinct values, derived as `STEP_MAX_CODES / 4` to `STEP_MAX_CODES × 4` so that it tracks the threshold it polices instead of adding two more hand-picked bounds.

**It is built to empty out.** Each row needs a verdict taken from the signal's physical definition, recorded in `SIGNAL_REVIEW`. Once given, the row reports as resolved. A list that shows the same rows every run becomes wallpaper; a list whose only interesting state is *a new unreviewed signal* stays worth reading.

**15 in band · 0 unreviewed · 2 overridden by physics.**

### Verdicts on record

| Flag | SPN | Signal | Distinct | Statistic | Verdict | Basis |
|---|--:|---|--:|---|---|---|
| 🟡 | 4154 | `4154 Actual Engine - Percent Torque (Fractional)` | 4 | step | **continuous** | fractional adder to SPN 513, 0.125%/bit, 0-0.875% (data dictionary) — column values exceed that range |
| 🟢 | 3232 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 4 | step | **step** | FMI — an enumerated J1939 failure-mode identifier |
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | step | **step** | 7 discrete gear positions |
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | step | **step** | 7 discrete gear positions |
| 🟡 | 2978 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 14 | step | **continuous** | percent torque; data dictionary names the sources as cooling fan, air compressor, air conditioning |
| 🟢 | 1717 | `1717 Actual Maximum Available Retarder - Percent Torque` | 19 | continuous | **continuous** | percent torque |
| 🟢 | 5398 | `5398 Estimated Pumping - Percent Torque` | 27 | continuous | **continuous** | percent torque |
| 🟢 | 3031 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 28 | continuous | **continuous** | temperature |
| 🟢 | 514 | `514 Nominal Friction - Percent Torque` | 29 | continuous | **continuous** | percent torque |
| 🟢 | 1087 | `1087 Service Brake Circuit 1 Air Pressure` | 32 | continuous | **continuous** | air pressure |
| 🟢 | 1088 | `1088 Service Brake Circuit 2 Air Pressure` | 32 | continuous | **continuous** | air pressure |
| 🟢 | 105 | `105 Engine Intake Manifold 1 Temperature` | 39 | continuous | **continuous** | temperature |
| 🟢 | 110 | `110 Engine Coolant Temperature` | 42 | continuous | **continuous** | temperature |
| 🟢 | 117 | `117 Brake Primary Pressure` | 64 | continuous | **continuous** | pressure |
| 🟢 | 118 | `118 Brake Secondary Pressure` | 64 | continuous | **continuous** | pressure |

🟡 marks a verdict that **changed** the type the statistic assigned; 🟢 marks one that confirmed it. A verdict applies in both directions, so a code book with many states can be forced back to `step` — which is why reviewing a signal is recorded separately from declaring it continuous.

Why this matters here: percent torque is one physical quantity, yet its members span 4 to 101 distinct values in this dataset (`4154`, `2978`, `5398`, `514`, `513`, `2432`, `512`). The two that barely move fell below the threshold and were typed as enums. That is a fact about this truck's engine, not evidence of a code book.

## How each type is recognised

- **event** — active for less than 50% of the drive, measured as `n_samples x median_period / elapsed_span` from the signal's own timestamps. Absence is the normal state (a command PGN sends only while something is commanding), so filling the gaps fabricates activity that never happened.
- **step** — integer-valued with at most 16 distinct codes: a gear, mode or status enum. Values between the codes do not exist, so neither interpolating them nor averaging them is meaningful.
- **continuous** — everything else, including coarsely-quantised sensors. A pressure reported in whole kPa has few distinct values but the quantity between them exists, so it keeps continuous handling.

These three rules give the **statistical** type. Where a signal falls in the audit band above, a recorded physics verdict takes precedence, so the `Type` column is the statistic *after* review. The statistic flags; physics decides — the same rule this project applies to η².

The **accumulator** column is not a fourth type. It marks signals that only ever count up (≥ 99% of their *changes* are upward): odometers, total hours, total revolutions, filter timers. They interpolate linearly like any continuous signal, but a window summarises them by last − first, because their mean is a statement about *when* in the drive the window sits — the strongest trip-identity leak in the data.
