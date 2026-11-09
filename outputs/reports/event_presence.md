# Event-signal presence — does the firing pattern identify the driver?

All **6 event** signals over **46 drivers**, raw CAN data. An event signal is absent most of the drive, so its values are not the question: **when and how often it fires** is.

| Column | Meaning |
|---|---|
| coverage | share of the drive the signal was transmitting |
| sd across drivers | how much that share varies between drives |
| η² on rate | driver separability of the per-120s-window firing rate |
| position | mean location of samples within the drive (0 = start, 1 = end) |
| early share | fraction of samples in the first 10% of the drive (uniform would give 10%) |

**This report measures only** — no exclusion labels, no recommendation.

## Why the spread matters more than the rate

The same artifact can be harmless or a severe leak, and only the spread across drivers distinguishes them. SPN 2979's unavailability sits at 28.44–28.60% for every one of the 46 drivers — a deterministic protocol cycle that cannot identify anyone. The aftertreatment group's ranges from 0% to 26% and clusters at drive start — a warm-up duration, which is trip identity. **A high rate is not the warning sign; a varying rate is.**

## All event signals

| Flag | SPN | Signal | Coverage | sd across drivers | η² on rate | Bursts | Position | Early share |
|---|--:|---|--:|--:|--:|--:|--:|--:|
| 🟢 | 4191 | `4191 Engine Requested Torque (Fractional)` | 8.6% | 0.012 | 0.106 | 178 | 0.491 | 11.4% |
| 🟢 | 518 | `518 Engine Requested Torque/Torque Limit` | 8.6% | 0.012 | 0.106 | 178 | 0.491 | 11.4% |
| 🟢 | 4206 | `4206 Message Counter` | 8.6% | 0.012 | 0.106 | 178 | 0.491 | 11.4% |
| 🟢 | 4207 | `4207 Message Checksum` | 8.6% | 0.012 | 0.106 | 178 | 0.491 | 11.4% |
| 🟢 | 898 | `898 Engine Requested Speed/Speed Limit` | 8.6% | 0.012 | 0.106 | 178 | 0.491 | 11.4% |
| 🟢 | 3544 | `3544 Time Remaining in Engine Operating State` | 16.4% | 0.048 | 0.061 | 22 | 0.508 | 11.3% |

## Uniform firing — 5 signals (sd < 0.02)

These fire at effectively the same rate for every driver, so the pattern carries no driver information regardless of η²:

- **SPN 4191** `4191 Engine Requested Torque (Fractional)` — coverage 6.2%–12.1% across 46 drivers (sd 0.0119)
- **SPN 518** `518 Engine Requested Torque/Torque Limit` — coverage 6.2%–12.1% across 46 drivers (sd 0.0119)
- **SPN 4206** `4206 Message Counter` — coverage 6.2%–12.1% across 46 drivers (sd 0.0119)
- **SPN 4207** `4207 Message Checksum` — coverage 6.2%–12.1% across 46 drivers (sd 0.0119)
- **SPN 898** `898 Engine Requested Speed/Speed Limit` — coverage 6.2%–12.1% across 46 drivers (sd 0.0119)

## Varying firing — 1 signals (sd ≥ 0.02)

The firing rate differs between drives, so the pattern is a candidate fingerprint. Physics decides whether the variation is behaviour or trip condition:

- **SPN 3544** `3544 Time Remaining in Engine Operating State` — coverage 7.4%–30.8% (sd 0.048), η² on rate 0.061

## ⚑ Corroboration against the dataset's own dictionary

`DriverIDSQLiteCSVDataDictionary.pdf` is quoted below. It settles two questions this report's statistics can only hint at.

### 1. The message grouping is confirmed by name

Five of these six signals produce **byte-identical statistics across every column above**, over all drivers. That implies they are fields of one message rather than five independent signals, and the dictionary says so outright:

> **SPN 898** — "Parameter provided to the engine from external sources in the *torque/speed control message*."
>
> **SPN 518** — "Parameter provided to the engine or retarder in the *torque/speed control message* for controlling or limiting the output torque."

