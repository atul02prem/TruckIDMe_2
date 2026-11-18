# exp05 — context length vs temporal resolution

Mantis takes **512 points regardless of window length**, so context and resolution cannot be increased together. 46-way closed set, chance 2.2%, frozen encoder, audited 50 channels, per-driver chronological 70/5/25 split. Only the window length changes.

| Window | Effective rate | Windows | train / test | linear probe | LDA + centroid | random forest |
|---|--:|--:|--:|--:|--:|--:|
| 30 s | 17.07 Hz | 3,876 | 2,691 / 983 | 22.9% | 20.3% | 15.0% |
| 51.2 s | 10.00 Hz | 2,267 | 1,567 / 585 | 24.6% | 23.2% | 19.1% |
| 90 s | 5.69 Hz | 1,290 | 878 / 336 | 22.6% | 25.0% | 14.6% |
| 120 s | 4.27 Hz | 964 | 654 / 256 | 21.9% | 27.7% | 20.3% |

Best: **120 s** at 27.7%.

## Why this is an axis, not a hyperparameter

- **51.2 s is the only length whose grid matches a native rate.** 512 / 51.2 = 10.00 Hz exactly, the modal rate across the audited 50 channels (20 of 50 are natively 10 Hz). Every other length resamples every channel to a rate nothing was recorded at.
- **At 120 s the grid is 4.27 Hz**, below the native rate of 39 of the 50 channels; the 100 Hz channels are downsampled 23x. Whatever accuracy is gained there is gained *despite* discarding most of the temporal detail.
- **Window count moves too.** Longer windows mean fewer training examples, and Stage 1 of exp04 established that training-set size is the binding constraint. So the trade is really three-way: context, resolution, and sample count.

## Figure

- `/home/ap9107/TruckIDMe/outputs/figures/exp05_window_sweep.png`

## Limitations

- **Single split per length, no error bars.**
- Resampling is linear interpolation onto a uniform grid (`np.interp`), not bin averaging, so upsampled slow channels carry interpolated rather than observed values.
- Frozen encoder only; one drive per driver. See `DECISIONS.md` C1.
