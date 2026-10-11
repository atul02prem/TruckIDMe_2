# CAN sampling rate — Δt characterised three ways

Source: `G1_Subject1.csv` (62 CAN signals). Δt = gap between consecutive timestamps of each signal's `TimeXXX` column.

- **mode Hz** = native cadence (most common Δt) — the ECU's design rate.
- **median Hz** = robust typical rate (what `build_processed_data` uses).
- **mean Hz** = throughput (N/duration) — sags with dropout/log-off.
- **dropout %** = share of native-cadence samples that never arrived.

## Native-rate buckets (by mode Hz)

| Nominal Hz | # signals |
|---:|---:|
| 100 | 6 |
| 50 | 16 |
| 20 | 8 |
| 10 | 21 |
| 2 | 6 |
| 1 | 5 |

## Dropout-flagged signals (throughput > 5% below native): 4

| SPN | Signal | mode Hz | mean Hz | dropout % | max gap (s) |
|---:|---|---:|---:|---:|---:|
| 3030 | 3030 Transmission Torque Converter Ratio | 50.00 | 23.10 | 53.8 | 10.16 |
| 5052 | 5052 Transmission Clutch/Converter Input Spe | 50.00 | 25.08 | 49.8 | 0.21 |
| 1087 | 1087 Service Brake Circuit 1 Air Pressure | 1.00 | 0.93 | 7.2 | 22.00 |
| 1088 | 1088 Service Brake Circuit 2 Air Pressure | 1.00 | 0.93 | 7.2 | 22.00 |

## Per-signal (sorted fast → slow by native cadence)

