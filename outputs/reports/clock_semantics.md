# Clock semantics verification

Claim: `gpsTime` = satellite **UTC**; `canloggerTime` = CAN-logger **local** (MDT, UTC-6); CAN `TimeXXX` share the local reference. Use `gpsTime` to validate, `canloggerTime` to align.

Computed over the **46 usable drivers**; the 3 excluded drivers present in the data are reported separately below as a contrast, since a clock already known to be broken cannot test the claim.

`EXCLUDE_DRIVERS` names 4 drivers, of which 1 never appears in the data at all: G1S04 (excluded upstream by ORNL for a low CAN sampling rate, so there is no file to analyse). 46 + 3 = 49 driver files on disk.

## Verdict
- gpsTime − canloggerTime = 6.00 h for all drivers: **PASS** (mean 6.0028 h, range 5.9996-6.0236). A whole-hour timezone offset → the clocks are in different frames.
- canloggerTime decodes to daytime (local): **PASS** (hours 8-18). → canloggerTime is the local wall clock; gpsTime (6 h later) is UTC.
- CAN TimeXXX aligns with canloggerTime, not gpsTime: **PASS** (max |offset| 0.10 s). → CAN timestamps are local; align on canloggerTime.

## Findings

**1. The offset is a time zone, not drift.** It sits at 6.0028 h across every usable driver — within 85 s of a whole six hours. Random clock error does not land on an exact hour boundary 46 times; a time-zone difference does. MDT is UTC−6, and every drive falls in the Apr–Sep 2024 daylight-saving window.

**2. Decoding each clock naively settles which is which.** Read as UTC, `canloggerTime` gives local wall-clock hours 8–18 — Colorado daytime, when the drives actually happened. `gpsTime` read the same way lands six hours later, which would place these drives in the evening and night. So `canloggerTime` carries local time and `gpsTime` carries UTC, not the reverse.

**3. The CAN timestamps follow the logger, not the satellites.** Each driver's CAN stream starts within 0.10 s of `canloggerTime` (tolerance 10 s), and therefore ~6 h away from `gpsTime`. This is the decisive check: it means the CAN `TimeXXX` columns and `canloggerTime` share one reference frame, so aligning CAN signals on `canloggerTime` needs no conversion at all.

**4. Within-drive stability, corroborated independently.** The offset's standard deviation is 0.023–0.045 s, so the frames differ by a fixed shift rather than sliding apart during the drive. The spread *between* drivers is 85 s of per-logger set-up error — which `canlogger_bridge_report.md` measures separately at 86 s by a different computation. Two scripts agreeing on that figure is what makes the constant-bias reading credible.

## Decision reached from this QC

**`gpsTime` validates, `canloggerTime` aligns.** The two clocks are in different frames, so they are not interchangeable: `gpsTime` is the only independent reference available (the vehicle cannot influence the satellites), which makes it the right instrument for *checking* the logger; and `canloggerTime` shares its frame with the CAN timestamps, which makes it the right axis for *aligning* data.

The corollary matters as much: **never validate one Teensy timestamp against another from the same device.** Both would carry the same fault, so agreement would prove nothing — exactly the trap the excluded drivers below fell into.

## Contrast — the excluded drivers

These are left out of the verdict above. They show what a broken clock looks like against the same three tests, which is why the claim needed an independent reference in the first place.

| Driver | Reason excluded | gps−clg (h) | canloggerTime (local) | gpsTime (UTC) |
|---|---|---:|---|---|
| G1S10 | canloggerTime stuck at the Teensy RTC default | 18,439.54 | 2022-05-01 09:10 | 2024-06-07 16:42 |
| G1S11 | canloggerTime stuck at the Teensy RTC default | 18,443.82 | 2022-05-01 08:27 | 2024-06-07 20:17 |
| G1S12 | canloggerTime stuck at the Teensy RTC default | 18,467.90 | 2022-05-01 08:34 | 2024-06-08 20:28 |

3 of the 3 excluded drivers show an offset nowhere near 6 h — up to **18,468 h** (2.1 years) for G1S12, whose `canloggerTime` never left its factory default. Any driver left in the cohort with a clock like this would have corrupted every downstream alignment silently.

## Per-driver (usable cohort)

