# Window tensor — 120s windows, 62 channels

Built from `data/processed_data/` at native rates, resampled to 512 steps per window.

- drivers: **46**
- windows: **964**
- mean windows/driver: **21.0**
- tensor: `(964, 62, 512)` float32 (channel-first, as the encoder expects)

## Violations

| Flag | Driver | Windows |
|---|---|---|
| 🔴 | G1S01 | 19 |
| 🔴 | G1S03 | 18 |
| 🔴 | G1S06 | 15 |
| 🔴 | G1S07 | 16 |
| 🔴 | G1S09 | 17 |
| 🔴 | G1S14 | 19 |
| 🔴 | G2S05 | 18 |
| 🔴 | G2S09 | 18 |
| 🔴 | G2S11 | 15 |
| 🔴 | G2S12 | 16 |
| 🔴 | G2S14 | 19 |
| 🔴 | G3S03 | 18 |
| 🔴 | G3S10 | 19 |
| 🔴 | G3S13 | 19 |
| 🔴 | G3S14 | 18 |
| 🔴 | G3S16 | 18 |

## Windows per driver

| Driver | Windows |
|---|---|
| G1S01 | 19 |
| G1S02 | 20 |
| G1S03 | 18 |
| G1S05 | 24 |
| G1S06 | 15 |
| G1S07 | 16 |
| G1S08 | 20 |
| G1S09 | 17 |
| G1S13 | 21 |
| G1S14 | 19 |
| G1S15 | 27 |
| G1S16 | 21 |
| G1S17 | 21 |
| G2S01 | 22 |
| G2S02 | 23 |
| G2S03 | 21 |
| G2S04 | 27 |
| G2S05 | 18 |
| G2S06 | 23 |
| G2S07 | 28 |
| G2S08 | 23 |
| G2S09 | 18 |
| G2S10 | 21 |
| G2S11 | 15 |
| G2S12 | 16 |
| G2S13 | 21 |
| G2S14 | 19 |
| G2S15 | 23 |
| G2S16 | 20 |
| G3S01 | 23 |
| G3S02 | 27 |
| G3S03 | 18 |
| G3S04 | 23 |
| G3S05 | 23 |
| G3S06 | 24 |
| G3S07 | 20 |
| G3S08 | 27 |
| G3S09 | 22 |
| G3S10 | 19 |
| G3S11 | 20 |
| G3S12 | 24 |
| G3S13 | 19 |
| G3S14 | 18 |
| G3S15 | 22 |
| G3S16 | 18 |
| G3S17 | 21 |
