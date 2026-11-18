# exp05 — channel subsets, window length and channel ranking on the frozen encoder

> **Configuration note.** Every number here uses the **frozen** encoder with
> `cls_token`, read out after block 3 of 6 (index 2) — the project setting at the
> time. Both were later superseded: `mean_token` (exp06, `DECISIONS.md` D13) and,
> for the frozen arm, block 1 (exp08, D14). The *levels* below are therefore
> superseded. The *comparisons* — subset against subset, window against window —
> still stand, because token and block were held fixed within each table.

## Objective

Three questions about what the frozen encoder needs, all answerable without a
GPU because the encoder is frozen and its embeddings are cached:

1. **Do fewer channels do as well as all 50?** In particular, are the 11
   signals a driver physically commands (the "actuated" set) enough?
2. **Which window length?** Mantis takes a fixed 512 points, so a longer window
   buys context and pays in temporal resolution.
3. **Which channels carry driver identity?** A ranking chosen without touching
   the test split.

## Why this costs minutes

Mantis encodes each channel **independently** and concatenates the results, so
the 12,800-dim embedding is 50 contiguous blocks of 256. A channel subset is
therefore a column slice of the cached embedding — **identical** to re-embedding
only those channels. `verify_slice_equivalence.py` checks this against the
library: re-embedding the 11 actuated channels from scratch differs from the
slice by at most 8.6 × 10⁻⁶ (float32 round-off). Only the classifiers are
retrained per subset.

This holds only for a frozen encoder; slicing a fine-tuned encoder's output is
not the same as fine-tuning on the subset.

## Data lineage (dimensions at each stage)

| Stage | What | Shape |
|---|---|---|
| frozen embeddings | `src/features/build_embeddings.py`: Mantis-8M, block 3 of 6 (index 2), `cls_token` | (n, 12800) |
| channel slice | keep k blocks of 256 | (n, k × 256) |
| cohort | all 46 drivers, or exp04 partition 1's 36 known | rows |
| split | per-driver chronological 70% / 5% gap / 25% | e.g. 1,567 / 585 at 51.2 s |
| read-out | linear probe, LDA + centroid, random forest | 46 or 36 classes |

## Results

### 1. Channel subsets (51.2 s, best read-out per set)

| Set | dims | 46-way | 36-way |
|---|--:|--:|--:|
| all 50 channels | 12,800 | **24.6%** | **32.0%** |
| 11 actuated | 2,816 | 13.8% | 16.6% |
| 11 random (5 draws) | 2,816 | 18.2% ± 2.1 | 21.7% ± 3.2 |

**The actuated set is worse than random channel sets of the same size** — it
finished below all five random draws at 46-way, 36-way, and again at 120 s
(14.8% vs 22.0%). The hypothesis that driver identity lives in what the driver
commands is falsified. No 11-channel subset reaches all 50 channels — but a
*ranked* subset of 15 does better than all 50 (section 3), so which channels are
removed matters more than how many.

### 2. Window length (46-way, all 50 channels)

| Window | Effective rate | Windows | probe | LDA | forest |
|---|--:|--:|--:|--:|--:|
| 30 s | 17.07 Hz | 3,876 | 22.9% | 20.3% | 15.0% |
| 51.2 s | 10.00 Hz | 2,267 | **24.6%** | 23.2% | 19.1% |
| 90 s | 5.69 Hz | 1,290 | 22.6% | 25.0% | 14.6% |
| 120 s | 4.27 Hz | 964 | 21.9% | **27.7%** | 20.3% |

The two read-outs want different windows: the probe peaks at 51.2 s, LDA rises
with window length. The trade is three-way — context, temporal resolution, and
number of training windows. exp07 later showed the best window also flips when
the encoder is fine-tuned, so this sweep is frozen-specific.

### 3. Channel ranking (51.2 s, 46-way)

Channels ranked by between-driver η² of their 256-dim block, computed on
**training windows only**, so selection never sees the test split. The ranking
agrees with held-out single-channel accuracy at r = 0.82.

| Top-k | dims | LDA + centroid |
|---|--:|--:|
| 5 | 1,280 | 18.5% |
| 11 | 2,816 | 23.2% |
| **15** | 3,840 | **29.2%** |
| 25 | 6,400 | 29.2% |
| 50 | 12,800 | 23.2% |

**Exploratory, not a choice.** The ranking is fitted on training windows only,
but k was never chosen on inner validation and this table is scored on test, so
top-15's lead is reported, not adopted. All 50 channels stay in the model input.

Top-ranked channels: SPN 1209, 3226, 641, 91, 512, 5398, 3357, 92, 514, 2432 —
mostly engine response (torque, load, exhaust) rather than driver command. Only
2 of the 11 actuated channels make the top 11.

## Files

| File | What |
|---|---|
| `run.py` → `results.md`, `results_120s.md` | channel subsets, 46- and 36-way |
| `window_sweep.py` → `window_sweep.md` | four window lengths |
| `channel_ranking.py` → `channel_ranking.md` | η² ranking and top-k |
| `verify_slice_equivalence.py` | proof that slicing equals re-embedding |
| `finetune_subset.py` | **written, never run** — fine-tuning on 11 channels, dropped once the actuated set lost to random draws |

## Commands

```bash
python -u -m experiments.exp05_frozen_channel_subsets.verify_slice_equivalence
python -u -m experiments.exp05_frozen_channel_subsets.run
python -u -m experiments.exp05_frozen_channel_subsets.run --window 120 --cohort 46
python -u -m experiments.exp05_frozen_channel_subsets.window_sweep
python -u -m experiments.exp05_frozen_channel_subsets.channel_ranking
```

## Limitations

- `cls_token` and block 3 throughout; superseded (D13, D14).
- Single chronological split for each table; error bars only on random draws.
- `attention15` in `results.md` was ranked using labelled training data from
  the same split and is descriptive only.
- One drive per driver. See `DECISIONS.md` C1.
