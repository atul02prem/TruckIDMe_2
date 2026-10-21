# Excluded-driver clock degradation — which clock failed?

G1S10/G1S11/G1S12 were excluded because `canloggerTime` defaulted to 2022-05-01. Question: did the CAN signal clocks (`TimeXXX`) degrade too, or is the corruption isolated to the Teensy-written `canloggerTime`?

## What is measured

Three clock families are read straight from the raw CSVs and their date ranges compared. They come from **two physically separate devices**, which is what makes the comparison informative:

| Clock | Written by | Role |
|---|---|---|
| `canloggerTime` | Teensy / SparkFun logger | the master alignment clock |
| `TimeXXX` (102 columns) | CANLogger | one timestamp per CAN signal |
| `gpsTime` | GPS satellites | independent reference the vehicle cannot influence |

## Verdict
- Corruption isolated to `canloggerTime`: **CONFIRMED**.
  - canloggerTime = 2022 for all excluded: True
  - gpsTime = 2024 (correct): True
  - every CAN TimeXXX = 2024 (correct): True

## Findings

**1. Two devices, two clocks — and only one failed.** The CANLogger kept correct time on all 102 `TimeXXX` columns; only the Teensy's `canloggerTime` is wrong. A single clock failing while another device in the same vehicle stays correct localises the fault to the device, not the drive.

**2. A default value, not drift.** All three drivers stamp the *identical* date, `2022-05-01` (verified: same value for every excluded driver). Drifting clocks diverge; they do not agree. An identical wrong date across three separate sessions is the signature of an **uninitialised RTC falling back to its factory default** — the Teensy never received a satellite time sync at boot.

**3. The behaviour data is intact.** `gpsTime` and every CAN timestamp read the true 2024 drive dates, so the CAN signals themselves — pedal, speed, torque — are undamaged. What is lost is the *bridge* between the CAN clock and GPS, not the measurements.

## Decision reached from this QC

**These three drivers are excluded, leaving 46 usable — but the exclusion is a bridge failure, not a data failure.** Since `canloggerTime` is the master alignment clock (see the canlogger-bridge report), losing it makes a driver unusable *by the current pipeline*. It does not make the driver's data bad.

**Deferred, not closed:** re-keying alignment on `TimeXXX`/`gpsTime` and de-duplicating the doubled GPS rows would restore these three, taking the cohort from **46 to 49 drivers** — about 6.5% more data. Worth doing only after the main pipeline is settled, since it needs a second alignment path that would itself have to be verified.

## Per-driver clock date ranges

| Driver | canloggerTime | gpsTime | CAN TimeXXX dates | # CAN cols |
|---|---|---|---|---:|
| G1_Subject10 | 2022-05-01 .. 2022-05-01 | 2024-06-07 .. 2024-06-07 | 2024-06-07 | 102 |
| G1_Subject11 | 2022-05-01 .. 2022-05-01 | 2024-06-07 .. 2024-06-07 | 2024-06-07 | 102 |
| G1_Subject12 | 2022-05-01 .. 2022-05-01 | 2024-06-08 .. 2024-06-08 | 2024-06-08 | 102 |
| G1_Subject1 (reference, good) | 2024-04-28 .. 2024-04-28 | 2024-04-28 .. 2024-04-28 | 2024-04-28 | 102 |
