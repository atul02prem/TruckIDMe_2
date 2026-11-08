# TruckIDMe — Window-Alignment Null Fractions (Pre-ffill)

**Source driver:** `G1_Subject1.csv`
**Master grid (canloggerTime ticks):** 26,212
**Window:** ±50 ms centered on each tick (100 ms full width)
**Total CAN signals analyzed:** 87

Each row reports, for one CAN signal, what fraction of the 10 Hz master ticks
received *zero* raw samples in their ±50 ms window. A high null fraction means
the signal's native rate is below 10 Hz — ffill will be required for those ticks.

## Distribution summary

- **Dense (null < 1%):** 43 signals — windowing is essentially lossless.
- **Moderate (1% ≤ null < 75%):** 8 signals.
- **Sparse (75% ≤ null < 95%):** 36 signals — ffill spreads each raw value across ~4–20 ticks.
- **Extremely sparse (null ≥ 95%):** 0 signals — ffill spreads each raw value across 20+ ticks.

## Per-signal breakdown (sparsest first)

| # | Signal | Native Hz | Raw samples | Filled ticks | Null % |
|---|---|---:|---:|---:|---:|
| 1 | `3544 Time Remaining in Engine Operating State` | 4.00 | 1,344 | 1,342 | 94.88% |
| 2 | `898 Engine Requested Speed/Speed Limit` | 100.08 | 19,689 | 2,119 | 91.92% |
| 3 | `518 Engine Requested Torque/Torque Limit` | 100.08 | 19,689 | 2,119 | 91.92% |
| 4 | `4191 Engine Requested Torque (Fractional)` | 100.08 | 19,689 | 2,119 | 91.92% |
| 5 | `96 Fuel Level 1` | 1.00 | 2,399 | 2,394 | 90.87% |
| 6 | `1087 Service Brake Circuit 1 Air Pressure` | 1.00 | 2,430 | 2,440 | 90.69% |
| 7 | `1088 Service Brake Circuit 2 Air Pressure` | 1.00 | 2,430 | 2,440 | 90.69% |
| 8 | `975 Engine Fan 1 Estimated Percent Speed` | 1.00 | 2,621 | 2,559 | 90.24% |
| 9 | `1136 Engine ECU Temperature` | 1.00 | 2,611 | 2,563 | 90.22% |
| 10 | `412 Engine Exhaust Gas Recirculation 1 Temperature` | 1.00 | 2,611 | 2,563 | 90.22% |
| 11 | `110 Engine Coolant Temperature` | 1.00 | 2,615 | 2,565 | 90.21% |
| 12 | `103 Engine Turbocharger 1 Speed` | 1.00 | 2,595 | 2,593 | 90.11% |
| 13 | `177 Transmission Oil Temperature 1` | 1.00 | 2,590 | 2,600 | 90.08% |
| 14 | `1761 Aftertreatment 1 Diesel Exhaust Fluid Tank Volume` | 1.00 | 2,617 | 2,615 | 90.02% |
| 15 | `3031 Aftertreatment 1 Diesel Exhaust Fluid Tank Temperature 1` | 1.00 | 2,617 | 2,615 | 90.02% |
| 16 | `5466 Aftertreatment 1 Diesel Particulate Filter Soot Load Regeneration Threshold` | 1.00 | 2,621 | 2,625 | 89.99% |
| 17 | `3721 Aftertreatment 1 Diesel Particulate Filter Time Since Last Active Regeneration` | 1.00 | 2,621 | 2,625 | 89.99% |
| 18 | `1172 Engine Turbocharger 1 Compressor Intake Temperature` | 1.00 | 2,620 | 2,626 | 89.98% |
| 19 | `118 Brake Secondary Pressure` | 1.00 | 2,622 | 2,633 | 89.95% |
| 20 | `117 Brake Primary Pressure` | 1.00 | 2,622 | 2,633 | 89.95% |
| 21 | `168 Battery Potential / Power Input 1` | 1.99 | 5,100 | 5,146 | 80.37% |
| 22 | `3241 Aftertreatment 1 Exhaust Temperature 1` | 2.00 | 5,233 | 5,192 | 80.19% |
| 23 | `3242 Aftertreatment 1 Diesel Particulate Filter Intake Temperature` | 2.00 | 5,233 | 5,192 | 80.19% |
| 24 | `986 Engine Fan 1 Requested Percent Speed` | 2.00 | 5,243 | 5,194 | 80.18% |
| 25 | `4765 Aftertreatment 1 Diesel Oxidation Catalyst Intake Temperature` | 2.00 | 5,214 | 5,224 | 80.07% |
| 26 | `101 Engine Crankcase Pressure 1` | 2.00 | 5,207 | 5,226 | 80.06% |
| 27 | `100 Engine Oil Pressure 1` | 2.00 | 5,207 | 5,226 | 80.06% |
| 28 | `3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | 2.00 | 5,228 | 5,227 | 80.06% |
| 29 | `3246 Aftertreatment 1 Diesel Particulate Filter Outlet Temperature` | 2.00 | 5,234 | 5,227 | 80.06% |
| 30 | `4363 Aftertreatment 1 SCR Outlet Temperature` | 2.00 | 5,242 | 5,235 | 80.03% |
| 31 | `4360 Aftertreatment 1 SCR Intake Temperature` | 2.00 | 5,242 | 5,235 | 80.03% |
| 32 | `5862 Aftertreatment 1 SCR Intermediate Temperature` | 2.00 | 5,238 | 5,239 | 80.01% |
| 33 | `157 Engine Fuel 1 Injector Metering Rail 1 Pressure` | 2.00 | 5,242 | 5,244 | 79.99% |
| 34 | `3610 Aftertreatment 1 Diesel Particulate Filter Outlet Pressure` | 2.00 | 5,227 | 5,247 | 79.98% |
| 35 | `105 Engine Intake Manifold 1 Temperature` | 2.00 | 5,241 | 5,502 | 79.01% |
| 36 | `102 Engine Intake Manifold #1 Pressure` | 2.00 | 5,241 | 5,502 | 79.01% |
| 37 | `3226 Aftertreatment 1 Outlet NOx 1` | 20.03 | 47,100 | 23,619 | 9.89% |
| 38 | `1242 Instantaneous Estimated Brake Power` | 10.00 | 26,090 | 24,148 | 7.87% |
| 39 | `1209 Engine Exhaust Bank 1 Pressure 1` | 10.00 | 26,090 | 24,148 | 7.87% |
| 40 | `3030 Transmission Torque Converter Ratio` | 49.88 | 60,554 | 25,136 | 4.10% |
| 41 | `184 Engine Instantaneous Fuel Economy` | 10.00 | 26,143 | 25,722 | 1.87% |
| 42 | `51 Engine Throttle Valve 1 Position 1` | 10.00 | 26,143 | 25,722 | 1.87% |
| 43 | `183 Engine Fuel Rate` | 10.00 | 26,143 | 25,722 | 1.87% |
| 44 | `27 Engine Exhaust Gas Recirculation 1 Valve Position` | 10.00 | 25,959 | 25,921 | 1.11% |
| 45 | `904 Front Axle Speed` | 9.98 | 26,012 | 25,984 | 0.87% |
| 46 | `908 Relative Speed; Rear Axle #1, Right Wheel` | 9.98 | 26,012 | 25,984 | 0.87% |
| 47 | `907 Relative Speed; Rear Axle #1, Left Wheel` | 9.98 | 26,012 | 25,984 | 0.87% |
| 48 | `906 Relative Speed; Front Axle, Right Wheel` | 9.98 | 26,012 | 25,984 | 0.87% |
| 49 | `905 Relative Speed; Front Axle, Left Wheel` | 9.98 | 26,012 | 25,984 | 0.87% |
| 50 | `84 Wheel-Based Vehicle Speed` | 10.00 | 26,171 | 26,025 | 0.71% |
| 51 | `7319 Cruise Control Speed` | 10.00 | 26,107 | 26,085 | 0.48% |
| 52 | `187 Power Takeoff Set Speed` | 10.00 | 26,146 | 26,093 | 0.45% |
| 53 | `1717 Actual Maximum Available Retarder - Percent Torque` | 10.00 | 26,150 | 26,096 | 0.44% |
| 54 | `5313 Commanded Engine Fuel Rail Pressure` | 10.00 | 26,173 | 26,100 | 0.43% |
| 55 | `5052 Transmission Clutch/Converter Input Speed` | 49.92 | 65,740 | 26,110 | 0.39% |
| 56 | `641 Engine Variable Geometry Turbocharger Actuator #1` | 10.00 | 26,151 | 26,146 | 0.25% |
| 57 | `2945 Active Shift Console Indicator` | 10.00 | 26,190 | 26,183 | 0.11% |
| 58 | `526 Transmission Actual Gear Ratio` | 10.00 | 26,208 | 26,202 | 0.04% |
| 59 | `523 Transmission Current Gear` | 10.00 | 26,208 | 26,202 | 0.04% |
| 60 | `524 Transmission Selected Gear` | 10.00 | 26,208 | 26,202 | 0.04% |
| 61 | `91 Accelerator Pedal Position 1` | 50.06 | 130,728 | 26,212 | 0.00% |
| 62 | `3357 Actual Maximum Available Engine - Percent Torque` | 50.06 | 130,728 | 26,212 | 0.00% |
| 63 | `4154 Actual Engine - Percent Torque (Fractional)` | 50.03 | 130,524 | 26,212 | 0.00% |
| 64 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | 20.03 | 52,285 | 26,212 | 0.00% |
| 65 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | 20.03 | 52,285 | 26,212 | 0.00% |
| 66 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | 20.03 | 52,285 | 26,212 | 0.00% |
| 67 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 20.03 | 52,285 | 26,212 | 0.00% |
| 68 | `513 Actual Engine - Percent Torque` | 50.03 | 130,524 | 26,212 | 0.00% |
| 69 | `512 Driver's Demand Engine - Percent Torque` | 50.03 | 130,524 | 26,212 | 0.00% |
| 70 | `3216 Engine Exhaust 1 NOx 1` | 20.00 | 52,068 | 26,212 | 0.00% |
| 71 | `2659 Engine Exhaust Gas Recirculation 1 Mass Flow Rate` | 19.99 | 52,100 | 26,212 | 0.00% |
| 72 | `190 Engine Speed` | 50.03 | 130,524 | 26,212 | 0.00% |
| 73 | `92 Engine Percent Load At Current Speed` | 50.06 | 130,728 | 26,212 | 0.00% |
| 74 | `132 Engine Intake Air Mass Flow Rate` | 19.99 | 52,100 | 26,212 | 0.00% |
| 75 | `3239 Aftertreatment 2 Intake Dew Point` | 50.04 | 130,574 | 26,212 | 0.00% |
| 76 | `2432 Engine Demand – Percent Torque` | 50.03 | 130,524 | 26,212 | 0.00% |
| 77 | `515 Engine's Desired Operating Speed` | 50.04 | 130,574 | 26,212 | 0.00% |
| 78 | `5398 Estimated Pumping - Percent Torque` | 50.06 | 130,728 | 26,212 | 0.00% |
| 79 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | 50.04 | 130,574 | 26,212 | 0.00% |
| 80 | `5015 Momentary Engine Maximum Power Enable` | 100.11 | 261,210 | 26,212 | 0.00% |
| 81 | `514 Nominal Friction - Percent Torque` | 50.04 | 130,574 | 26,212 | 0.00% |
| 82 | `191 Transmission 1 Output Shaft Speed` | 100.11 | 261,210 | 26,212 | 0.00% |
| 83 | `161 Transmission 1 Input Shaft Speed` | 100.11 | 261,210 | 26,212 | 0.00% |
| 84 | `573 Transmission Torque Converter Lockup Engaged` | 100.11 | 261,210 | 26,212 | 0.00% |
| 85 | `574 Transmission Shift In Process` | 100.11 | 261,210 | 26,212 | 0.00% |
| 86 | `4816 Transmission Torque Converter Lockup Transition in Process` | 100.11 | 261,210 | 26,212 | 0.00% |
| 87 | `2979 Vehicle Acceleration Rate Limit Status` | 67.08 | 183,099 | 26,212 | 0.00% |
