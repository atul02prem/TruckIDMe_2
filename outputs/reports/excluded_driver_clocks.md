# Excluded-driver clock degradation — which clock failed?

G1S10/G1S11/G1S12 were excluded because `canloggerTime` defaulted to 2022-05-01. Question: did the CAN signal clocks (`TimeXXX`) degrade too, or is the corruption isolated to the Teensy-written `canloggerTime`?

## Verdict
- Corruption isolated to `canloggerTime`: **CONFIRMED**.
  - canloggerTime = 2022 for all excluded: True
  - gpsTime = 2024 (correct): True
  - every CAN TimeXXX = 2024 (correct): True

Two devices, two clocks: the **CANLogger** (stamps `TimeXXX`) kept correct time; only the **Teensy/SparkFun** logger (`canloggerTime`) fell back to its uninitialised RTC. The CAN behaviour data is therefore intact and could be salvaged by re-keying alignment on `TimeXXX`/`gpsTime`.

## Per-driver clock date ranges

| Driver | canloggerTime | gpsTime | CAN TimeXXX dates | # CAN cols |
|---|---|---|---|---:|
| G1_Subject10 | 2022-05-01 .. 2022-05-01 | 2024-06-07 .. 2024-06-07 | 2024-06-07 | 102 |
| G1_Subject11 | 2022-05-01 .. 2022-05-01 | 2024-06-07 .. 2024-06-07 | 2024-06-07 | 102 |
| G1_Subject12 | 2022-05-01 .. 2022-05-01 | 2024-06-08 .. 2024-06-08 | 2024-06-08 | 102 |
| G1_Subject1 (reference, good) | 2024-04-28 .. 2024-04-28 | 2024-04-28 .. 2024-04-28 | 2024-04-28 | 102 |
