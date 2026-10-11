# TruckIDMe — SPN Exclusion Rationale

Documentation of every SPN in `EXCLUDE_SPNS` (`src/config.py`), why it is
excluded, and how confident that exclusion is. **Verify the reasoning against
the J1939 data dictionary and the empirical reports before citing in the paper.**

## The exclusion principle

Driver-behaviour modelling wants signals that encode **how a person drives**
(pedal, brake, gear, RPM, torque demand) — behaviour that generalises across
drives. We must exclude signals that instead encode **which drive this is**.
Because each driver has exactly **one** drive in the ORNL dataset, any signal
that fingerprints the *trip* trivially fingerprints the *driver* — giving
inflated accuracy that would collapse on a new drive of the same person.

Four leakage/quality mechanisms:

1. **Cumulative counters** — monotonic lifetime totals. Each drive occupies a
   unique, non-overlapping value range → an exact trip label.
2. **Session/ambient state** — starting fuel, tank levels, ambient temperature,
   warmup temperatures. Set by *when/where* the drive happened, not by driving.
3. **Protocol / status / diagnostic** — counters, checksums, FMI codes, state
   flags. No behavioural meaning; near-zero or nominal variance.
4. **Data-quality** — bursty signals silent ~92% of the time where our
   mean+ffill alignment produces stale, misleading values.

## Confidence tiers

- **STRONG** — exclusion is unambiguous; keep out.
- **DEFENSIBLE** — real behavioural content exists but is confounded with
  ambient/warmup/trip state we cannot disentangle; conservative to exclude.
- **VERIFY** — dropped largely because it was in the collaborator `drop.py.txt`
  list or is redundant; **arguably behavioural — re-examine before finalising.**

---

## Tier 1 — STRONG (cumulative counters)

Monotonic lifetime or per-trip accumulators. A single drive spans a unique
contiguous value band → direct trip identity.

| SPN | Name | Unit | Why excluded |
|---|---|---|---|
| 245 | Total Vehicle Distance | km | Lifetime odometer. Non-overlapping per-drive range = exact trip ID. |
| 244 | Trip Distance | km | Resets per trip but monotonic within it → encodes "how far into the drive" ≈ a timestamp. |
| 918 | Trip Distance (High Res) | m | Same as 244, finer resolution. |
| 250 | Engine Total Fuel Used | l | Lifetime fuel counter — same leak as odometer. |
| 182 | Engine Trip Fuel | l | Per-trip monotonic fuel accumulator. |
| 247 | Engine Total Hours of Operation | h | Lifetime engine-hours counter. |
| 235 | Engine Total Idle Hours | h | Lifetime idle-hours counter. |
| 249 | Engine Total Revolutions | r | Lifetime crank-revolution counter. |
| 236 | Engine Total Idle Fuel Used | l | Lifetime idle-fuel counter. |

## Tier 1 — STRONG (protocol / status / diagnostic — no behaviour)

| SPN | Name | Why excluded |
|---|---|---|
| 4206 | Message Counter | Protocol field cycling 0–7. No physical meaning. |
| 4207 | Message Checksum | Protocol integrity field, effectively random. No behaviour. |
| 3232 | Outlet Gas Sensor 1 Heater Preliminary FMI | J1939 fault-mode indicator code — diagnostic, not behaviour. |
| 3231 | Outlet Wide-Range O2 Reading Stable | Sensor status flag (stable / not). Not behaviour. |
| 2945 | Active Shift Console Indicator | Which shift console is active — a near-constant configuration state. |
| 4816 | Transmission Lockup Transition In Process | Transient status flag; sparse; not a behaviour signal. |

## Tier 1 — STRONG (ambient — encodes day/place of experiment)

Different drivers drove on different days → these are proxies for "which day",
i.e. trip identity, plus fixed route effects.

| SPN | Name | Unit | Why excluded |
|---|---|---|---|
| 171 | Ambient Air Temperature | °C | Weather on the drive's day. Proxy for trip. |
| 108 | Barometric Pressure | kPa | Weather + altitude; route fixed → mostly day-to-day weather. |

## Tier 1 — STRONG (trip-state levels — set at engine start)

Whatever value the tank/maintenance state happened to hold when this driver
got in. Arbitrary per trip; constant-ish within it. **These were our top
empirical RF leaks** (see `baseline_rf_results.md` pre-fix run).

| SPN | Name | Unit | Why excluded |
|---|---|---|---|
| 96 | Fuel Level 1 | % | Starting fuel level — arbitrary per trip. Was RF importance rank 1–3. |
| 1761 | DEF Tank Volume | % | Starting DEF level — arbitrary per trip. |
| 3721 | DPF Time Since Last Active Regeneration | s | Maintenance state at trip start. |
| 5466 | DPF Soot Load Regeneration Threshold | % | DPF cleanliness state at trip start. |

## Tier 2 — DEFENSIBLE (running averages — trip history)

