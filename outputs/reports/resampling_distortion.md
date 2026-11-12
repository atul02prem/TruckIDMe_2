# Resampling distortion — what the 512-point grid does to each channel

**50 channels** × **4 window lengths**, measured on **9 drivers** — three from each awareness group: G1S01, G1S02, G1S03, G2S01, G2S02, G2S03, G3S01, G3S02, G3S03.

`RESIZE_STEPS = 512` is fixed, so the window length sets the grid rate and therefore how violently each channel is resampled.

| Metric | Meaning |
|---|---|
| sample ratio | raw samples per resampled point. **Below 1 means the channel is upsampled and the extra points are invented.** Also the rate information, in the units that matter. |
| variance retained | `std(resampled) / std(raw)` — information lost to smoothing |
| anti-alias delta | how much the input would move if low-passed before decimating, in units of the raw std. **Measures the decision directly** |
| round-trip error | resample to 512, interpolate back to the raw timestamps, RMSE / std(raw) |

Flags: 🔴 variance retained < 0.7 or anti-alias delta > 0.2 · 🟡 upsampled (ratio < 1) · 🟢 faithful.

## ⚑ No sampling rate is estimated here

An earlier version reported a native frequency and used it to locate spectral energy above the grid's Nyquist. That was removed because the estimate is not well defined: the **mean** averages in silent stretches (25 Hz for SPN 3030 against a true 50 Hz), the **mode** depends on bin width (SPN 2979 reads 50 Hz or 1736 Hz from the same data depending on whether gaps are binned to 0.1 ms or 1 µs), and the **median**, while sound for a unimodal channel, describes only one of two cadences for a channel like SPN 5052 that sends 50 Hz bursts separated by 100 ms pauses.

The pipeline never estimates a rate — `resample_window` is `np.interp` over the raw timestamps — so a diagnostic depending on one was measuring its own estimator. Rates are computed properly, per driver, in `sampling_rate_all_drivers.md`.

## 30 s window — 17.07 Hz grid

**0 channels severely distorted · 31 upsampled · median variance retained 0.992 · median anti-alias delta 0.0367**

