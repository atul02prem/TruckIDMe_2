# exp05 — 46-way closed set across frozen-embedding channel subsets

Frozen Mantis embeddings (`embeddings_armB_51.2s.npz`), sliced channel-major. Mantis encodes each channel independently, so a channel subset is a **column slice** of the cached embedding and costs nothing to evaluate. Per-driver chronological 70/5/25 split, seed 42.

**46-way chance is 2.2%; 36-way chance is 2.8%.** exp04's 33.2% is 36-way and must not be compared with the 46-way rows below.

## 46-way

| Channel set | dims | linear probe | LDA + centroid | random forest | vs `all50` (best) |
|---|--:|--:|--:|--:|:--:|
| `all50` | 12,800 | 24.6% | 23.2% | 19.1% | 🟢 +0.0pp |
| `actuated11` | 2,816 | 13.8% | 12.0% | 12.6% | 🔴 -6.5pp |
| `attention15` | 3,840 | 22.4% | 22.7% | 13.5% | 🟡 -0.5pp |
| `random11` (×5) | 2,816 | 18.2% ± 2.1% | 18.1% ± 2.4% | 15.5% ± 2.3% | 🔴 -3.7pp |

## 36-way

| Channel set | dims | linear probe | LDA + centroid | random forest | vs `all50` (best) |
|---|--:|--:|--:|--:|:--:|
| `all50` | 12,800 | 28.3% | 32.0% | 20.5% | 🟢 +0.0pp |
| `actuated11` | 2,816 | 16.6% | 15.3% | 15.9% | 🔴 -4.6pp |
| `attention15` | 3,840 | 25.7% | 26.6% | 16.1% | 🟡 -2.6pp |
| `random11` (×5) | 2,816 | 21.0% ± 2.9% | 21.7% ± 3.2% | 19.4% ± 3.5% | 🟡 -1.1pp |

## How to read this

- **`actuated11` vs `random11` is the only comparison that says anything about the driver-actuated signals.** If they match, the actuated set is not special and any change is a dimensionality effect.
- **`attention15` is selection-biased.** Those channels were ranked by exp04's attention weights, fitted on labelled training data from this same split. Descriptive only.
- The flag compares each subset's **best** read-out against `all50`'s best: 🟢 at least equal, 🟡 within 3pp below, 🔴 worse than that.

## Channel sets

- `actuated11` (11): SPN 91, SPN 117, SPN 118, SPN 512, SPN 523, SPN 524, SPN 574, SPN 1087, SPN 1088, SPN 2945, SPN 7319
- `attention15` (15): SPN 513, SPN 2432, SPN 1242, SPN 5398, SPN 514, SPN 92, SPN 512, SPN 103, SPN 3357, SPN 2659, SPN 3226, SPN 184, SPN 91, SPN 3610, SPN 641

## Limitations

- **Frozen encoder only.** Slicing a *fine-tuned* encoder's embeddings would not equal training on the subset, because its weights were adapted while all 50 channels were present.
- **One drive per driver**, so the chronological split separates early from late in a single trip, not across sessions. See `DECISIONS.md` C1.
- Single split per cohort, so no error bars except on `random11`, where the spread is across channel draws rather than across splits.
