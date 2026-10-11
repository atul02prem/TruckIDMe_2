# CAN sampling rate — verified across all drivers

Source: 46 usable drivers (post `EXCLUDE_DRIVERS`). Δt stats are computed per driver, then aggregated. A signal is flagged only if the issue appears in ≥ 50% of drivers (structural, not a single-driver fluke).

- 🔴 **multi-rate** — |median−mode|/mode > 10% (no stable native rate) in a majority of drivers.
- 🟡 **dropout** — throughput > 5% below native in a majority of drivers.
- 🟢 healthy — mode ≈ median, low dropout.

`native_std` = spread of native (mode) Hz across drivers: 0 = rock-stable, large = no stable rate.

## ⚠️ Flags (3) — read these first

| flag | SPN | Signal | native Hz | % drv dropout | % drv multi-rate | note |
|:--:|--:|--|--:|--:|--:|--|
| 🟡 | 3030 | 3030 Transmission Torque Converter Ratio | 50 | 98% | 2% | state-conditional silence (~49% of samples absent) |
| 🟡 | 5052 | 5052 Transmission Clutch/Converter Input Spe | 50 | 98% | 2% | state-conditional silence (~47% of samples absent) |
| 🔴 | 2979 | 2979 Vehicle Acceleration Rate Limit Status | 50 | 2% | 100% | no stable native rate (bursty / event-driven) |

## Per-signal (all signals, sorted fast → slow)

