# CAN leakage audit — η² over all signals

102 CAN signals (40 EXCLUDED / 62 KEPT), 46 drivers. η² = between-driver variance / total; 1.0 = each driver a distinct band (trip fingerprint), 0.0 = drivers overlap (behavioural). **η² flags; physics decides.**

- 🔴 η² ≥ 0.9 (separates drivers cleanly — leak suspect)  ·  🟡 0.5–0.9  ·  🟢 ≤ 0.5 (behavioural)

## ⚠️ Audit — inconsistencies to review first

**KEPT but η² ≥ 0.9 (possible MISSED leak): 0**
_None — no kept signal separates drivers like a leak._

**EXCLUDED but η² < 0.5 and not a known non-η² cut (questionable): 13**

| η² | SPN | Signal |
|--:|--:|---|
| 0.378 | 177 | 177 Transmission Oil Temperature 1 |
| 0.319 | 975 | 975 Engine Fan 1 Estimated Percent Speed |
| 0.239 | 168 | 168 Battery Potential / Power Input 1 |
| 0.166 | 3246 | 3246 Aftertreatment 1 Diesel Particulate Filte |
| 0.164 | 3242 | 3242 Aftertreatment 1 Diesel Particulate Filte |
| 0.142 | 5862 | 5862 Aftertreatment 1 SCR Intermediate Tempera |
| 0.142 | 4360 | 4360 Aftertreatment 1 SCR Intake Temperature |
| 0.136 | 412 | 412 Engine Exhaust Gas Recirculation 1 Tempera |
| 0.127 | 4363 | 4363 Aftertreatment 1 SCR Outlet Temperature |
| 0.100 | 986 | 986 Engine Fan 1 Requested Percent Speed |
| 0.088 | 4765 | 4765 Aftertreatment 1 Diesel Oxidation Catalys |
| 0.088 | 3241 | 3241 Aftertreatment 1 Exhaust Temperature 1 |
| 0.078 | 110 | 110 Engine Coolant Temperature |

## All CAN signals — ranked by η² (leak → behavioural)