| Flag | SPN | Signal | Ratio | Var retained | Anti-alias Δ | Round-trip |
|---|--:|---|--:|--:|--:|--:|
| 🟡 | 908 | `The speed of the rear axle #1, right whe` | 0.58 | 0.920 | 0.1251 | 0.163 |
| 🟡 | 906 | `The speed of the front axle, right wheel` | 0.58 | 0.920 | 0.1155 | 0.152 |
| 🟡 | 905 | `The speed of the front axle, left wheel ` | 0.58 | 0.921 | 0.1143 | 0.153 |
| 🟡 | 101 | `First instance of the gage pressure insi` | 0.12 | 0.922 | 0.0212 | 0.027 |
| 🟡 | 907 | `The speed of the rear axle #1, left whee` | 0.58 | 0.926 | 0.1169 | 0.154 |
| 🟡 | 641 | `Actuator that controls the variable geom` | 0.59 | 0.969 | 0.0716 | 0.078 |
| 🟡 | 157 | `The gage pressure of fuel in the primary` | 0.12 | 0.970 | 0.0161 | 0.016 |
| 🟢 | 5052 | `Rotational velocity of the input to a tr` | 1.68 | 0.973 | 0.0815 | 0.109 |
| 🟡 | 187 | `Rotational velocity selected by operator` | 0.59 | 0.978 | 0.0401 | 0.046 |
| 🟡 | 102 | `The gage pressure measurement of the air` | 0.12 | 0.978 | 0.0114 | 0.012 |
| 🟡 | 100 | `Gage pressure of oil in engine lubricati` | 0.12 | 0.979 | 0.0124 | 0.012 |
| 🟡 | 183 | `Amount of fuel consumed by engine per un` | 0.59 | 0.980 | 0.0512 | 0.064 |
| 🟡 | 1209 | `Gage pressure of the exhaust gases as me` | 0.59 | 0.981 | 0.0537 | 0.055 |
| 🟡 | 1087 | `The pneumatic pressure in the primary se` | 0.06 | 0.983 | 0.0050 | 0.005 |
| 🟡 | 1088 | `The pneumatic pressure in the secondary ` | 0.06 | 0.983 | 0.0047 | 0.005 |
| 🟡 | 3251 | `Exhaust differential pressure measured b` | 0.12 | 0.984 | 0.0099 | 0.009 |
| 🟡 | 27 | `The position of the exhaust gas recircul` | 0.58 | 0.984 | 0.0509 | 0.055 |
| 🟡 | 1242 | `Estimate of the power developed by the e` | 0.59 | 0.985 | 0.0395 | 0.044 |
| 🟡 | 3610 | `This parameter indicates the diesel part` | 0.12 | 0.987 | 0.0093 | 0.008 |
| 🟡 | 103 | `Rotational velocity of rotor in the turb` | 0.06 | 0.988 | 0.0061 | 0.005 |
| 🟡 | 117 | `Gage pressure of air in the primary, or ` | 0.06 | 0.988 | 0.0045 | 0.004 |
| 🟡 | 184 | `Current fuel economy at current vehicle ` | 0.59 | 0.990 | 0.0456 | 0.049 |
| 🟡 | 118 | `Gage pressure of air in the secondary, o` | 0.06 | 0.991 | 0.0053 | 0.004 |
| 🟡 | 1717 | `Percent Torque - This is the maximum amo` | 0.59 | 0.991 | 0.0359 | 0.043 |
| 🟡 | 5313 | `Provides the commanded set point value f` | 0.59 | 0.991 | 0.0366 | 0.035 |
| 🟢 | 5398 | `Percent Torque - The calculated torque t` | 2.93 | 0.993 | 0.1272 | 0.160 |
| 🟢 | 514 | `Percent Torque - The calculated torque t` | 2.93 | 0.993 | 0.1135 | 0.143 |
| 🟢 | 2659 | `Flow rate of gas through the EGR system.` | 1.17 | 0.995 | 0.0583 | 0.064 |
| 🟢 | 132 | `Mass flow rate of fresh air entering the` | 1.17 | 0.996 | 0.0412 | 0.046 |
| 🟢 | 513 | `Percent Torque - The calculated output t` | 2.93 | 0.996 | 0.0696 | 0.072 |
| 🟢 | 3357 | `Percent Torque - This is the maximum amo` | 2.93 | 0.996 | 0.0989 | 0.106 |
| 🟢 | 2432 | `The requested torque output of the engin` | 2.93 | 0.996 | 0.0702 | 0.073 |
| 🟢 | 92 | `The ratio of actual engine percent torqu` | 2.93 | 0.997 | 0.0727 | 0.069 |
| 🟢 | 3226 | `The amount of combined NO and NO2 in the` | 1.16 | 0.997 | 0.0325 | 0.039 |
| 🟢 | 190 | `Actual engine speed which is calculated ` | 2.93 | 0.998 | 0.0642 | 0.061 |
| 🟡 | 2945 | `Signal from transmission control unit in` | 0.59 | 0.999 | 0.0168 | 0.018 |
| 🟡 | 904 | `The average speed of the two front wheel` | 0.58 | 0.999 | 0.0090 | 0.007 |
| 🟡 | 524 | `The gear that the transmission will atte` | 0.59 | 1.000 | 0.0224 | 0.022 |
| 🟢 | 3216 | `The amount of combined NO and NO2 in the` | 1.17 | 1.000 | 0.0168 | 0.013 |
| 🟢 | 573 | `State signal which indicates whether the` | 5.85 | 1.001 | 0.1039 | 0.119 |
| 🟡 | 526 | `Actual ratio of input shaft speed to out` | 0.59 | 1.001 | 0.0275 | 0.026 |
| 🟡 | 7319 | `This parameter is the vehicle speed that` | 0.59 | 1.001 | 0.0079 | 0.007 |
| 🟢 | 574 | `Indicates that the transmission is in pr` | 5.85 | 1.001 | 0.0414 | 0.049 |
| 🟡 | 523 | `The gear currently engaged in the transm` | 0.59 | 1.001 | 0.0261 | 0.024 |
| 🟢 | 161 | `Rotational velocity of the primary shaft` | 5.85 | 1.001 | 0.0272 | 0.022 |
| 🟢 | 4816 | `State signal indicating whether or not t` | 5.85 | 1.001 | 0.0368 | 0.038 |
| 🟡 | 84 | `Speed of the vehicle as calculated from ` | 0.59 | 1.002 | 0.0079 | 0.007 |
| 🟢 | 191 | `Calculated speed of the transmission 1 o` | 5.85 | 1.002 | 0.0230 | 0.025 |
| 🟢 | 91 | `This parameter is intended for the prima` | 2.93 | 1.006 | 0.0313 | 0.018 |
| 🟢 | 512 | `Percent Torque - The requested torque ou` | 2.93 | 1.007 | 0.0401 | 0.026 |