That message is TSC1. So the input set was carrying one message five times, and 4206/4207 are its counter and checksum rather than vehicle state at all:

> **SPN 4206** — "The message counter is used to detect situations where the transmitting ECU malfunction repeats the same frame all the time."
>
> **SPN 4207** — "The message checksum is used to verify the signal path from the transmitting device to the receiving device… calculated using the first 7 data bytes, the message counter and the bytes of the message identifier."

Neither describes the truck. They describe the bus.

### 2. Observed values against the documented range

| Flag | SPN | Signal | Units | Observed values | Dictionary says |
|---|--:|---|---|---|---|
| ⚪ | 518 | `518 Engine Requested Torque/Torque Limit` | % | 127 values, -125–125 | no range given; observed -125 to 125% is exactly the J1939 percent-torque span, consistent with a correct decode |
| ⚪ | 898 | `898 Engine Requested Speed/Speed Limit` | rpm | 14414 values, 3424.12–8031.88 | no range given; the 8031.88 rpm ceiling is the saturation value for 0.125 rpm/bit over two bytes, so the scale decodes correctly |
| 🔴 | 3544 | `3544 Time Remaining in Engine Operating State` | Seconds | 64255 | 65535 (FFFFh) where time remaining is not applicable |
| 🔴 | 4191 | `4191 Engine Requested Torque (Fractional)` | % | 138 | 0000b-0111b = 0-0.875% at 0.125%/bit; 1000b-1111b not available |
| 🔴 | 4206 | `4206 Message Counter` | count | 1111 | counts 0 to 7 then wraps, increasing every cycle |
| ⚪ | 4207 | `4207 Message Checksum` | count | 1111 | no range given, but a checksum over the payload must change with it |

**SPN 4206 is the decisive one.** The dictionary states the counter "will count from 0 to 7 and then wrap" and that the transmitter "will increase the message counter in every cycle". It is observed **constant**, at a value outside 0–7. Both halves of its specification are violated at once, so this is not a judgement about field widths — it is the dataset's own documentation contradicted by the dataset's own values.

There is an irony worth recording: a counter frozen at one value is precisely the fault condition SPN 4206 exists to detect. Here the freezing is in the CSV export rather than on the bus.

**SPN 4207** compounds it. A checksum computed over the payload must change as the payload changes; it is observed constant, and constant at the *same* value as the counter — which a counter/checksum pair cannot be.

**SPN 3544** is a further anomaly of the same kind. The dictionary specifies **65535 (FFFFh)** for states where time remaining does not apply. The observed constant is **64255 (FAFFh)** — the top of the valid range for a two-byte parameter, not the documented not-applicable code. Either the ECU saturates instead of signalling inapplicability, or the decode clamps. It carries no information either way.

**Why this matters beyond these six signals.** Three violations are proven here against the dictionary — 4191 and 4206 outside their stated ranges, 3544 reporting a constant that is not its stated sentinel — and 4207 fails on logic alone, a payload checksum that never changes. Add SPN 4154 from the continuous report, whose values exceed its documented 0–0.875% range by 15–158×, and that is **four columns whose values their own dictionary forbids, plus a fifth that cannot be what it claims**.

Note which ones *pass*: SPN 518's observed −125 to 125% is exactly the J1939 percent-torque span, and SPN 898's 8031.88 rpm ceiling is the saturation value for 0.125 rpm/bit over two bytes. The decoder handles ordinary scaled parameters correctly. What it appears to mishandle are **sub-byte bit fields** — fractional torque adders, a 3-bit counter, a checksum nibble — which is a narrower and more plausible fault than wholesale breakage, and it predicts where else to look.

All six signals here are excluded on data quality regardless, so no decision rests on resolving this. It is a dataset-wide question. **Action: obtain the DBC.**


## Caveat

A burst is counted where the gap between consecutive samples exceeds ten times the signal's own median period. That multiplier is a judgement call; it separates genuine silences from ordinary timing jitter, and the burst column is descriptive — no decision rests on it.