| η² | flag | status | SPN | Signal | note |
|--:|:--:|:--|--:|---|---|
| 1.000 | 🔴 | EXCLUDED | 235 | 235 Engine Total Idle Hours |  |
| 1.000 | 🔴 | EXCLUDED | 182 | 182 Engine Trip Fuel |  |
| 1.000 | 🔴 | EXCLUDED | 250 | 250 Engine Total Fuel Used |  |
| 1.000 | 🔴 | EXCLUDED | 918 | 918 Trip Distance (High Resolution) |  |
| 1.000 | 🔴 | EXCLUDED | 244 | 244 Trip Distance |  |
| 1.000 | 🔴 | EXCLUDED | 245 | 245 Total Vehicle Distance |  |
| 1.000 | 🔴 | EXCLUDED | 249 | 249 Engine Total Revolutions |  |
| 1.000 | 🔴 | EXCLUDED | 247 | 247 Engine Total Hours of Operation |  |
| 1.000 | 🔴 | EXCLUDED | 236 | 236 Engine Total Idle Fuel Used |  |
| 0.999 | 🔴 | EXCLUDED | 185 | 185 Engine Average Fuel Economy |  |
| 0.999 | 🔴 | EXCLUDED | 1029 | 1029 Trip Average Fuel Rate |  |
| 0.998 | 🔴 | EXCLUDED | 1761 | 1761 Aftertreatment 1 Diesel Exhaust Fluid Tan |  |
| 0.998 | 🔴 | EXCLUDED | 96 | 96 Fuel Level 1 |  |
| 0.986 | 🔴 | EXCLUDED | 3031 | 3031 Aftertreatment 1 Diesel Exhaust Fluid Tan |  |
| 0.968 | 🔴 | EXCLUDED | 171 | 171 Ambient Air Temperature |  |
| 0.948 | 🔴 | EXCLUDED | 5466 | 5466 Aftertreatment 1 Diesel Particulate Filte |  |
| 0.941 | 🔴 | EXCLUDED | 1172 | 1172 Engine Turbocharger 1 Compressor Intake T |  |
| 0.937 | 🔴 | EXCLUDED | 3721 | 3721 Aftertreatment 1 Diesel Particulate Filte |  |
| 0.743 | 🟡 | EXCLUDED | 108 | 108 Barometric Pressure |  |
| 0.731 | 🟡 | EXCLUDED | 105 | 105 Engine Intake Manifold 1 Temperature |  |
| 0.569 | 🟡 | EXCLUDED | 1136 | 1136 Engine ECU Temperature |  |
| 0.378 | 🟢 | EXCLUDED | 177 | 177 Transmission Oil Temperature 1 |  |
| 0.319 | 🟢 | EXCLUDED | 975 | 975 Engine Fan 1 Estimated Percent Speed |  |
| 0.244 | 🟢 | KEPT | 2978 | 2978 Estimated Engine Parasitic Losses - Perce |  |
| 0.239 | 🟢 | EXCLUDED | 168 | 168 Battery Potential / Power Input 1 |  |
| 0.166 | 🟢 | EXCLUDED | 3246 | 3246 Aftertreatment 1 Diesel Particulate Filte |  |
| 0.164 | 🟢 | EXCLUDED | 3242 | 3242 Aftertreatment 1 Diesel Particulate Filte |  |
| 0.142 | 🟢 | EXCLUDED | 5862 | 5862 Aftertreatment 1 SCR Intermediate Tempera |  |
| 0.142 | 🟢 | EXCLUDED | 4360 | 4360 Aftertreatment 1 SCR Intake Temperature |  |
| 0.136 | 🟢 | EXCLUDED | 412 | 412 Engine Exhaust Gas Recirculation 1 Tempera |  |
| 0.127 | 🟢 | EXCLUDED | 4363 | 4363 Aftertreatment 1 SCR Outlet Temperature |  |
| 0.127 | 🟢 | KEPT | 3251 | 3251 Aftertreatment 1 Diesel Particulate Filte |  |
| 0.100 | 🟢 | EXCLUDED | 986 | 986 Engine Fan 1 Requested Percent Speed |  |
| 0.099 | 🟢 | KEPT | 3232 | 3232 Aftertreatment 1 Outlet Gas Sensor 1 Heat |  |
| 0.098 | 🟢 | KEPT | 3226 | 3226 Aftertreatment 1 Outlet NOx 1 |  |
| 0.093 | 🟢 | KEPT | 3231 | 3231 Aftertreatment 1 Outlet Wide-Range Percen |  |
| 0.093 | 🟢 | KEPT | 3239 | 3239 Aftertreatment 2 Intake Dew Point |  |
| 0.091 | 🟢 | KEPT | 3230 | 3230 Aftertreatment 1 Outlet NOx 1 Reading Sta |  |
| 0.091 | 🟢 | KEPT | 3229 | 3229 Aftertreatment 1 Outlet Gas Sensor 1 at T |  |
| 0.088 | 🟢 | EXCLUDED | 4765 | 4765 Aftertreatment 1 Diesel Oxidation Catalys |  |
| 0.088 | 🟢 | EXCLUDED | 3241 | 3241 Aftertreatment 1 Exhaust Temperature 1 |  |
| 0.078 | 🟢 | EXCLUDED | 110 | 110 Engine Coolant Temperature |  |
| 0.064 | 🟢 | KEPT | 3357 | 3357 Actual Maximum Available Engine - Percent |  |
| 0.053 | 🟢 | KEPT | 641 | 641 Engine Variable Geometry Turbocharger Actu |  |
| 0.050 | 🟢 | KEPT | 3216 | 3216 Engine Exhaust 1 NOx 1 |  |
| 0.042 | 🟢 | KEPT | 5398 | 5398 Estimated Pumping - Percent Torque |  |
| 0.036 | 🟢 | KEPT | 514 | 514 Nominal Friction - Percent Torque |  |
| 0.035 | 🟢 | KEPT | 1209 | 1209 Engine Exhaust Bank 1 Pressure 1 |  |
| 0.025 | 🟢 | KEPT | 3610 | 3610 Aftertreatment 1 Diesel Particulate Filte |  |
| 0.023 | 🟢 | KEPT | 515 | 515 Engine's Desired Operating Speed |  |
| 0.023 | 🟢 | KEPT | 3030 | 3030 Transmission Torque Converter Ratio |  |
| 0.020 | 🟢 | KEPT | 2945 | 2945 Active Shift Console Indicator |  |
| 0.020 | 🟢 | KEPT | 4816 | 4816 Transmission Torque Converter Lockup Tran |  |
| 0.020 | 🟢 | KEPT | 27 | 27 Engine Exhaust Gas Recirculation 1 Valve Po |  |
| 0.019 | 🟢 | KEPT | 132 | 132 Engine Intake Air Mass Flow Rate |  |
| 0.019 | 🟢 | KEPT | 103 | 103 Engine Turbocharger 1 Speed |  |
| 0.018 | 🟢 | KEPT | 84 | 84 Wheel-Based Vehicle Speed |  |
| 0.018 | 🟢 | KEPT | 7319 | 7319 Cruise Control Speed |  |
| 0.018 | 🟢 | KEPT | 904 | 904 Front Axle Speed |  |
| 0.018 | 🟢 | KEPT | 191 | 191 Transmission 1 Output Shaft Speed |  |
| 0.018 | 🟢 | KEPT | 4154 | 4154 Actual Engine - Percent Torque (Fractiona |  |
| 0.018 | 🟢 | KEPT | 907 | 907 Relative Speed; Rear Axle #1, Left Wheel |  |
| 0.018 | 🟢 | KEPT | 161 | 161 Transmission 1 Input Shaft Speed |  |
| 0.017 | 🟢 | KEPT | 526 | 526 Transmission Actual Gear Ratio |  |
| 0.017 | 🟢 | KEPT | 523 | 523 Transmission Current Gear |  |
| 0.017 | 🟢 | KEPT | 100 | 100 Engine Oil Pressure 1 |  |
| 0.017 | 🟢 | KEPT | 524 | 524 Transmission Selected Gear |  |
| 0.016 | 🟢 | KEPT | 102 | 102 Engine Intake Manifold #1 Pressure |  |
| 0.016 | 🟢 | KEPT | 2659 | 2659 Engine Exhaust Gas Recirculation 1 Mass F |  |
| 0.016 | 🟢 | KEPT | 5052 | 5052 Transmission Clutch/Converter Input Speed |  |
| 0.015 | 🟢 | KEPT | 187 | 187 Power Takeoff Set Speed |  |
| 0.014 | 🟢 | KEPT | 190 | 190 Engine Speed |  |
| 0.014 | 🟢 | KEPT | 101 | 101 Engine Crankcase Pressure 1 |  |
| 0.013 | 🟢 | KEPT | 1717 | 1717 Actual Maximum Available Retarder - Perce |  |
| 0.012 | 🟢 | KEPT | 157 | 157 Engine Fuel 1 Injector Metering Rail 1 Pre |  |
| 0.011 | 🟢 | KEPT | 574 | 574 Transmission Shift In Process |  |
| 0.011 | 🟢 | KEPT | 5313 | 5313 Commanded Engine Fuel Rail Pressure |  |
| 0.010 | 🟢 | KEPT | 512 | 512 Driver's Demand Engine - Percent Torque |  |
| 0.010 | 🟢 | KEPT | 183 | 183 Engine Fuel Rate |  |
| 0.010 | 🟢 | KEPT | 908 | 908 Relative Speed; Rear Axle #1, Right Wheel |  |
| 0.010 | 🟢 | EXCLUDED | 898 | 898 Engine Requested Speed/Speed Limit | non-η² exclusion (bursty/protocol) |
| 0.010 | 🟢 | KEPT | 1088 | 1088 Service Brake Circuit 2 Air Pressure |  |
| 0.009 | 🟢 | KEPT | 118 | 118 Brake Secondary Pressure |  |
| 0.009 | 🟢 | KEPT | 91 | 91 Accelerator Pedal Position 1 |  |
| 0.009 | 🟢 | KEPT | 1087 | 1087 Service Brake Circuit 1 Air Pressure |  |
| 0.009 | 🟢 | KEPT | 117 | 117 Brake Primary Pressure |  |
| 0.008 | 🟢 | KEPT | 1242 | 1242 Instantaneous Estimated Brake Power |  |
| 0.006 | 🟢 | KEPT | 184 | 184 Engine Instantaneous Fuel Economy |  |
| 0.005 | 🟢 | KEPT | 2432 | 2432 Engine Demand – Percent Torque |  |
| 0.005 | 🟢 | KEPT | 513 | 513 Actual Engine - Percent Torque |  |
| 0.004 | 🟢 | KEPT | 92 | 92 Engine Percent Load At Current Speed |  |
| 0.003 | 🟢 | EXCLUDED | 518 | 518 Engine Requested Torque/Torque Limit | non-η² exclusion (bursty/protocol) |
| 0.002 | 🟢 | KEPT | 573 | 573 Transmission Torque Converter Lockup Engag |  |
| 0.001 | 🟢 | KEPT | 51 | 51 Engine Throttle Valve 1 Position 1 |  |
| 0.000 | 🟢 | KEPT | 906 | 906 Relative Speed; Front Axle, Right Wheel |  |
| 0.000 | 🟢 | KEPT | 905 | 905 Relative Speed; Front Axle, Left Wheel |  |
| 0.000 | 🟢 | KEPT | 2979 | 2979 Vehicle Acceleration Rate Limit Status |  |
| nan | ⚪ | EXCLUDED | 4191 | 4191 Engine Requested Torque (Fractional) | non-η² exclusion (bursty/protocol) |
| nan | ⚪ | EXCLUDED | 4207 | 4207 Message Checksum | non-η² exclusion (bursty/protocol) |
| nan | ⚪ | EXCLUDED | 4206 | 4206 Message Counter | non-η² exclusion (bursty/protocol) |
| nan | ⚪ | KEPT | 5015 | 5015 Momentary Engine Maximum Power Enable |  |
| nan | ⚪ | EXCLUDED | 3544 | 3544 Time Remaining in Engine Operating State | non-η² exclusion (bursty/protocol) |
