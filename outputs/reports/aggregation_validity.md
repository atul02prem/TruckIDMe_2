# Aggregation validity — what linear interpolation does to step signals

Measured over **8 drivers**, 120s windows, on the **13 step channels** among the 62 audited channels fed to the models. Windows are built exactly as `build_windows.build_driver_windows` builds them, and the resampling is `build_windows.resample_window` itself, imported — this measures the shipping code, not a reimplementation.

**Legal values** are the values each signal was observed to take anywhere in this dataset. A resampled point is counted illegal when it matches none of them: a state the vehicle was never in.

Signal types and legal value sets are decided **once, pooled over all drivers measured** — not per driver. The pipeline builds one tensor with one type per channel, so a type must be a property of the channel. Deriving it per driver let SPN 515 (constant for some drivers, 800 distinct values pooled) appear as a step channel.

## 🔴 Violations — 1 of 13 step channels receive fabricated states

| Flag | SPN | Signal | Legal values | Mean illegal | Worst window | Windows affected |
|---|--:|---|--:|--:|--:|--:|
| 🔴 | 2979 | `2979 Vehicle Acceleration Rate Limit Status` | 3 | 40.2% | 50.4% | 100.0% |

Every percentage above is a share of the 512 numbers per window that the encoder reads as a vehicle state which never existed.

## All step channels

| Flag | SPN | Signal | Legal values | Windows | Mean illegal | Transitions/window | Time in modal state |
|---|--:|---|--:|--:|--:|--:|--:|
| 🔴 | 2979 | `2979 Vehicle Acceleration Rate Limit Status` | 3 | 184 | 40.2% | 4793.04 | 70.4% |
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | 184 | 0.6% | 7.61 | 53.7% |
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | 184 | 0.6% | 7.55 | 53.8% |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 184 | 0.1% | 14.85 | 91.8% |
| 🟢 | 574 | `574 Transmission Shift In Process` | 2 | 184 | 0.0% | 2.57 | 74.2% |
| 🟢 | 2945 | `2945 Active Shift Console Indicator` | 2 | 184 | 0.0% | 0.08 | 98.7% |
| 🟢 | 3229 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | 3 | 184 | 0.0% | 0.07 | 98.7% |
| 🟢 | 3230 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | 3 | 184 | 0.0% | 0.05 | 98.6% |
| 🟢 | 3232 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 4 | 184 | 0.0% | 0.08 | 98.4% |
| 🟢 | 3231 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | 2 | 184 | 0.0% | 0.03 | 99.1% |
| 🟢 | 3239 | `3239 Aftertreatment 2 Intake Dew Point` | 2 | 184 | 0.0% | 0.03 | 99.1% |
| 🟢 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 184 | 0.0% | 0.08 | 98.6% |
| 🟢 | 5015 | `5015 Momentary Engine Maximum Power Enable` | 1 | 184 | 0.0% | 0.00 | 100.0% |

## What the correct features would be

The last two columns are the information interpolation and averaging destroy. A step signal's behaviour is *when and how often it changed*, not its level:

- **12 of 13 step channels actually change state** within a window. For those, `transitions/window` is a direct behavioural measure — how often this driver shifted, or engaged torque-converter lockup — and it survives no averaging.
- `time in modal state` is the complementary measure: a driver who holds one gear differs from one who hunts between two, even with the same mean.

Correct handling per the taxonomy in `signal_classification.md`: repeat the previous value (ZOH) rather than interpolate, and summarise a window by transition count, time-in-state fractions and mode — never a mean.

## Caveat

Window counts here may differ slightly from the full pipeline build. `build_driver_windows` drops a window when *any* of the 62 channels has fewer than 10 native samples in it, whereas this script evaluates each step channel independently. That affects how many windows are counted, not the per-window illegal fraction being measured.
