# Signal-integrity investigation thread

A traceable chain: **flag → hypothesis → test → result → decision**, so any
conclusion about a flagged signal can be walked back to the evidence that
produced it. Append to the log; do not rewrite history.

---

## Origin

`QC/verify_sampling_rates.py` (all-drivers) → `sampling_rate_all_drivers.md`
flagged **3 signals**, and all 3 are **currently KEPT in the feature set**:

| flag | SPN | Signal | native Hz | evidence |
|:--:|--:|---|--:|---|
| 🔴 | 2979 | Vehicle Acceleration Rate Limit **Status** | 50 | multi-rate in 100% of drivers, native_std 138.5 |
| 🟡 | 3030 | Transmission Torque Converter **Ratio** | 50 | ~49% dropout in 98% of drivers |
| 🟡 | 5052 | Transmission Clutch/Converter Input **Speed** | 50 | ~47% dropout in 98% of drivers |

## The question (integrity, not accuracy)

Do these belong in the feature set, or are they **vehicle-state / status
proxies** whose presence-pattern encodes trip structure and leaks driver
identity? Judged by **η² + physical reasoning**, never accuracy — per the
leakage-audit methodology. A rate flag is only the entry point; the real test is
integrity.

## Hypotheses

| ID | Hypothesis | Rationale | Status |
|:--:|---|---|:--:|
| **H1** | 3030's ~49% dropout is **torque-converter-lockup-conditional** (silent when lockup engaged), not a logging fault | TC ratio (turbine/impeller) is undefined ≈ 1 when the lockup clutch is engaged; ECU stops sending it | ❌ **REFUTED** (T1) — present 97% unlocked / 99% locked; lockup does not gate it |
| **H2** | 5052's dropout is the **same mechanism** (converter input speed meaningless when locked) | Same subsystem as 3030 | ❌ **REFUTED** (T2) — present 100% unlocked / 99% locked |
| **H3** | 2979 is **genuinely event-driven multi-rate**, not an artifact | It is a *limit status* flag the ECU raises, not a periodic measurement | ✅ **CONFIRMED** (T3) — 54% of Δt are sub-mode bursts |
| **H4** | ~~these are vehicle-state signals whose presence-pattern leaks trip identity~~ **REVISED:** 3030/5052 are present ~100% of the time (distributed rate-thinning, not on/off) → presence cannot fingerprint the route. Leakage risk now rests **only on the values → η²** | Same integrity test as every other signal | ✅ **RESOLVED** (T4) — no leak; all 3 KEEP. η² = 0.000/0.016/0.023, at the behavioural-anchor level (0.009–0.018), nowhere near the leak anchor (245 = 1.000) |

## Tests

| ID | Test | Tests | Script | Pass criterion | Result |
|:--:|---|:--:|---|---|:--:|
| **T1** | Align 3030 sample-**presence** against SPN 573 (TC Lockup Engaged) state, per driver, aggregated | H1 | `QC/verify_flagged_signal_integrity.py` | presence(3030 \| locked) < 0.3 **and** presence(3030 \| unlocked) > 0.8 across drivers | 🔴 **refuted** — 97% / 99% |
| **T2** | Same, 5052 vs 573 | H2 | (same script) | same | 🔴 **refuted** — 100% / 99% |
| **T3** | 2979 Δt distribution: share of intervals faster than the 50 Hz mode | H3 | (same script) | ≥30% of Δt below the mode period (bursts) → multimodal | ✅ **confirmed** — 54%; Δt p10/p50/p90 = 3.3/16.9/20.9 ms |
| **T4** | η² of 3030 / 5052 / 2979 values (integrity) — the sole decider | H4 | `QC/verify_flagged_signal_eta2.py` → `flagged_signal_eta2.md` | η² ≳ 0.9 → exclude; ≈ behavioural anchors → keep | ✅ **all KEEP** — η² 0.023 / 0.016 / 0.000, interleaved with 84/190/91 anchors |

## Decision rules

- **T1 & T2 confirm →** 3030/5052 are TC-**state** signals (commanded by the
  transmission controller from speed/load, *not* the driver). Proceed to T4.
- **T3 confirms →** 2979 is an ECU-imposed **limit status**, not a behaviour;
  strong exclude candidate regardless of η².
- **T4 η² high →** add the confirmed signals to `EXCLUDE_SPNS` with this thread
  cited as the rationale, then regenerate features and re-check the audit.
- **Any test refutes →** the signal stays KEPT; record why here.

## Reference signals (available, verified healthy)

- **SPN 573** "TC Lockup Engaged" and **4816** "Lockup Transition" — both 🟢,
  100 Hz, native_std 0, 0% dropout. Reliable ground truth for the lockup state
  used in T1/T2.

## Revised understanding (post T1–T3)

- **3030 / 5052 are NOT block-silenced by lockup.** They are present ~97–100% of
  the time regardless of TC state; the ~49% "dropout" is **distributed
  rate-thinning** (effective ~25 Hz vs a 50 Hz mode), not an informative on/off
  pattern. Correction to an earlier note: the "one 10 s block" seen in G1S01 is a
  per-driver outlier, not the norm.
- Because presence is near-constant, **the presence pattern cannot leak the
  route.** The only open leakage question for 3030/5052 is whether their *values*
  separate drivers → **T4 (η²)**. They are drivetrain-loading signals (TC ratio,
  converter input speed), plausibly behavioural — decide on η², not on the flag.
- **2979** is a confirmed event-driven *limit-status* flag, not a periodic
  behaviour → strong exclude candidate on semantics; η² for completeness.

## Conclusion (investigation CLOSED)

**No change to `EXCLUDE_SPNS`. 3030, 5052, 2979 all stay in the feature set.**
The sampling-rate flags were *rate artifacts* (distributed thinning / event-driven
bursts), not leaks. η² on the values puts all three at the behavioural-signal
level, indistinguishable from wheel speed / RPM / pedal.

- The exercise **validated the leakage audit**: the behavioural anchors landed
  exactly where expected (η² ≈ 0.01) and the counter anchor at 1.000, so the η²
  machinery and the KEEP decisions are internally consistent.
- **Footnote (contribution, not integrity):** 2979 has η² = 0.000 — it doesn't
  leak, but it also barely varies between drivers, so it likely carries little
  behavioural signal. Cleared on *integrity*; revisit as a low-contribution
  feature in a later ablation, not here.

## Log

- **2026-07-30** — thread opened. Flags from `sampling_rate_all_drivers.md`
  (46-driver QC). All 3 flagged signals confirmed KEPT.
- **2026-07-30** — T1–T3 run (`flagged_signal_integrity.md`). **H1/H2 refuted**
  (lockup does not gate 3030/5052 — present 97–100% in both states); **H3
  confirmed** (2979 is 54% sub-mode bursts). H4 revised: presence-leak defused;
  decision now hinges solely on T4 (η² of values).
- **2026-07-30** — T4 run (`flagged_signal_eta2.md`). **All 3 KEEP** — η² =
  0.023/0.016/0.000 vs behavioural anchors 0.009–0.018 and leak anchor 1.000.
  Investigation closed; `EXCLUDE_SPNS` unchanged.
