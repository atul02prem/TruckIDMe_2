# Step-signal separability — Cramér's V and mutual information

Every **step** signal, counted over **46 drivers**. These are the signals for which η² is the wrong instrument: it compares group means, so on a gear it asks whether drivers occupy different *average gears*, and an average gear of 4.3 is not a quantity.

- **Cramér's V** — association between driver identity and signal state, 0 (independent) to 1 (state determines driver).
- **Theil's U** — share of the signal's own entropy explained by knowing the driver; catches dependence that is not simple association.

Flags: 🔴 V ≥ 0.5 · 🟡 0.3–0.5 · 🟢 < 0.3. Both are **effect sizes, not significance tests** — CAN samples are autocorrelated at 10–67 Hz, so a p-value would be meaningless here while an effect size stays honest.

**The statistic flags; physics decides.** A high value says the signal separates drivers. Whether that is behaviour (this driver shifts differently) or a trip artifact is not something either number can tell.

## 🟢 No step signal reaches V ≥ 0.5 except SPN 975

## All step signals

| Flag | SPN | Signal | States | Cramér's V | Theil's U |
|---|--:|---|--:|--:|--:|
| 🔴 | 975 | `975 Engine Fan 1 Estimated Percent Speed` | 2 | 0.565 | 0.291 |
| 🟡 | 986 | `986 Engine Fan 1 Requested Percent Speed` | 2 | 0.316 | 0.102 |
| 🟡 | 3231 | `3231 Aftertreatment 1 Outlet Wide-Range Percent Oxygen 1 Reading Stable` | 2 | 0.306 | 0.194 |
| 🟡 | 3239 | `3239 Aftertreatment 2 Intake Dew Point` | 2 | 0.305 | 0.193 |
| 🟢 | 3229 | `3229 Aftertreatment 1 Outlet Gas Sensor 1 at Temperature` | 3 | 0.229 | 0.181 |
| 🟢 | 3230 | `3230 Aftertreatment 1 Outlet NOx 1 Reading Stable` | 3 | 0.228 | 0.182 |
| 🟢 | 3232 | `3232 Aftertreatment 1 Outlet Gas Sensor 1 Heater Preliminary FMI` | 4 | 0.189 | 0.176 |
| 🟢 | 2945 | `2945 Active Shift Console Indicator` | 2 | 0.143 | 0.097 |
| 🟢 | 4816 | `4816 Transmission Torque Converter Lockup Transition in Process` | 2 | 0.142 | 0.096 |
| 🟢 | 524 | `524 Transmission Selected Gear` | 7 | 0.117 | 0.023 |
| 🟢 | 523 | `523 Transmission Current Gear` | 7 | 0.117 | 0.023 |
| 🟢 | 2979 | `2979 Vehicle Acceleration Rate Limit Status` | 3 | 0.117 | 0.022 |
| 🟢 | 574 | `574 Transmission Shift In Process` | 2 | 0.107 | 0.008 |
| 🟢 | 573 | `573 Transmission Torque Converter Lockup Engaged` | 2 | 0.040 | 0.003 |
| 🟢 | 5015 | `5015 Momentary Engine Maximum Power Enable` | 1 | nan | nan |

## Why this report exists

`all_can_eta2.md` scored every one of the 102 signals with η², including these. For a step signal that number is not merely imprecise, it is answering a different question — so a step signal kept on an η² near zero was not actually cleared by any evidence. This report supplies the evidence that applies to them.

**This report measures only** — no exclusion labels, no recommendation. The decisions that cite it live in `DECISIONS.md`.

## Caveat — what Cramér's V cannot see

Both statistics are read off a driver × state contingency table, which discards temporal ordering. Two drivers who occupy the same gears for the same total time score identically whether one shifted twice or two hundred times. Gear (SPN 523/524) averages ~7.6 transitions per 120 s window in this data, so its *shifting behaviour* is invisible to this table and its low V is not evidence that gear carries no driver information — only that gear *occupancy* does not. Transition-count and time-in-state features are the instrument for that question.