## 51.2 s window — 10.00 Hz grid

**0 channels severely distorted · 31 upsampled · median variance retained 0.996 · median anti-alias delta 0.0390**

| Flag | SPN | Signal | Ratio | Var retained | Anti-alias Δ | Round-trip |
|---|--:|---|--:|--:|--:|--:|
| 🟡 | 908 | `The speed of the rear axle #1, right whe` | 1.00 | 0.938 | 0.1778 | 0.225 |
| 🟡 | 907 | `The speed of the rear axle #1, left whee` | 1.00 | 0.946 | 0.1621 | 0.208 |
| 🟡 | 906 | `The speed of the front axle, right wheel` | 1.00 | 0.946 | 0.1515 | 0.191 |
| 🟡 | 905 | `The speed of the front axle, left wheel ` | 1.00 | 0.948 | 0.1481 | 0.190 |
| 🟢 | 5052 | `Rotational velocity of the input to a tr` | 2.86 | 0.951 | 0.0575 | 0.074 |
| 🟡 | 101 | `First instance of the gage pressure insi` | 0.20 | 0.958 | 0.0264 | 0.033 |
| 🟡 | 157 | `The gage pressure of fuel in the primary` | 0.20 | 0.979 | 0.0216 | 0.023 |
| 🟡 | 641 | `Actuator that controls the variable geom` | 1.00 | 0.980 | 0.0958 | 0.108 |
| 🟡 | 100 | `Gage pressure of oil in engine lubricati` | 0.20 | 0.988 | 0.0157 | 0.016 |
| 🟡 | 103 | `Rotational velocity of rotor in the turb` | 0.10 | 0.989 | 0.0085 | 0.007 |
| 🟡 | 1209 | `Gage pressure of the exhaust gases as me` | 1.00 | 0.989 | 0.0680 | 0.073 |
| 🟡 | 118 | `Gage pressure of air in the secondary, o` | 0.10 | 0.989 | 0.0066 | 0.005 |
| 🟡 | 1088 | `The pneumatic pressure in the secondary ` | 0.10 | 0.989 | 0.0061 | 0.005 |
| 🟡 | 184 | `Current fuel economy at current vehicle ` | 1.00 | 0.989 | 0.0630 | 0.075 |
| 🟡 | 187 | `Rotational velocity selected by operator` | 1.00 | 0.990 | 0.0397 | 0.045 |
| 🟡 | 102 | `The gage pressure measurement of the air` | 0.20 | 0.990 | 0.0137 | 0.011 |
| 🟡 | 1087 | `The pneumatic pressure in the primary se` | 0.10 | 0.990 | 0.0059 | 0.005 |
| 🟡 | 183 | `Amount of fuel consumed by engine per un` | 1.00 | 0.991 | 0.0566 | 0.077 |
| 🟡 | 27 | `The position of the exhaust gas recircul` | 1.00 | 0.991 | 0.0648 | 0.072 |
| 🟡 | 1242 | `Estimate of the power developed by the e` | 1.00 | 0.993 | 0.0435 | 0.052 |
| 🟡 | 3610 | `This parameter indicates the diesel part` | 0.20 | 0.993 | 0.0123 | 0.010 |
| 🟡 | 3251 | `Exhaust differential pressure measured b` | 0.20 | 0.994 | 0.0121 | 0.010 |
| 🟡 | 1717 | `Percent Torque - This is the maximum amo` | 1.00 | 0.994 | 0.0449 | 0.057 |
| 🟡 | 5313 | `Provides the commanded set point value f` | 1.00 | 0.995 | 0.0421 | 0.045 |
| 🟡 | 117 | `Gage pressure of air in the primary, or ` | 0.10 | 0.996 | 0.0056 | 0.005 |
| 🟢 | 2659 | `Flow rate of gas through the EGR system.` | 2.00 | 0.997 | 0.0713 | 0.078 |
| 🟢 | 3226 | `The amount of combined NO and NO2 in the` | 1.99 | 0.998 | 0.0443 | 0.042 |
| 🟢 | 2432 | `The requested torque output of the engin` | 5.00 | 0.998 | 0.0690 | 0.072 |
| 🟢 | 513 | `Percent Torque - The calculated output t` | 5.00 | 0.999 | 0.0698 | 0.072 |
| 🟢 | 92 | `The ratio of actual engine percent torqu` | 4.99 | 0.999 | 0.0784 | 0.080 |
| 🟢 | 190 | `Actual engine speed which is calculated ` | 5.00 | 0.999 | 0.0545 | 0.056 |
| 🟢 | 573 | `State signal which indicates whether the` | 9.99 | 0.999 | 0.1411 | 0.157 |
| 🟢 | 514 | `Percent Torque - The calculated torque t` | 4.99 | 0.999 | 0.1289 | 0.151 |
| 🟢 | 3357 | `Percent Torque - This is the maximum amo` | 4.99 | 0.999 | 0.1200 | 0.133 |
| 🟢 | 132 | `Mass flow rate of fresh air entering the` | 2.00 | 0.999 | 0.0380 | 0.042 |
| 🟢 | 5398 | `Percent Torque - The calculated torque t` | 4.99 | 1.000 | 0.1510 | 0.176 |
| 🟢 | 3216 | `The amount of combined NO and NO2 in the` | 2.00 | 1.000 | 0.0251 | 0.016 |
| 🟡 | 524 | `The gear that the transmission will atte` | 1.00 | 1.000 | 0.0276 | 0.030 |
| 🟡 | 526 | `Actual ratio of input shaft speed to out` | 1.00 | 1.000 | 0.0289 | 0.032 |
| 🟡 | 2945 | `Signal from transmission control unit in` | 1.00 | 1.000 | 0.0303 | 0.024 |
| 🟢 | 512 | `Percent Torque - The requested torque ou` | 5.00 | 1.000 | 0.0383 | 0.031 |
| 🟡 | 523 | `The gear currently engaged in the transm` | 1.00 | 1.000 | 0.0267 | 0.030 |
| 🟢 | 91 | `This parameter is intended for the prima` | 4.99 | 1.000 | 0.0350 | 0.026 |
| 🟢 | 574 | `Indicates that the transmission is in pr` | 9.99 | 1.001 | 0.0478 | 0.059 |
| 🟢 | 161 | `Rotational velocity of the primary shaft` | 9.99 | 1.001 | 0.0285 | 0.025 |
| 🟡 | 7319 | `This parameter is the vehicle speed that` | 1.00 | 1.001 | 0.0070 | 0.006 |
| 🟡 | 84 | `Speed of the vehicle as calculated from ` | 1.00 | 1.001 | 0.0071 | 0.006 |
| 🟢 | 191 | `Calculated speed of the transmission 1 o` | 9.99 | 1.001 | 0.0183 | 0.020 |
| 🟡 | 904 | `The average speed of the two front wheel` | 1.00 | 1.002 | 0.0072 | 0.006 |
| 🟢 | 4816 | `State signal indicating whether or not t` | 9.99 | 1.003 | 0.0355 | 0.049 |

