# Aggregation validity — step signals in the 50-channel model input

> Supersedes `aggregation_validity.md` for the model input. That report measured the earlier 62-channel set at 120 s on 8 drivers, and remains the evidence for excluding SPN 2979.

**50 channels** x **4 window lengths**, all **46 drivers**, resampled with `np.interp` exactly as `build_windows.resample_window` does.

Signal types among the model's channels, pooled over all drivers: **continuous 44**, **step 6**, **event 0**. Only step channels can receive an illegal value; a continuous channel has no forbidden values between its samples.

A resampled point is **illegal** when it matches no value the signal takes anywhere in the dataset — a state the vehicle was never in.

Flags: 🔴 mean illegal ≥ 10% · 🟡 ≥ 1% · 🟢 below 1%.

## 🟢 No violations

No step channel exceeds 1% illegal values at any window length.

## Mean illegal share, by window length

| SPN | Signal | 30 s | 51.2 s | 90 s | 120 s |
|--:|---|--:|--:|--:|--:|
| 524 | `524 Transmission Selected Gear` | 🟢 0.64% | 🟢 0.64% | 🟢 0.64% | 🟢 0.64% |
| 523 | `523 Transmission Current Gear` | 🟢 0.62% | 🟢 0.63% | 🟢 0.63% | 🟢 0.65% |
| 573 | `573 Transmission Torque Converter Lockup Engaged` | 🟢 0.13% | 🟢 0.13% | 🟢 0.13% | 🟢 0.13% |
| 574 | `574 Transmission Shift In Process` | 🟢 0.02% | 🟢 0.02% | 🟢 0.02% | 🟢 0.02% |
| 2945 | `2945 Active Shift Console Indicator` | 🟢 0.01% | 🟢 0.01% | 🟢 0.01% | 🟢 0.01% |
| 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 🟢 0.00% | 🟢 0.00% | 🟢 0.00% | 🟢 0.00% |

## 30 s window

| Flag | SPN | Signal | Legal values | Windows | Mean illegal | Worst window | Windows affected | Transitions/window | Time in modal state |
|---|--:|---|--:|--:|--:|--:|--:|--:|--:|
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | 4292 | 0.64% | 2.9% | 75.8% | 1.89 | 70.8% |
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | 4292 | 0.62% | 2.7% | 75.9% | 1.88 | 71.0% |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 4292 | 0.13% | 1.2% | 45.0% | 3.71 | 91.8% |
| 🟢 | 574 | `574 Transmission Shift In Process` | 2 | 4292 | 0.02% | 0.6% | 11.0% | 0.66 | 86.2% |
| 🟢 | 2945 | `2945 Active Shift Console Indicator` | 2 | 4292 | 0.01% | 11.9% | 2.0% | 0.02 | 99.5% |
| 🟢 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 4292 | 0.00% | 0.2% | 0.3% | 0.02 | 99.5% |

## 51.2 s window

| Flag | SPN | Signal | Legal values | Windows | Mean illegal | Worst window | Windows affected | Transitions/window | Time in modal state |
|---|--:|---|--:|--:|--:|--:|--:|--:|--:|
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | 2503 | 0.64% | 3.1% | 88.1% | 3.23 | 63.1% |
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | 2503 | 0.63% | 2.7% | 88.2% | 3.22 | 63.1% |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 2503 | 0.13% | 1.0% | 45.7% | 6.35 | 91.8% |
| 🟢 | 574 | `574 Transmission Shift In Process` | 2 | 2503 | 0.02% | 0.4% | 11.3% | 1.13 | 80.9% |
| 🟢 | 2945 | `2945 Active Shift Console Indicator` | 2 | 2503 | 0.01% | 7.0% | 2.9% | 0.04 | 99.2% |
| 🟢 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 2503 | 0.00% | 0.2% | 0.4% | 0.04 | 99.2% |

## 90 s window

| Flag | SPN | Signal | Legal values | Windows | Mean illegal | Worst window | Windows affected | Transitions/window | Time in modal state |
|---|--:|---|--:|--:|--:|--:|--:|--:|--:|
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | 1418 | 0.64% | 2.3% | 92.5% | 5.69 | 55.8% |
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | 1418 | 0.63% | 2.1% | 92.5% | 5.66 | 55.8% |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 1418 | 0.13% | 1.0% | 48.2% | 11.15 | 91.8% |
| 🟢 | 574 | `574 Transmission Shift In Process` | 2 | 1418 | 0.02% | 0.6% | 11.4% | 1.98 | 75.6% |
| 🟢 | 2945 | `2945 Active Shift Console Indicator` | 2 | 1418 | 0.01% | 4.1% | 3.1% | 0.07 | 98.9% |
| 🟢 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 1418 | 0.00% | 0.2% | 0.5% | 0.06 | 98.9% |

## 120 s window

| Flag | SPN | Signal | Legal values | Windows | Mean illegal | Worst window | Windows affected | Transitions/window | Time in modal state |
|---|--:|---|--:|--:|--:|--:|--:|--:|--:|
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | 1056 | 0.65% | 2.3% | 93.8% | 7.54 | 52.5% |
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | 1056 | 0.64% | 2.1% | 94.1% | 7.58 | 52.5% |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 1056 | 0.13% | 1.0% | 46.5% | 14.85 | 91.8% |
| 🟢 | 574 | `574 Transmission Shift In Process` | 2 | 1056 | 0.02% | 0.4% | 10.5% | 2.64 | 73.2% |
| 🟢 | 2945 | `2945 Active Shift Console Indicator` | 2 | 1056 | 0.01% | 3.1% | 3.9% | 0.09 | 98.8% |
| 🟢 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 1056 | 0.00% | 0.2% | 0.7% | 0.09 | 98.8% |

## Limitations

- Illegal share measures one failure only: values between two states. It does not measure the transition being smeared in time, which interpolation also does.
- Window counts can differ slightly from the tensors: the pipeline drops a window when *any* channel is too sparse, while this script judges each step channel on its own. The per-window share is unaffected.
- Continuous channels are measured separately, in `resampling_distortion.md`.