| SPN | Signal | n | mode Hz | median Hz | mean Hz | mode Δt (s) | median Δt (s) | mean Δt (s) | max gap (s) | dropout % |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 191 | 191 Transmission 1 Output Shaft Speed | 261,210 | 100.000 | 100.110 | 99.647 | 0.0100 | 0.0100 | 0.0100 | 0.047 | 0.4 |
| 573 | 573 Transmission Torque Converter Lockup Eng | 261,210 | 100.000 | 100.110 | 99.647 | 0.0100 | 0.0100 | 0.0100 | 0.047 | 0.4 |
| 4816 | 4816 Transmission Torque Converter Lockup Tr | 261,210 | 100.000 | 100.110 | 99.647 | 0.0100 | 0.0100 | 0.0100 | 0.047 | 0.4 |
| 161 | 161 Transmission 1 Input Shaft Speed | 261,210 | 100.000 | 100.110 | 99.647 | 0.0100 | 0.0100 | 0.0100 | 0.047 | 0.4 |
| 574 | 574 Transmission Shift In Process | 261,210 | 100.000 | 100.110 | 99.647 | 0.0100 | 0.0100 | 0.0100 | 0.047 | 0.4 |
| 5015 | 5015 Momentary Engine Maximum Power Enable | 261,210 | 100.000 | 100.110 | 99.647 | 0.0100 | 0.0100 | 0.0100 | 0.047 | 0.4 |
| 2432 | 2432 Engine Demand – Percent Torque | 130,524 | 50.000 | 50.030 | 49.792 | 0.0200 | 0.0200 | 0.0201 | 0.058 | 0.4 |
| 512 | 512 Driver's Demand Engine - Percent Torque | 130,524 | 50.000 | 50.030 | 49.792 | 0.0200 | 0.0200 | 0.0201 | 0.058 | 0.4 |
| 91 | 91 Accelerator Pedal Position 1 | 130,728 | 50.000 | 50.060 | 49.870 | 0.0200 | 0.0200 | 0.0201 | 0.054 | 0.3 |
| 513 | 513 Actual Engine - Percent Torque | 130,524 | 50.000 | 50.030 | 49.792 | 0.0200 | 0.0200 | 0.0201 | 0.058 | 0.4 |
| 3357 | 3357 Actual Maximum Available Engine - Perce | 130,728 | 50.000 | 50.060 | 49.870 | 0.0200 | 0.0200 | 0.0201 | 0.054 | 0.3 |
| 4154 | 4154 Actual Engine - Percent Torque (Fractio | 130,524 | 50.000 | 50.030 | 49.792 | 0.0200 | 0.0200 | 0.0201 | 0.058 | 0.4 |
| 3239 | 3239 Aftertreatment 2 Intake Dew Point | 130,574 | 50.000 | 50.043 | 49.812 | 0.0200 | 0.0200 | 0.0201 | 0.067 | 0.4 |
| 515 | 515 Engine's Desired Operating Speed | 130,574 | 50.000 | 50.043 | 49.812 | 0.0200 | 0.0200 | 0.0201 | 0.067 | 0.4 |
| 190 | 190 Engine Speed | 130,524 | 50.000 | 50.030 | 49.792 | 0.0200 | 0.0200 | 0.0201 | 0.058 | 0.4 |
| 2978 | 2978 Estimated Engine Parasitic Losses - Per | 130,574 | 50.000 | 50.043 | 49.812 | 0.0200 | 0.0200 | 0.0201 | 0.067 | 0.4 |
| 514 | 514 Nominal Friction - Percent Torque | 130,574 | 50.000 | 50.043 | 49.812 | 0.0200 | 0.0200 | 0.0201 | 0.067 | 0.4 |
| 5398 | 5398 Estimated Pumping - Percent Torque | 130,728 | 50.000 | 50.060 | 49.870 | 0.0200 | 0.0200 | 0.0201 | 0.054 | 0.3 |
| 92 | 92 Engine Percent Load At Current Speed | 130,728 | 50.000 | 50.060 | 49.870 | 0.0200 | 0.0200 | 0.0201 | 0.054 | 0.3 |
| 3030 | 3030 Transmission Torque Converter Ratio | 60,554 | 50.000 | 49.880 | 23.100 | 0.0200 | 0.0200 | 0.0433 | 10.157 | 53.8 |
| 5052 | 5052 Transmission Clutch/Converter Input Spe | 65,740 | 50.000 | 49.917 | 25.078 | 0.0200 | 0.0200 | 0.0399 | 0.205 | 49.8 |
| 2979 | 2979 Vehicle Acceleration Rate Limit Status | 183,099 | 50.000 | 67.078 | 69.849 | 0.0200 | 0.0149 | 0.0143 | 0.054 | 0.0 |
| 3216 | 3216 Engine Exhaust 1 NOx 1 | 52,068 | 20.000 | 19.999 | 19.863 | 0.0500 | 0.0500 | 0.0503 | 0.102 | 0.7 |
| 3231 | 3231 Aftertreatment 1 Outlet Wide-Range Perc | 52,285 | 20.000 | 20.027 | 19.946 | 0.0500 | 0.0499 | 0.0501 | 0.102 | 0.3 |
| 3230 | 3230 Aftertreatment 1 Outlet NOx 1 Reading S | 52,285 | 20.000 | 20.027 | 19.946 | 0.0500 | 0.0499 | 0.0501 | 0.102 | 0.3 |
| 3229 | 3229 Aftertreatment 1 Outlet Gas Sensor 1 at | 52,285 | 20.000 | 20.027 | 19.946 | 0.0500 | 0.0499 | 0.0501 | 0.102 | 0.3 |
| 3226 | 3226 Aftertreatment 1 Outlet NOx 1 | 47,100 | 20.000 | 20.028 | 19.941 | 0.0500 | 0.0499 | 0.0501 | 0.102 | 0.3 |
| 3232 | 3232 Aftertreatment 1 Outlet Gas Sensor 1 He | 52,285 | 20.000 | 20.027 | 19.946 | 0.0500 | 0.0499 | 0.0501 | 0.102 | 0.3 |
| 2659 | 2659 Engine Exhaust Gas Recirculation 1 Mass | 52,100 | 19.608 | 19.994 | 19.875 | 0.0510 | 0.0500 | 0.0503 | 0.102 | 0.0 |
| 132 | 132 Engine Intake Air Mass Flow Rate | 52,100 | 19.608 | 19.994 | 19.875 | 0.0510 | 0.0500 | 0.0503 | 0.102 | 0.0 |
| 907 | 907 Relative Speed; Rear Axle #1, Left Wheel | 26,012 | 10.000 | 9.979 | 9.923 | 0.1000 | 0.1002 | 0.1008 | 0.205 | 0.8 |
| 524 | 524 Transmission Selected Gear | 26,208 | 10.000 | 10.000 | 9.998 | 0.1000 | 0.1000 | 0.1000 | 0.200 | 0.0 |
| 526 | 526 Transmission Actual Gear Ratio | 26,208 | 10.000 | 10.000 | 9.998 | 0.1000 | 0.1000 | 0.1000 | 0.200 | 0.0 |
| 906 | 906 Relative Speed; Front Axle, Right Wheel | 26,012 | 10.000 | 9.979 | 9.923 | 0.1000 | 0.1002 | 0.1008 | 0.205 | 0.8 |
| 904 | 904 Front Axle Speed | 26,012 | 10.000 | 9.979 | 9.923 | 0.1000 | 0.1002 | 0.1008 | 0.205 | 0.8 |
| 905 | 905 Relative Speed; Front Axle, Left Wheel | 26,012 | 10.000 | 9.979 | 9.923 | 0.1000 | 0.1002 | 0.1008 | 0.205 | 0.8 |
| 1209 | 1209 Engine Exhaust Bank 1 Pressure 1 | 26,090 | 10.000 | 9.999 | 9.953 | 0.1000 | 0.1000 | 0.1005 | 0.203 | 0.5 |
| 184 | 184 Engine Instantaneous Fuel Economy | 26,143 | 10.000 | 9.999 | 9.973 | 0.1000 | 0.1000 | 0.1003 | 0.202 | 0.3 |
| 7319 | 7319 Cruise Control Speed | 26,107 | 10.000 | 9.999 | 9.959 | 0.1000 | 0.1000 | 0.1004 | 0.201 | 0.4 |
| 5313 | 5313 Commanded Engine Fuel Rail Pressure | 26,173 | 10.000 | 9.999 | 9.984 | 0.1000 | 0.1000 | 0.1002 | 0.201 | 0.2 |
| 183 | 183 Engine Fuel Rate | 26,143 | 10.000 | 9.999 | 9.973 | 0.1000 | 0.1000 | 0.1003 | 0.202 | 0.3 |
| 27 | 27 Engine Exhaust Gas Recirculation 1 Valve  | 25,959 | 10.000 | 9.999 | 9.903 | 0.1000 | 0.1000 | 0.1010 | 0.202 | 1.0 |
| 1717 | 1717 Actual Maximum Available Retarder - Per | 26,150 | 10.000 | 9.999 | 9.976 | 0.1000 | 0.1000 | 0.1002 | 0.203 | 0.2 |
| 2945 | 2945 Active Shift Console Indicator | 26,190 | 10.000 | 10.000 | 9.991 | 0.1000 | 0.1000 | 0.1001 | 0.202 | 0.1 |
| 641 | 641 Engine Variable Geometry Turbocharger Ac | 26,151 | 10.000 | 9.999 | 9.976 | 0.1000 | 0.1000 | 0.1002 | 0.201 | 0.2 |
| 51 | 51 Engine Throttle Valve 1 Position 1 | 26,143 | 10.000 | 9.999 | 9.973 | 0.1000 | 0.1000 | 0.1003 | 0.202 | 0.3 |
| 523 | 523 Transmission Current Gear | 26,208 | 10.000 | 10.000 | 9.998 | 0.1000 | 0.1000 | 0.1000 | 0.200 | 0.0 |
| 84 | 84 Wheel-Based Vehicle Speed | 26,171 | 10.000 | 9.999 | 9.984 | 0.1000 | 0.1000 | 0.1002 | 0.205 | 0.2 |
| 908 | 908 Relative Speed; Rear Axle #1, Right Whee | 26,012 | 10.000 | 9.979 | 9.923 | 0.1000 | 0.1002 | 0.1008 | 0.205 | 0.8 |
| 1242 | 1242 Instantaneous Estimated Brake Power | 26,090 | 10.000 | 9.999 | 9.953 | 0.1000 | 0.1000 | 0.1005 | 0.203 | 0.5 |
| 187 | 187 Power Takeoff Set Speed | 26,146 | 10.000 | 9.999 | 9.974 | 0.1000 | 0.1000 | 0.1003 | 0.202 | 0.3 |
| 3610 | 3610 Aftertreatment 1 Diesel Particulate Fil | 5,227 | 2.000 | 2.000 | 1.994 | 0.5000 | 0.5001 | 0.5015 | 1.028 | 0.3 |
| 3251 | 3251 Aftertreatment 1 Diesel Particulate Fil | 5,228 | 2.000 | 2.000 | 1.994 | 0.5000 | 0.5001 | 0.5014 | 1.018 | 0.3 |
| 101 | 101 Engine Crankcase Pressure 1 | 5,207 | 2.000 | 2.000 | 1.986 | 0.5000 | 0.5001 | 0.5034 | 4.000 | 0.7 |
| 102 | 102 Engine Intake Manifold #1 Pressure | 5,241 | 2.000 | 2.000 | 1.999 | 0.5000 | 0.5001 | 0.5002 | 1.002 | 0.0 |
| 100 | 100 Engine Oil Pressure 1 | 5,207 | 2.000 | 2.000 | 1.986 | 0.5000 | 0.5001 | 0.5034 | 4.000 | 0.7 |
| 157 | 157 Engine Fuel 1 Injector Metering Rail 1 P | 5,242 | 2.000 | 2.000 | 2.000 | 0.5000 | 0.5001 | 0.5001 | 0.543 | 0.0 |
| 118 | 118 Brake Secondary Pressure | 2,622 | 1.000 | 1.000 | 1.000 | 1.0000 | 1.0000 | 1.0000 | 1.030 | 0.0 |
| 117 | 117 Brake Primary Pressure | 2,622 | 1.000 | 1.000 | 1.000 | 1.0000 | 1.0000 | 1.0000 | 1.030 | 0.0 |
| 103 | 103 Engine Turbocharger 1 Speed | 2,595 | 1.000 | 1.000 | 0.990 | 1.0000 | 1.0001 | 1.0102 | 7.001 | 1.0 |
| 1087 | 1087 Service Brake Circuit 1 Air Pressure | 2,430 | 1.000 | 1.000 | 0.928 | 1.0000 | 1.0000 | 1.0778 | 22.000 | 7.2 |
| 1088 | 1088 Service Brake Circuit 2 Air Pressure | 2,430 | 1.000 | 1.000 | 0.928 | 1.0000 | 1.0000 | 1.0778 | 22.000 | 7.2 |