Real behavioural content (an aggressive driver has worse economy), but as
**trip-cumulative averages** they converge to a per-drive constant that acts as
a trip fingerprint rather than a generalisable feature.

| SPN | Name | Unit | Note |
|---|---|---|---|
| 1029 | Trip Average Fuel Rate | l/h | Trip-running average → per-drive constant. |
| 185 | Engine Average Fuel Economy | km/L | Same. Instantaneous economy would be behavioural; the *average* leaks. |

## Tier 2 — DEFENSIBLE (thermal / warmup — confounded with ambient + warmup)

Temperatures rise on a warmup curve and track ambient. They carry *some*
behavioural load (hard driving heats components), but that is confounded with
(a) ambient temperature = day-of-experiment and (b) warmup position = time into
trip. We cannot disentangle, so we exclude conservatively. **This is a
deliberate choice to sacrifice possible signal to avoid a confound — a reviewer
may ask about it.**

| SPN | Name | Unit |
|---|---|---|
| 3031 | DEF Tank Temperature | °C |
| 4360 | SCR Intake Temperature | °C |
| 1172 | Turbocharger 1 Compressor Intake Temperature | °C |
| 1136 | Engine ECU Temperature | °C |
| 110 | Engine Coolant Temperature | °C |
| 105 | Engine Intake Manifold 1 Temperature | °C |
| 177 | Transmission Oil Temperature | °C |
| 3251 | DPF Differential Pressure | kPa | (soot-fill state dominates over load response) |

## Tier 2 — DEFENSIBLE (thermal management actuators)

| SPN | Name | Unit | Note |
|---|---|---|---|
| 975 | Engine Fan 1 Estimated Percent Speed | % | Driven by coolant temp (ambient + warmup); mostly binary. |
| 986 | Engine Fan 1 Requested Percent Speed | % | Companion request to 975. |

## Tier 2 — DEFENSIBLE (redundant / low-information encodings)

| SPN | Name | Note |
|---|---|---|
| 4154 | Actual Engine Percent Torque (Fractional) | 3-bit fractional companion to SPN 513 (kept). Redundant low-res detail. |
| 4191 | Engine Requested Torque (Fractional) | Fractional companion; also bursty (below). |

## Data-quality — BURSTY (silent ~92% of the time; ffill unsafe)

Fire at 100 Hz only inside specific operating modes (cruise, shift requests,
finite-time engine states) then go silent. Our mean-window + ffill alignment
carries stale values across silent periods. See
`window_alignment_nulls.md`. **Excluded for the first pass — genuinely
behavioural (cruise usage!) and worth re-including later with a `*_active`
flag.**

| SPN | Name | Unit |
|---|---|---|
| 898 | Engine Requested Speed/Speed Limit | rpm |
| 518 | Engine Requested Torque/Torque Limit | % |
| 4191 | Engine Requested Torque (Fractional) | — |
| 3544 | Time Remaining in Engine Operating State | s |

## Tier 3 — VERIFY (questionable — arguably behavioural, re-examine)

Dropped mainly because they appeared in the collaborator `drop.py.txt` list.
Each has a plausible behavioural interpretation. **Before finalising, test
whether re-including these helps or hurts, and whether they leak.**

| SPN | Name | Unit | Argument to KEEP | Argument to DROP |
|---|---|---|---|---|
| 132 | Engine Intake Air Mass Flow Rate | kg/h | Tracks engine load closely → strongly behavioural. | Correlated with fuel rate / RPM already kept; possible redundancy. |
| 5313 | Commanded Engine Fuel Rail Pressure | MPa | Load-dependent control setpoint → behavioural. | In drop.py.txt; may correlate with torque signals. |
| 3216 | Engine Exhaust 1 NOx | ppm | Rises with load/aggressiveness → behavioural. | Confounded with aftertreatment thermal state. |
| 2978 | Estimated Engine Parasitic Losses (% Torque) | % | Reflects accessory + load state. | Largely a derived thermal/accessory quantity, weak behaviour. |
| 168 | Battery Potential / Power Input 1 | V | — | Electrical/alternator state, weakly driver-linked; was RF leak rank 19. Lean DROP. |

---

## Open caveats for the paper

1. **Soft-leakage aftertreatment thermals still rank high** in the *post-fix* RF
   (`412 EGR Temp`, `4363 SCR Outlet`, `3242 DPF Intake`, `5862 SCR
   Intermediate`, `3246 DPF Outlet` — all currently **kept**). These are the
   same *kind* of confounded thermal signal as the Tier-2 excludes. Decide
   whether consistency demands excluding them too. Excluding them is the
   stricter, more defensible science; it will likely lower accuracy.
2. **Tier-3 signals** should get an explicit ablation: run the classifier with
   and without them and report the delta.
3. Every "STRONG" exclusion should be reproducible from first principles
   (cumulative = monotonic; ambient = day proxy). The "DEFENSIBLE" and "VERIFY"
   tiers are judgement calls that a reviewer may challenge — document the
   ablation results to back them.
