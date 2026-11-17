# Tensor verification — do the built artefacts match their source?

`verify_resampling_distortion.py` measures the resampling *operation*. This reads the saved `.npz` files and checks that they contain it — catching faults in windowing, channel ordering or the write itself, which measuring a parallel re-derivation cannot see.

## 🟢 30 s window

| Check | Result | Detail |
|---|:-:|---|
| channel order exact | 🟢 | 50 channels |
| no excluded SPN present | 🟢 | none |
| all finite | 🟢 | 0 non-finite values |
| shape is (n, channels, steps) | 🟢 | (3876, 50, 512) |
| all usable drivers present | 🟢 | 46 drivers |
| every driver has a window | 🟢 | min 59, median 83.5, max 111 windows per driver |
| exact match vs raw | 🟢 | 45 comparisons, 0 mismatched, worst absolute difference 0.00e+00 |

## 🟢 51.2 s window

| Check | Result | Detail |
|---|:-:|---|
| channel order exact | 🟢 | 50 channels |
| no excluded SPN present | 🟢 | none |
| all finite | 🟢 | 0 non-finite values |
| shape is (n, channels, steps) | 🟢 | (2267, 50, 512) |
| all usable drivers present | 🟢 | 46 drivers |
| every driver has a window | 🟢 | min 35, median 49, max 65 windows per driver |
| exact match vs raw | 🟢 | 45 comparisons, 0 mismatched, worst absolute difference 0.00e+00 |

## 🟢 90 s window

| Check | Result | Detail |
|---|:-:|---|
| channel order exact | 🟢 | 50 channels |
| no excluded SPN present | 🟢 | none |
| all finite | 🟢 | 0 non-finite values |
| shape is (n, channels, steps) | 🟢 | (1290, 50, 512) |
| all usable drivers present | 🟢 | 46 drivers |
| every driver has a window | 🟢 | min 19, median 28, max 37 windows per driver |
| exact match vs raw | 🟢 | 45 comparisons, 0 mismatched, worst absolute difference 0.00e+00 |

## 🟢 120 s window

| Check | Result | Detail |
|---|:-:|---|
| channel order exact | 🟢 | 50 channels |
| no excluded SPN present | 🟢 | none |
| all finite | 🟢 | 0 non-finite values |
| shape is (n, channels, steps) | 🟢 | (964, 50, 512) |
| all usable drivers present | 🟢 | 46 drivers |
| every driver has a window | 🟢 | min 15, median 21, max 28 windows per driver |
| exact match vs raw | 🟢 | 45 comparisons, 0 mismatched, worst absolute difference 0.00e+00 |

## On the exact-match check

The comparison recomputes `resample_window` on the raw samples inside each sampled window and requires **bit-identical** agreement with the stored column — not agreement within a tolerance. Both paths call the same function on the same inputs, so any non-zero difference is a windowing or indexing fault rather than numerical drift, and a tolerance would hide exactly the bug this check exists to find.