| Driver | gps−clg (h) | offset std (s) | \|clg−CANtime\| (s) | canloggerTime (local) | gpsTime (UTC) |
|---|---:|---:|---:|---|---|
| G1S01 | 6.0021 | 0.028 | 0.07 | 2024-04-28 11:12 | 2024-04-28 17:12 |
| G1S13 | 5.9996 | 0.039 | 0.02 | 2024-07-09 13:14 | 2024-07-09 19:14 |
| G1S14 | 6.0014 | 0.035 | 0.09 | 2024-07-12 13:15 | 2024-07-12 19:15 |
| G1S15 | 6.0033 | 0.044 | 0.04 | 2024-08-07 13:54 | 2024-08-07 19:54 |
| G1S16 | 6.0236 | 0.034 | 0.02 | 2024-08-08 14:39 | 2024-08-08 20:40 |
| G1S17 | 6.0010 | 0.034 | 0.07 | 2024-08-27 10:07 | 2024-08-27 16:07 |
| G1S02 | 6.0018 | 0.030 | 0.03 | 2024-05-09 13:26 | 2024-05-09 19:26 |
| G1S03 | 6.0031 | 0.029 | 0.01 | 2024-05-09 17:48 | 2024-05-09 23:48 |
| G1S05 | 6.0023 | 0.028 | 0.03 | 2024-05-16 12:06 | 2024-05-16 18:06 |
| G1S06 | 6.0020 | 0.023 | 0.02 | 2024-05-20 10:28 | 2024-05-20 16:29 |
| G1S07 | 6.0023 | 0.028 | 0.02 | 2024-05-21 08:28 | 2024-05-21 14:28 |
| G1S08 | 6.0026 | 0.028 | 0.06 | 2024-05-23 10:45 | 2024-05-23 16:46 |
| G1S09 | 6.0020 | 0.027 | 0.00 | 2024-05-24 09:40 | 2024-05-24 15:40 |
| G2S01 | 6.0022 | 0.026 | 0.01 | 2024-05-16 14:00 | 2024-05-16 20:00 |
| G2S10 | 6.0034 | 0.033 | 0.01 | 2024-07-25 11:50 | 2024-07-25 17:50 |
| G2S11 | 6.0015 | 0.028 | 0.04 | 2024-07-25 15:20 | 2024-07-25 21:20 |
| G2S12 | 6.0011 | 0.033 | 0.08 | 2024-08-05 09:11 | 2024-08-05 15:11 |
| G2S13 | 6.0015 | 0.037 | 0.05 | 2024-08-12 12:32 | 2024-08-12 18:32 |
| G2S14 | 6.0025 | 0.036 | 0.01 | 2024-08-14 10:02 | 2024-08-14 16:02 |
| G2S15 | 6.0020 | 0.041 | 0.02 | 2024-08-14 15:03 | 2024-08-14 21:04 |
| G2S16 | 6.0043 | 0.032 | 0.01 | 2024-08-15 13:44 | 2024-08-15 19:44 |
| G2S02 | 6.0036 | 0.037 | 0.00 | 2024-07-16 16:07 | 2024-07-16 22:08 |
| G2S03 | 6.0024 | 0.033 | 0.06 | 2024-07-17 10:09 | 2024-07-17 16:09 |
| G2S04 | 6.0024 | 0.044 | 0.08 | 2024-07-17 18:05 | 2024-07-18 00:05 |
| G2S05 | 6.0019 | 0.034 | 0.00 | 2024-07-18 10:36 | 2024-07-18 16:36 |
| G2S06 | 6.0087 | 0.036 | 0.04 | 2024-07-19 09:52 | 2024-07-19 15:52 |
| G2S07 | 6.0011 | 0.045 | 0.03 | 2024-07-23 09:44 | 2024-07-23 15:44 |
| G2S08 | 6.0020 | 0.042 | 0.05 | 2024-07-23 13:21 | 2024-07-23 19:21 |
| G2S09 | 6.0020 | 0.034 | 0.01 | 2024-07-24 08:53 | 2024-07-24 14:53 |
| G3S01 | 6.0013 | 0.043 | 0.02 | 2024-07-26 15:31 | 2024-07-26 21:31 |
| G3S10 | 6.0019 | 0.035 | 0.02 | 2024-08-21 10:27 | 2024-08-21 16:27 |
| G3S11 | 6.0012 | 0.037 | 0.10 | 2024-08-21 13:18 | 2024-08-21 19:18 |
| G3S12 | 6.0020 | 0.038 | 0.00 | 2024-08-22 16:54 | 2024-08-22 22:54 |
| G3S13 | 6.0019 | 0.038 | 0.08 | 2024-08-23 11:08 | 2024-08-23 17:08 |
| G3S14 | 6.0020 | 0.035 | 0.00 | 2024-08-28 10:24 | 2024-08-28 16:24 |
| G3S15 | 6.0015 | 0.041 | 0.06 | 2024-08-29 09:29 | 2024-08-29 15:29 |
| G3S16 | 6.0028 | 0.034 | 0.01 | 2024-08-29 13:26 | 2024-08-29 19:27 |
| G3S17 | 6.0012 | 0.039 | 0.01 | 2024-09-03 13:47 | 2024-09-03 19:47 |
| G3S02 | 6.0051 | 0.044 | 0.10 | 2024-07-29 10:58 | 2024-07-29 16:58 |
| G3S03 | 6.0013 | 0.032 | 0.02 | 2024-07-29 13:30 | 2024-07-29 19:30 |
| G3S04 | 6.0015 | 0.038 | 0.01 | 2024-07-31 11:12 | 2024-07-31 17:12 |
| G3S05 | 6.0010 | 0.037 | 0.00 | 2024-08-02 10:00 | 2024-08-02 16:00 |
| G3S06 | 6.0013 | 0.040 | 0.04 | 2024-08-06 10:16 | 2024-08-06 16:16 |
| G3S07 | 6.0025 | 0.034 | 0.00 | 2024-08-16 09:34 | 2024-08-16 15:34 |
| G3S08 | 6.0076 | 0.042 | 0.03 | 2024-08-19 11:15 | 2024-08-19 17:16 |
| G3S09 | 6.0025 | 0.034 | 0.05 | 2024-08-20 16:14 | 2024-08-20 22:14 |
