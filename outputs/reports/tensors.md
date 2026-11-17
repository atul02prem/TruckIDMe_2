# Arm B window tensors

**50 channels** x **4 window lengths**, built from `data/processed_data/` by `build_tensors.py`.

`RESIZE_STEPS = 512` is fixed, so window length sets the grid rate.

| Window | Grid | Shape | Windows | Drivers | Per driver (min/med/max) | Size | Built in |
|--:|--:|---|--:|--:|---|--:|--:|
| 30s | 17.07 Hz | `(3876, 50, 512)` | 3876 | 46 | 59/83.5/111 | 186 MB | 113s |
| 51.2s | 10.00 Hz | `(2267, 50, 512)` | 2267 | 46 | 35/49/65 | 112 MB | 93s |
| 90s | 5.69 Hz | `(1290, 50, 512)` | 1290 | 46 | 19/28/37 | 65 MB | 81s |
| 120s | 4.27 Hz | `(964, 50, 512)` | 964 | 46 | 15/21/28 | 50 MB | 78s |

## Channels

Stacked in this order, saved in each `.npz` under `channels`: 27, 84, 91, 92, 100, 101, 102, 103, 117, 118, 132, 157, 161, 183, 184, 187, 190, 191, 512, 513, 514, 523, 524, 526, 573, 574, 641, 904, 905, 906, 907, 908, 1087, 1088, 1209, 1242, 1717, 2432, 2659, 2945, 3216, 3226, 3251, 3357, 3610, 4816, 5052, 5313, 5398, 7319

## Excluded before this step

12 SPNs beyond the 40 that `data/processed_data/` had already dropped: 51, 515, 2978, 2979, 3030, 3229, 3230, 3231, 3232, 3239, 4154, 5015 — S1's nine plus S3's three data-quality drops (51, 3030, 2979). The tensor is built at the final channel count, so it is the model input with no later subsetting step that could fall out of step with DECISIONS.md.

