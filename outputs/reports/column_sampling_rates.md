# TruckIDMe — Column Sampling Rates

**Source file:** `G1_Subject1.csv`
**Total columns:** 134

Each data column inherits its sampling rate from its paired timestamp
column. CAN signal columns pair with their `TimeXXX` partner; SparkFun
GPS data columns pair with the appropriate `timestamp*` column.

| # | Column | Paired Time Column | Hz | Non-null samples |
|---|---|---|---:|---:|
| 1 | `Time91` | `(self)` | 50.0597 | 130,728 |
| 2 | `91 Accelerator Pedal Position 1` | `Time91` | 50.0597 | 130,728 |
| 3 | `Time2945` | `(self)` | 9.9996 | 26,190 |
| 4 | `2945 Active Shift Console Indicator` | `Time2945` | 9.9996 | 26,190 |
| 5 | `Time513` | `(self)` | 50.0299 | 130,524 |
| 6 | `513 Actual Engine - Percent Torque` | `Time513` | 50.0299 | 130,524 |
| 7 | `Time4154` | `(self)` | 50.0299 | 130,524 |
| 8 | `4154 Actual Engine - Percent Torque (Fractional)` | `Time4154` | 50.0299 | 130,524 |
| 9 | `Time3357` | `(self)` | 50.0597 | 130,728 |
| 10 | `3357 Actual Maximum Available Engine - Percent Torque` | `Time3357` | 50.0597 | 130,728 |
| 11 | `Time1717` | `(self)` | 9.9990 | 26,150 |
| 12 | `1717 Actual Maximum Available Retarder - Percent Torque` | `Time1717` | 9.9990 | 26,150 |
| 13 | `Time3251` | `(self)` | 1.9997 | 5,228 |
| 14 | `3251 Aftertreatment 1 Diesel Particulate Filter Differential Pressure` | `Time3251` | 1.9997 | 5,228 |
| 15 | `Time3610` | `(self)` | 1.9997 | 5,227 |
| 16 | `3610 Aftertreatment 1 Diesel Particulate Filter Outlet Pressure` | `Time3610` | 1.9997 | 5,227 |
| 17 | `Time3229` | `(self)` | 20.0269 | 52,285 |
| 18 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | `Time3229` | 20.0269 | 52,285 |
| 19 | `Time3232` | `(self)` | 20.0269 | 52,285 |
| 20 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | `Time3232` | 20.0269 | 52,285 |
| 21 | `Time3226` | `(self)` | 20.0276 | 47,100 |
| 22 | `3226 Aftertreatment 1 Outlet NOx 1` | `Time3226` | 20.0276 | 47,100 |
| 23 | `Time3230` | `(self)` | 20.0269 | 52,285 |
| 24 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | `Time3230` | 20.0269 | 52,285 |
| 25 | `Time3231` | `(self)` | 20.0269 | 52,285 |
| 26 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | `Time3231` | 20.0269 | 52,285 |
| 27 | `Time3239` | `(self)` | 50.0430 | 130,574 |
| 28 | `3239 Aftertreatment 2 Intake Dew Point` | `Time3239` | 50.0430 | 130,574 |
| 29 | `Time117` | `(self)` | 1.0000 | 2,622 |
| 30 | `117 Brake Primary Pressure` | `Time117` | 1.0000 | 2,622 |
| 31 | `Time118` | `(self)` | 1.0000 | 2,622 |
| 32 | `118 Brake Secondary Pressure` | `Time118` | 1.0000 | 2,622 |
| 33 | `Time5313` | `(self)` | 9.9990 | 26,173 |
| 34 | `5313 Commanded Engine Fuel Rail Pressure` | `Time5313` | 9.9990 | 26,173 |
| 35 | `Time7319` | `(self)` | 9.9989 | 26,107 |
| 36 | `7319 Cruise Control Speed` | `Time7319` | 9.9989 | 26,107 |
| 37 | `Time512` | `(self)` | 50.0299 | 130,524 |
| 38 | `512 Driver's Demand Engine - Percent Torque` | `Time512` | 50.0299 | 130,524 |
| 39 | `Time515` | `(self)` | 50.0430 | 130,574 |
| 40 | `515 Engine's Desired Operating Speed` | `Time515` | 50.0430 | 130,574 |
| 41 | `Time101` | `(self)` | 1.9997 | 5,207 |
| 42 | `101 Engine Crankcase Pressure 1` | `Time101` | 1.9997 | 5,207 |
| 43 | `Time2432` | `(self)` | 50.0299 | 130,524 |
| 44 | `2432 Engine Demand – Percent Torque` | `Time2432` | 50.0299 | 130,524 |
| 45 | `Time3216` | `(self)` | 19.9992 | 52,068 |
| 46 | `3216 Engine Exhaust 1 NOx 1` | `Time3216` | 19.9992 | 52,068 |
| 47 | `Time1209` | `(self)` | 9.9991 | 26,090 |
| 48 | `1209 Engine Exhaust Bank 1 Pressure 1` | `Time1209` | 9.9991 | 26,090 |
| 49 | `Time2659` | `(self)` | 19.9936 | 52,100 |
| 50 | `2659 Engine Exhaust Gas Recirculation 1 Mass Flow Rate` | `Time2659` | 19.9936 | 52,100 |
| 51 | `Time27` | `(self)` | 9.9986 | 25,959 |
| 52 | `27 Engine Exhaust Gas Recirculation 1 Valve Position` | `Time27` | 9.9986 | 25,959 |
| 53 | `Time157` | `(self)` | 1.9997 | 5,242 |
| 54 | `157 Engine Fuel 1 Injector Metering Rail 1 Pressure` | `Time157` | 1.9997 | 5,242 |
| 55 | `Time183` | `(self)` | 9.9987 | 26,143 |
| 56 | `183 Engine Fuel Rate` | `Time183` | 9.9987 | 26,143 |
| 57 | `Time184` | `(self)` | 9.9987 | 26,143 |
| 58 | `184 Engine Instantaneous Fuel Economy` | `Time184` | 9.9987 | 26,143 |
| 59 | `Time132` | `(self)` | 19.9936 | 52,100 |
| 60 | `132 Engine Intake Air Mass Flow Rate` | `Time132` | 19.9936 | 52,100 |
| 61 | `Time102` | `(self)` | 1.9997 | 5,241 |
| 62 | `102 Engine Intake Manifold #1 Pressure` | `Time102` | 1.9997 | 5,241 |
| 63 | `Time100` | `(self)` | 1.9997 | 5,207 |
| 64 | `100 Engine Oil Pressure 1` | `Time100` | 1.9997 | 5,207 |
| 65 | `Time92` | `(self)` | 50.0597 | 130,728 |
| 66 | `92 Engine Percent Load At Current Speed` | `Time92` | 50.0597 | 130,728 |
| 67 | `Time190` | `(self)` | 50.0299 | 130,524 |
| 68 | `190 Engine Speed` | `Time190` | 50.0299 | 130,524 |
| 69 | `Time51` | `(self)` | 9.9987 | 26,143 |
| 70 | `51 Engine Throttle Valve 1 Position 1` | `Time51` | 9.9987 | 26,143 |
| 71 | `Time103` | `(self)` | 0.9999 | 2,595 |
| 72 | `103 Engine Turbocharger 1 Speed` | `Time103` | 0.9999 | 2,595 |
| 73 | `Time641` | `(self)` | 9.9987 | 26,151 |
| 74 | `641 Engine Variable Geometry Turbocharger Actuator #1` | `Time641` | 9.9987 | 26,151 |
| 75 | `Time2978` | `(self)` | 50.0430 | 130,574 |
| 76 | `2978 Estimated Engine Parasitic Losses - Percent Torque` | `Time2978` | 50.0430 | 130,574 |
| 77 | `Time5398` | `(self)` | 50.0597 | 130,728 |
| 78 | `5398 Estimated Pumping - Percent Torque` | `Time5398` | 50.0597 | 130,728 |
| 79 | `Time904` | `(self)` | 9.9788 | 26,012 |
| 80 | `904 Front Axle Speed` | `Time904` | 9.9788 | 26,012 |
| 81 | `Time1242` | `(self)` | 9.9991 | 26,090 |
| 82 | `1242 Instantaneous Estimated Brake Power` | `Time1242` | 9.9991 | 26,090 |
| 83 | `Time5015` | `(self)` | 100.1099 | 261,210 |
| 84 | `5015 Momentary Engine Maximum Power Enable` | `Time5015` | 100.1099 | 261,210 |
| 85 | `Time514` | `(self)` | 50.0430 | 130,574 |
| 86 | `514 Nominal Friction - Percent Torque` | `Time514` | 50.0430 | 130,574 |
| 87 | `Time187` | `(self)` | 9.9989 | 26,146 |
| 88 | `187 Power Takeoff Set Speed` | `Time187` | 9.9989 | 26,146 |
| 89 | `Time905` | `(self)` | 9.9788 | 26,012 |
| 90 | `905 Relative Speed; Front Axle, Left Wheel` | `Time905` | 9.9788 | 26,012 |
| 91 | `Time906` | `(self)` | 9.9788 | 26,012 |
| 92 | `906 Relative Speed; Front Axle, Right Wheel` | `Time906` | 9.9788 | 26,012 |
| 93 | `Time907` | `(self)` | 9.9788 | 26,012 |
| 94 | `907 Relative Speed; Rear Axle #1, Left Wheel` | `Time907` | 9.9788 | 26,012 |
| 95 | `Time908` | `(self)` | 9.9788 | 26,012 |
| 96 | `908 Relative Speed; Rear Axle #1, Right Wheel` | `Time908` | 9.9788 | 26,012 |
| 97 | `Time1087` | `(self)` | 1.0000 | 2,430 |
| 98 | `1087 Service Brake Circuit 1 Air Pressure` | `Time1087` | 1.0000 | 2,430 |
| 99 | `Time1088` | `(self)` | 1.0000 | 2,430 |
| 100 | `1088 Service Brake Circuit 2 Air Pressure` | `Time1088` | 1.0000 | 2,430 |
| 101 | `Time161` | `(self)` | 100.1099 | 261,210 |
| 102 | `161 Transmission 1 Input Shaft Speed` | `Time161` | 100.1099 | 261,210 |
| 103 | `Time191` | `(self)` | 100.1099 | 261,210 |
| 104 | `191 Transmission 1 Output Shaft Speed` | `Time191` | 100.1099 | 261,210 |
| 105 | `Time526` | `(self)` | 9.9998 | 26,208 |
| 106 | `526 Transmission Actual Gear Ratio` | `Time526` | 9.9998 | 26,208 |
| 107 | `Time5052` | `(self)` | 49.9173 | 65,740 |
| 108 | `5052 Transmission Clutch/Converter Input Speed` | `Time5052` | 49.9173 | 65,740 |
| 109 | `Time523` | `(self)` | 9.9998 | 26,208 |
| 110 | `523 Transmission Current Gear` | `Time523` | 9.9998 | 26,208 |
| 111 | `Time524` | `(self)` | 9.9998 | 26,208 |
| 112 | `524 Transmission Selected Gear` | `Time524` | 9.9998 | 26,208 |
| 113 | `Time574` | `(self)` | 100.1099 | 261,210 |
| 114 | `574 Transmission Shift In Process` | `Time574` | 100.1099 | 261,210 |
| 115 | `Time573` | `(self)` | 100.1099 | 261,210 |
| 116 | `573 Transmission Torque Converter Lockup Engaged` | `Time573` | 100.1099 | 261,210 |
| 117 | `Time4816` | `(self)` | 100.1099 | 261,210 |
| 118 | `4816 Transmission Torque Converter Lockup Transition in Process` | `Time4816` | 100.1099 | 261,210 |
| 119 | `Time3030` | `(self)` | 49.8799 | 60,554 |
| 120 | `3030 Transmission Torque Converter Ratio` | `Time3030` | 49.8799 | 60,554 |
| 121 | `Time2979` | `(self)` | 67.0777 | 183,099 |
| 122 | `2979 Vehicle Acceleration Rate Limit Status` | `Time2979` | 67.0777 | 183,099 |
| 123 | `Time84` | `(self)` | 9.9989 | 26,171 |
| 124 | `84 Wheel-Based Vehicle Speed` | `Time84` | 9.9989 | 26,171 |
| 125 | `canloggerTime` | `(self)` | 10.0005 | 26,212 |
| 126 | `gpsTime` | `(self)` | 10.0000 | 26,212 |
| 127 | `timestampsLocation` | `(self)` | 10.0006 | 26,212 |
| 128 | `longitude` | `timestampsLocation` | 10.0006 | 26,212 |
| 129 | `latitude` | `timestampsLocation` | 10.0006 | 26,212 |
| 130 | `timestampHeading` | `(self)` | 10.0008 | 26,212 |
| 131 | `gpsSpeed` | `timestampHeading` | 10.0008 | 26,212 |
| 132 | `headingDegree` | `timestampHeading` | 10.0008 | 26,212 |
| 133 | `timestampSat` | `(self)` | 10.0005 | 26,212 |
| 134 | `numSats` | `timestampSat` | 10.0005 | 26,212 |