## 90 s window — 5.69 Hz grid

**4 channels severely distorted · 11 upsampled · median variance retained 0.999 · median anti-alias delta 0.0513**

| Flag | SPN | Signal | Ratio | Var retained | Anti-alias Δ | Round-trip |
|---|--:|---|--:|--:|--:|--:|
| 🟢 | 5052 | `Rotational velocity of the input to a tr` | 4.77 | 0.928 | 0.0497 | 0.056 |
| 🔴 | 908 | `The speed of the rear axle #1, right whe` | 1.75 | 0.943 | 0.2475 | 0.384 |
| 🔴 | 907 | `The speed of the rear axle #1, left whee` | 1.75 | 0.947 | 0.2453 | 0.377 |
| 🔴 | 905 | `The speed of the front axle, left wheel ` | 1.75 | 0.952 | 0.2004 | 0.314 |
| 🔴 | 906 | `The speed of the front axle, right wheel` | 1.75 | 0.954 | 0.2020 | 0.316 |
| 🟡 | 101 | `First instance of the gage pressure insi` | 0.35 | 0.979 | 0.0337 | 0.043 |
| 🟡 | 157 | `The gage pressure of fuel in the primary` | 0.35 | 0.981 | 0.0355 | 0.039 |
| 🟢 | 641 | `Actuator that controls the variable geom` | 1.76 | 0.988 | 0.1343 | 0.165 |
| 🟡 | 103 | `Rotational velocity of rotor in the turb` | 0.18 | 0.992 | 0.0127 | 0.010 |
| 🟢 | 184 | `Current fuel economy at current vehicle ` | 1.76 | 0.992 | 0.0822 | 0.104 |
| 🟢 | 187 | `Rotational velocity selected by operator` | 1.76 | 0.993 | 0.0475 | 0.054 |
| 🟢 | 27 | `The position of the exhaust gas recircul` | 1.76 | 0.993 | 0.0934 | 0.107 |
| 🟡 | 100 | `Gage pressure of oil in engine lubricati` | 0.35 | 0.993 | 0.0227 | 0.022 |
| 🟡 | 102 | `The gage pressure measurement of the air` | 0.35 | 0.993 | 0.0182 | 0.015 |
| 🟢 | 183 | `Amount of fuel consumed by engine per un` | 1.76 | 0.993 | 0.0793 | 0.109 |
| 🟢 | 1209 | `Gage pressure of the exhaust gases as me` | 1.76 | 0.994 | 0.0945 | 0.109 |
| 🟢 | 1242 | `Estimate of the power developed by the e` | 1.76 | 0.995 | 0.0641 | 0.073 |
| 🟢 | 5313 | `Provides the commanded set point value f` | 1.76 | 0.996 | 0.0706 | 0.074 |
| 🟡 | 3610 | `This parameter indicates the diesel part` | 0.35 | 0.996 | 0.0170 | 0.012 |
| 🟡 | 3251 | `Exhaust differential pressure measured b` | 0.35 | 0.997 | 0.0162 | 0.012 |
| 🟢 | 3357 | `Percent Torque - This is the maximum amo` | 8.78 | 0.998 | 0.1511 | 0.170 |
| 🟢 | 2659 | `Flow rate of gas through the EGR system.` | 3.51 | 0.998 | 0.0981 | 0.102 |
| 🟢 | 1717 | `Percent Torque - This is the maximum amo` | 1.76 | 0.998 | 0.0530 | 0.066 |
| 🟢 | 3216 | `The amount of combined NO and NO2 in the` | 3.50 | 0.999 | 0.0417 | 0.021 |
| 🟢 | 513 | `Percent Torque - The calculated output t` | 8.78 | 0.999 | 0.0903 | 0.092 |
| 🟢 | 92 | `The ratio of actual engine percent torqu` | 8.78 | 0.999 | 0.1004 | 0.105 |
| 🟢 | 5398 | `Percent Torque - The calculated torque t` | 8.78 | 0.999 | 0.1709 | 0.199 |
| 🟢 | 2432 | `The requested torque output of the engin` | 8.78 | 0.999 | 0.0885 | 0.091 |
| 🟢 | 132 | `Mass flow rate of fresh air entering the` | 3.51 | 0.999 | 0.0442 | 0.044 |
| 🟢 | 190 | `Actual engine speed which is calculated ` | 8.78 | 1.000 | 0.0538 | 0.053 |
| 🟢 | 524 | `The gear that the transmission will atte` | 1.76 | 1.000 | 0.0327 | 0.038 |
| 🟢 | 512 | `Percent Torque - The requested torque ou` | 8.78 | 1.000 | 0.0576 | 0.050 |
| 🟢 | 91 | `This parameter is intended for the prima` | 8.78 | 1.000 | 0.0534 | 0.045 |
| 🟢 | 523 | `The gear currently engaged in the transm` | 1.76 | 1.000 | 0.0340 | 0.039 |
| 🟢 | 526 | `Actual ratio of input shaft speed to out` | 1.76 | 1.000 | 0.0378 | 0.044 |
| 🟢 | 161 | `Rotational velocity of the primary shaft` | 17.56 | 1.000 | 0.0305 | 0.027 |
| 🟢 | 84 | `Speed of the vehicle as calculated from ` | 1.76 | 1.001 | 0.0068 | 0.005 |
| 🟢 | 4816 | `State signal indicating whether or not t` | 17.56 | 1.001 | 0.0321 | 0.045 |
| 🟢 | 191 | `Calculated speed of the transmission 1 o` | 17.56 | 1.001 | 0.0137 | 0.016 |
| 🟢 | 904 | `The average speed of the two front wheel` | 1.75 | 1.001 | 0.0068 | 0.005 |
| 🟢 | 2945 | `Signal from transmission control unit in` | 1.76 | 1.001 | 0.0288 | 0.029 |
| 🟢 | 574 | `Indicates that the transmission is in pr` | 17.56 | 1.001 | 0.0561 | 0.068 |
| 🟢 | 7319 | `This parameter is the vehicle speed that` | 1.75 | 1.001 | 0.0068 | 0.005 |
| 🟡 | 117 | `Gage pressure of air in the primary, or ` | 0.17 | 1.002 | 0.0062 | 0.005 |
| 🟢 | 573 | `State signal which indicates whether the` | 17.56 | 1.002 | 0.1943 | 0.213 |
| 🟡 | 118 | `Gage pressure of air in the secondary, o` | 0.17 | 1.002 | 0.0054 | 0.004 |
| 🟢 | 514 | `Percent Torque - The calculated torque t` | 8.78 | 1.004 | 0.1432 | 0.165 |
| 🟢 | 3226 | `The amount of combined NO and NO2 in the` | 3.44 | 1.006 | 0.0676 | 0.046 |
| 🟡 | 1087 | `The pneumatic pressure in the primary se` | 0.17 | 1.009 | 0.0070 | 0.006 |
| 🟡 | 1088 | `The pneumatic pressure in the secondary ` | 0.17 | 1.009 | 0.0066 | 0.006 |

