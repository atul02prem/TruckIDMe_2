# exp05 — per-channel identity ranking (51.2 s windows)

46-way closed set, chance 2.2%. Each channel occupies its own 256-dim block of the frozen embedding, so a channel's identity content can be measured on its own.

**Selection is leak-free.** Channels are ranked by mean between-driver `eta_squared` over their 256 dims, computed on **training windows only**. The single-channel probe accuracy below uses the test split and is reported as a descriptive check — it never drives selection.

## Top-k by ranking

| Channel set | dims | linear probe | LDA + centroid | random forest |
|---|--:|--:|--:|--:|
| `top5` | 1,280 | 16.9% | 18.5% | 13.7% |
| `top11` | 2,816 | 20.3% | 23.2% | 12.3% |
| `top15` | 3,840 | 22.7% | 29.2% | 15.9% |
| `top25` | 6,400 | 23.1% | 29.2% | 15.6% |
| `all50` | 12,800 | 24.6% | 23.2% | 19.1% |

Best subset: **top15** at 29.2%, against `all50`'s 24.6%.

## Channel ranking

| Rank | Channel | mean $\eta^2$ (train) | single-channel probe (test) |
|--:|---|--:|--:|
| 1 | SPN 1209 | 0.1060 | 8.7% |
| 2 | SPN 3226 | 0.1057 | 5.6% |
| 3 | SPN 641 | 0.1026 | 10.4% |
| 4 | SPN 91 ⚙ | 0.0997 | 14.9% |
| 5 | SPN 512 ⚙ | 0.0970 | 12.6% |
| 6 | SPN 5398 | 0.0908 | 8.4% |
| 7 | SPN 3357 | 0.0832 | 12.3% |
| 8 | SPN 92 | 0.0818 | 11.5% |
| 9 | SPN 514 | 0.0816 | 7.7% |
| 10 | SPN 2432 | 0.0812 | 11.3% |
| 11 | SPN 2659 | 0.0808 | 9.1% |
| 12 | SPN 3251 | 0.0802 | 6.8% |
| 13 | SPN 513 | 0.0791 | 13.3% |
| 14 | SPN 27 | 0.0699 | 6.5% |
| 15 | SPN 1242 | 0.0693 | 10.3% |
| 16 | SPN 3610 | 0.0644 | 6.8% |
| 17 | SPN 102 | 0.0644 | 6.0% |
| 18 | SPN 183 | 0.0629 | 7.5% |
| 19 | SPN 132 | 0.0614 | 10.4% |
| 20 | SPN 184 | 0.0610 | 7.9% |

⚙ marks a driver-actuated channel. **2 of 11** actuated channels appear in the top 11: SPN 91, SPN 512.

Agreement between the selection statistic and held-out single-channel accuracy: r = 0.82.

## Figure

- `/home/ap9107/TruckIDMe/outputs/figures/exp05_channel_ranking.png`

## Limitations

- **Single split, no error bars.** The random-draw control in `results.md` is what bounds chance-level subset performance.
- **Channels are ranked individually**, so a channel that is only useful in combination with another is ranked low. This measures marginal, not joint, identity content.
- Frozen encoder only; one drive per driver. See `DECISIONS.md` C1.
