---
name: dimensionality-change
description: Standard operating procedure for any change to what the model sees — dropping or adding signals, changing the channel set, changing aggregation or window length, applying PCA or channel adapters. Produces before/after control numbers with two classical models plus the integrity evidence, and records the decision. Use whenever the feature or channel set changes, or when asked whether a signal should be excluded.
---

# SOP: changing what the model sees

Any change to the inputs — dropping signals, adding them back, changing how they
are aggregated, changing window length, PCA or channel adapters — needs **two
separate questions answered with two separate instruments**. Conflating them is
the single most common error in this literature.

| Question | Instrument | Verdict power |
|---|---|---|
| **Is this signal legitimate?** (integrity) | the signal's *kind*, a separability statistic, and **physics** | **decides** |
| **What did the change cost?** (contribution) | before/after accuracy, two models, identical split | **informative only** |

## The forbidden inference

**Never conclude leakage from an accuracy delta.** Leaks are exactly what inflate
accuracy, so a drop when a signal is removed is equally consistent with "it was a
leak" and "it was genuinely behavioural". Both directions are traps:

- accuracy **rises** after removal → **not** proof the signal was a leak
- accuracy **falls** after removal → **not** proof the signal was innocent

Worked example from this project: removing the thermal/ambient family cost 45
percentage points (74% → 29%). That established the family was *predictive*. What
established *leakage* was physics — a coolant temperature is not a driver action —
plus the fact that each driver drove on a different day, so trip conditions and
driver identity are confounded (`DECISIONS.md` C1).

## Step 1 — Integrity (the part that decides)

For every signal being added or removed, record three things:

1. **Kind**, from `outputs/reports/signal_classification.md`. This picks the valid
   statistic, so it comes first:
   - continuous / quantised-continuous → **η²**, optionally mutual information
   - discrete-state / binary → **Cramér's V** (η² is invalid on an enum)
   - constant → **no statistic**; drop it, it has no variance
2. **The statistic's value**, with anchors so the scale is readable: known
   behavioural signals (SPN 91 pedal, 84 wheel speed, 190 engine speed) and a known
   leak (SPN 245 total vehicle distance, η² ≈ 1.0).
3. **A physics sentence** — can a driver's actions plausibly produce this
   separation? "The driver cannot manipulate this" is a reason to **exclude**, not
   to trust (see `DECISIONS.md`, the Kwak et al. critique).

Optional, for signals where physics is genuinely ambiguous (fuel-rail pressure,
boost, turbo speed): compare η² on raw samples against η² on per-window means. A
much larger window-mean η² means the discriminating information sits in the slow
level (session state) rather than the fast variation (behaviour).

## Step 2 — Control numbers (the part that informs)

Run **two models with different inductive biases** so a result does not rest on
one algorithm's quirks:

- `RandomForestClassifier` — bagging, random feature subsets
- `HistGradientBoostingClassifier` — boosting, depth-wise growth

Not two variants of the same family (Random Forest and Extra Trees are too alike
to corroborate each other).

Hold everything else fixed:

- identical windows, identical per-driver chronological split (train first 70%,
  discard a 5% gap, test last 25%), identical seed
- report **top-1 / top-5** and **pooled per driver** (one decision from all of a
  driver's test windows — the deployment question)
- state the noise floor alongside the delta: in this dataset one test window is
  **0.4 pp** and one driver is **2.2 pp** of pooled accuracy, so differences below
  ~2 pp are not findings

## Step 3 — Record it

Append to `DECISIONS.md`: what changed, the integrity evidence per signal, the
before/after table, and the verdict with its physics justification. If the change
alters a published number, update `RESULTS.md` and re-run
`scripts/check_results_consistency.py`.

## Report template

```markdown
## Change: <what changed>

### Integrity (decides)
| SPN | Signal | Kind | Statistic | Value | Physics verdict |
|--:|---|---|---|--:|---|
| 110 | Engine Coolant Temperature | continuous | η² (raw) | 0.078 | EXCLUDE — thermal state, proxies trip timing, not a driver action |

Anchors: behavioural 91/84/190 = <values> · leak 245 = <value>

### Cost (informative only)
| Model | Top-1 before | Top-1 after | Δ | Top-5 Δ | Pooled Δ |
|---|--:|--:|--:|--:|--:|
| Random Forest | | | | | |
| HistGradientBoosting | | | | | |

Noise floor: 1 window = 0.4 pp, 1 driver = 2.2 pp pooled.

### Verdict
<decision, justified by the integrity column — never by the cost column>
```

## Checks that must pass before the change is accepted

- [ ] every affected signal has a **kind**, and the statistic used is valid for it
- [ ] every exclusion has a **physics sentence**, not only a statistic
- [ ] constant (zero-variance) signals dropped, not fed to the model
- [ ] discrete and binary signals aggregated by **mode or last value**, never
      mean-aggregated or linearly interpolated
- [ ] before/after run on the **same split with the same seed**, two model families
- [ ] delta compared against the noise floor before being called an effect
- [ ] decision appended to `DECISIONS.md`; `RESULTS.md` updated if a headline moved