## 120 s window — 4.27 Hz grid

**5 channels severely distorted · 11 upsampled · median variance retained 0.999 · median anti-alias delta 0.0568**

| Flag | SPN | Signal | Ratio | Var retained | Anti-alias Δ | Round-trip |
|---|--:|---|--:|--:|--:|--:|
| 🟢 | 5052 | `Rotational velocity of the input to a tr` | 6.12 | 0.903 | 0.0471 | 0.049 |
| 🔴 | 908 | `The speed of the rear axle #1, right whe` | 2.34 | 0.935 | 0.3105 | 0.474 |
| 🔴 | 907 | `The speed of the rear axle #1, left whee` | 2.34 | 0.940 | 0.3060 | 0.465 |
| 🔴 | 906 | `The speed of the front axle, right wheel` | 2.34 | 0.952 | 0.2472 | 0.376 |
| 🔴 | 905 | `The speed of the front axle, left wheel ` | 2.34 | 0.954 | 0.2430 | 0.371 |
| 🟡 | 157 | `The gage pressure of fuel in the primary` | 0.47 | 0.983 | 0.0465 | 0.051 |
| 🟡 | 101 | `First instance of the gage pressure insi` | 0.47 | 0.985 | 0.0396 | 0.050 |
| 🟢 | 641 | `Actuator that controls the variable geom` | 2.34 | 0.986 | 0.1551 | 0.209 |
| 🟡 | 103 | `Rotational velocity of rotor in the turb` | 0.23 | 0.992 | 0.0166 | 0.012 |
| 🟢 | 184 | `Current fuel economy at current vehicle ` | 2.34 | 0.993 | 0.1017 | 0.117 |
| 🟢 | 1209 | `Gage pressure of the exhaust gases as me` | 2.34 | 0.994 | 0.1104 | 0.137 |
| 🟡 | 102 | `The gage pressure measurement of the air` | 0.47 | 0.994 | 0.0236 | 0.019 |
| 🟢 | 5313 | `Provides the commanded set point value f` | 2.34 | 0.995 | 0.0876 | 0.092 |
| 🟢 | 27 | `The position of the exhaust gas recircul` | 2.34 | 0.995 | 0.1092 | 0.123 |
| 🟡 | 100 | `Gage pressure of oil in engine lubricati` | 0.47 | 0.995 | 0.0281 | 0.027 |
| 🟢 | 183 | `Amount of fuel consumed by engine per un` | 2.34 | 0.995 | 0.0862 | 0.117 |
| 🟢 | 1242 | `Estimate of the power developed by the e` | 2.34 | 0.996 | 0.0711 | 0.081 |
| 🟢 | 187 | `Rotational velocity selected by operator` | 2.34 | 0.996 | 0.0467 | 0.049 |
| 🟡 | 3610 | `This parameter indicates the diesel part` | 0.47 | 0.996 | 0.0239 | 0.016 |
| 🟢 | 5398 | `Percent Torque - The calculated torque t` | 11.71 | 0.997 | 0.1830 | 0.220 |
| 🟢 | 3357 | `Percent Torque - This is the maximum amo` | 11.71 | 0.998 | 0.1637 | 0.188 |
| 🟡 | 3251 | `Exhaust differential pressure measured b` | 0.47 | 0.998 | 0.0211 | 0.016 |
| 🟢 | 1717 | `Percent Torque - This is the maximum amo` | 2.34 | 0.999 | 0.0632 | 0.079 |
| 🟢 | 92 | `The ratio of actual engine percent torqu` | 11.71 | 0.999 | 0.1053 | 0.111 |
| 🟢 | 2432 | `The requested torque output of the engin` | 11.70 | 0.999 | 0.0931 | 0.095 |
| 🟢 | 513 | `Percent Torque - The calculated output t` | 11.70 | 0.999 | 0.0957 | 0.098 |
| 🟢 | 2659 | `Flow rate of gas through the EGR system.` | 4.68 | 0.999 | 0.1102 | 0.114 |
| 🟢 | 514 | `Percent Torque - The calculated torque t` | 11.71 | 1.000 | 0.1529 | 0.178 |
| 🟢 | 3216 | `The amount of combined NO and NO2 in the` | 4.64 | 1.000 | 0.0538 | 0.028 |
| 🟢 | 523 | `The gear currently engaged in the transm` | 2.34 | 1.000 | 0.0359 | 0.042 |
| 🟢 | 526 | `Actual ratio of input shaft speed to out` | 2.34 | 1.000 | 0.0414 | 0.049 |
| 🟢 | 3226 | `The amount of combined NO and NO2 in the` | 4.66 | 1.000 | 0.0814 | 0.059 |
| 🟢 | 132 | `Mass flow rate of fresh air entering the` | 4.68 | 1.000 | 0.0486 | 0.047 |
| 🟢 | 524 | `The gear that the transmission will atte` | 2.34 | 1.000 | 0.0358 | 0.042 |
| 🔴 | 573 | `State signal which indicates whether the` | 23.42 | 1.000 | 0.2252 | 0.245 |
| 🟢 | 190 | `Actual engine speed which is calculated ` | 11.70 | 1.000 | 0.0545 | 0.051 |
| 🟢 | 91 | `This parameter is intended for the prima` | 11.71 | 1.000 | 0.0644 | 0.058 |
| 🟢 | 904 | `The average speed of the two front wheel` | 2.34 | 1.000 | 0.0085 | 0.006 |
| 🟢 | 191 | `Calculated speed of the transmission 1 o` | 23.42 | 1.000 | 0.0157 | 0.018 |
| 🟢 | 7319 | `This parameter is the vehicle speed that` | 2.34 | 1.001 | 0.0084 | 0.006 |
| 🟢 | 161 | `Rotational velocity of the primary shaft` | 23.42 | 1.001 | 0.0328 | 0.027 |
| 🟢 | 512 | `Percent Torque - The requested torque ou` | 11.70 | 1.001 | 0.0685 | 0.064 |
| 🟢 | 84 | `Speed of the vehicle as calculated from ` | 2.34 | 1.001 | 0.0084 | 0.006 |
| 🟢 | 574 | `Indicates that the transmission is in pr` | 23.42 | 1.001 | 0.0604 | 0.070 |
| 🟢 | 2945 | `Signal from transmission control unit in` | 2.34 | 1.002 | 0.0417 | 0.042 |
| 🟡 | 1087 | `The pneumatic pressure in the primary se` | 0.23 | 1.002 | 0.0076 | 0.007 |
| 🟢 | 4816 | `State signal indicating whether or not t` | 23.42 | 1.003 | 0.0590 | 0.049 |
| 🟡 | 117 | `Gage pressure of air in the primary, or ` | 0.23 | 1.003 | 0.0062 | 0.005 |
| 🟡 | 1088 | `The pneumatic pressure in the secondary ` | 0.23 | 1.003 | 0.0078 | 0.007 |
| 🟡 | 118 | `Gage pressure of air in the secondary, o` | 0.23 | 1.004 | 0.0068 | 0.005 |

## Spread across drivers

Distortion should be a property of a channel's sampling against the grid, not of who was driving. The largest across-driver standard deviation in variance retained is **0.0525** (median 0.0042). A large value would mean the measurement depends on the driver and needs all 46.