| flag | SPN | Signal | #drv | native Hz | native_std | dropout med% | %drv drop>5 | %drv multi-rate |
|:--:|--:|--|--:|--:|--:|--:|--:|--:|
| 🟢 | 191 | 191 Transmission 1 Output Shaft Speed | 46 | 100 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 573 | 573 Transmission Torque Converter Lockup Eng | 46 | 100 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 4816 | 4816 Transmission Torque Converter Lockup Tr | 46 | 100 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 161 | 161 Transmission 1 Input Shaft Speed | 46 | 100 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 574 | 574 Transmission Shift In Process | 46 | 100 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 5015 | 5015 Momentary Engine Maximum Power Enable | 46 | 100 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 2432 | 2432 Engine Demand – Percent Torque | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 512 | 512 Driver's Demand Engine - Percent Torque | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 91 | 91 Accelerator Pedal Position 1 | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 513 | 513 Actual Engine - Percent Torque | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 3357 | 3357 Actual Maximum Available Engine - Perce | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 4154 | 4154 Actual Engine - Percent Torque (Fractio | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 3239 | 3239 Aftertreatment 2 Intake Dew Point | 46 | 50 | 0.52 | 0.0 | 2% | 0% |
| 🟢 | 515 | 515 Engine's Desired Operating Speed | 46 | 50 | 0.52 | 0.0 | 2% | 0% |
| 🟢 | 190 | 190 Engine Speed | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 2978 | 2978 Estimated Engine Parasitic Losses - Per | 46 | 50 | 0.52 | 0.0 | 2% | 0% |
| 🟢 | 514 | 514 Nominal Friction - Percent Torque | 46 | 50 | 0.52 | 0.0 | 2% | 0% |
| 🟢 | 5398 | 5398 Estimated Pumping - Percent Torque | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 92 | 92 Engine Percent Load At Current Speed | 46 | 50 | 0.00 | 0.0 | 0% | 0% |
| 🟡 | 3030 | 3030 Transmission Torque Converter Ratio | 46 | 50 | 5.83 | 49.5 | 98% | 2% |
| 🟡 | 5052 | 5052 Transmission Clutch/Converter Input Spe | 46 | 50 | 5.83 | 47.1 | 98% | 2% |
| 🔴 | 2979 | 2979 Vehicle Acceleration Rate Limit Status | 46 | 50 | 138.54 | 0.0 | 2% | 100% |
| 🟢 | 3216 | 3216 Engine Exhaust 1 NOx 1 | 46 | 20 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 3231 | 3231 Aftertreatment 1 Outlet Wide-Range Perc | 46 | 20 | 0.27 | 0.0 | 4% | 0% |
| 🟢 | 3230 | 3230 Aftertreatment 1 Outlet NOx 1 Reading S | 46 | 20 | 0.27 | 0.0 | 4% | 0% |
| 🟢 | 3229 | 3229 Aftertreatment 1 Outlet Gas Sensor 1 at | 46 | 20 | 0.27 | 0.0 | 4% | 0% |
| 🟢 | 3226 | 3226 Aftertreatment 1 Outlet NOx 1 | 46 | 20 | 0.27 | 0.0 | 4% | 0% |
| 🟢 | 3232 | 3232 Aftertreatment 1 Outlet Gas Sensor 1 He | 46 | 20 | 0.27 | 0.0 | 4% | 0% |
| 🟢 | 2659 | 2659 Engine Exhaust Gas Recirculation 1 Mass | 46 | 20 | 0.19 | 0.0 | 0% | 0% |
| 🟢 | 132 | 132 Engine Intake Air Mass Flow Rate | 46 | 20 | 0.19 | 0.0 | 0% | 0% |
| 🟢 | 907 | 907 Relative Speed; Rear Axle #1, Left Wheel | 46 | 10 | 0.00 | 0.2 | 0% | 0% |
| 🟢 | 524 | 524 Transmission Selected Gear | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 526 | 526 Transmission Actual Gear Ratio | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 906 | 906 Relative Speed; Front Axle, Right Wheel | 46 | 10 | 0.00 | 0.2 | 0% | 0% |
| 🟢 | 904 | 904 Front Axle Speed | 46 | 10 | 0.00 | 0.2 | 0% | 0% |
| 🟢 | 905 | 905 Relative Speed; Front Axle, Left Wheel | 46 | 10 | 0.00 | 0.2 | 0% | 0% |
| 🟢 | 1209 | 1209 Engine Exhaust Bank 1 Pressure 1 | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 184 | 184 Engine Instantaneous Fuel Economy | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 7319 | 7319 Cruise Control Speed | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 5313 | 5313 Commanded Engine Fuel Rail Pressure | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 183 | 183 Engine Fuel Rate | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 27 | 27 Engine Exhaust Gas Recirculation 1 Valve  | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 1717 | 1717 Actual Maximum Available Retarder - Per | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 2945 | 2945 Active Shift Console Indicator | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 641 | 641 Engine Variable Geometry Turbocharger Ac | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 51 | 51 Engine Throttle Valve 1 Position 1 | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 523 | 523 Transmission Current Gear | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 84 | 84 Wheel-Based Vehicle Speed | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 908 | 908 Relative Speed; Rear Axle #1, Right Whee | 46 | 10 | 0.00 | 0.2 | 0% | 0% |
| 🟢 | 1242 | 1242 Instantaneous Estimated Brake Power | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 187 | 187 Power Takeoff Set Speed | 46 | 10 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 3610 | 3610 Aftertreatment 1 Diesel Particulate Fil | 46 | 2 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 3251 | 3251 Aftertreatment 1 Diesel Particulate Fil | 46 | 2 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 101 | 101 Engine Crankcase Pressure 1 | 46 | 2 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 102 | 102 Engine Intake Manifold #1 Pressure | 46 | 2 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 100 | 100 Engine Oil Pressure 1 | 46 | 2 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 157 | 157 Engine Fuel 1 Injector Metering Rail 1 P | 46 | 2 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 118 | 118 Brake Secondary Pressure | 46 | 1 | 0.00 | 0.0 | 4% | 0% |
| 🟢 | 117 | 117 Brake Primary Pressure | 46 | 1 | 0.00 | 0.0 | 4% | 0% |
| 🟢 | 103 | 103 Engine Turbocharger 1 Speed | 46 | 1 | 0.00 | 0.0 | 0% | 0% |
| 🟢 | 1087 | 1087 Service Brake Circuit 1 Air Pressure | 46 | 1 | 0.00 | 0.0 | 4% | 0% |
| 🟢 | 1088 | 1088 Service Brake Circuit 2 Air Pressure | 46 | 1 | 0.00 | 0.0 | 4% | 0% |
