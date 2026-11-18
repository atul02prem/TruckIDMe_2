# Decisions log

Every judgement call made while building this project, with the reasoning and
who made it. Written so the work can be reviewed end to end rather than taken
on trust. Newest first within each section.

---

## S6 — Resampling stays `np.interp`: bin averaging tested and not adopted

**The question.** `np.interp` point-samples each channel onto the 512-point grid,
so a channel faster than the grid is decimated without averaging. Bin averaging
(the mean of the raw samples in each of 512 bins) is the textbook alternative.

**Rule, fixed before the test run:** adopt bin averaging only if, at the headline
30 s window, its mean driver AUROC is higher **and** it improves on at least 4 of
5 partitions **and** closed-set LDA is not more than 2pp lower.

**Measured** (`experiments/exp08_layer_resampling/round1.md`, `round2.md`):

| Window | LDA, binavg − interp | driver AUROC, binavg − interp | partitions improved |
|--:|--:|--:|--:|
| **30 s** | +1.3pp | +0.018 | **2 of 5** |
| 51.2 s | −2.1pp | −0.051 | 1 of 5 |
| 90 s | −0.9pp | −0.024 | 2 of 5 |
| 120 s | +4.2pp | −0.041 | 2 of 5 |

Inner validation (Round 1) had already kept `np.interp`. On test, bin averaging's
higher mean at 30 s rests on one partition (driver AUROC 0.844 against 0.669); it
improves 2 of 5. **The rule is not met; `np.interp` stays.** Its distortion is
measured for both signal types (`resampling_distortion.md`, S5).

---

## S5 — Step signals stay on linear interpolation: damage measured, bounded, accepted

**The problem.** `build_windows.resample_window` applies `np.interp` to every
channel. That is the correct method for the **44 continuous** channels and the wrong
method for the **6 step** channels — 523, 524 (gear), 573 (lockup engaged), 574
(shift in process), 2945 (shift console), 4816 (lockup transition). Interpolating
gear 3 to gear 4 emits 3.5, a state the transmission was never in, and spreads each
change across the gap between two samples. The correct method for a step signal is
zero-order hold (repeat the previous value), per `signal_classification.md`.

**Decision: keep `np.interp` for all 50 channels. Zero-order hold is not built.**
The defect is real; it was measured, and it is too small to change a conclusion.

**The measurement** — `QC/verify_aggregation_validity_50ch.py`, all 46 drivers,
every window length (`outputs/reports/aggregation_validity_50ch.md`):

| SPN | Signal | Native rate | Illegal values, worst window length |
|--:|---|--:|--:|
| 524 | Selected Gear | 10 Hz | 0.64% |
| 523 | Current Gear | 10 Hz | 0.65% |
| 573 | Lockup Engaged | 100 Hz | 0.13% |
| 574 | Shift In Process | 100 Hz | 0.02% |
| 2945 | Shift Console | 10 Hz | 0.01% |
| 4816 | Lockup Transition | 100 Hz | 0.00% |

At most about 3 of the 512 points per window are fabricated, and the share is the
same at 30, 51.2, 90 and 120 s: a shorter window holds fewer transitions but also
fewer seconds, and the two cancel.

**Why this is acceptable, not ignored:**

1. **Where interpolation did real damage, the channel was removed.** SPN 2979 had
   40.2% illegal values and SPN 3030 was interpolated across multi-second
   blackouts; both are excluded (S3). Every channel was measured; the six kept are
   the ones where the damage is under 1%.
2. **Zero-order hold would not recover the true timing either.** A sensor logged
   at 10 Hz only says a gear change happened somewhere in a 0.1 s gap.
   Interpolation spreads the change across that gap; zero-order hold places it at
   the later sample, up to 0.1 s late. Both carry the same timing uncertainty,
   because it is set by the sensor's rate (0.1 s for gear, 0.01 s for the 100 Hz
   channels), not by the resampling method.
3. **The fabricated points cannot leak identity.** They occur only at genuine
   transitions, so they mark how often a driver shifts — real driving behaviour,
   already present in the signal — rather than an artefact unrelated to the driver.

**Not measured:** the effect of these six channels on the model. The 0.64% bounds
how much of the input is fabricated, not how much of the result depends on it.

**Future work, recorded rather than lost:**

- **Ablation:** drop the six step channels and re-score. For the frozen encoder this
  is a column slice of the cached embeddings — verified equal to a re-embed to
  ≤8.6e-6 in exp05 — so it needs no GPU. If accuracy does not move, the step
  channels' pre-processing cannot be driving the results, whichever method is used.
- **Typed resampling:** zero-order hold for the six step channels, linear
  interpolation for the rest.

**Stated limitation for the writeup:** six of 50 channels are step signals resampled
by linear interpolation; at most 0.65% of their values are fabricated, at every
window length, and the timing of each state change is uncertain by one native
sample interval regardless of the resampling method.

Evidence: `outputs/reports/aggregation_validity_50ch.md` (step channels),
`outputs/reports/resampling_distortion.md` (continuous channels),
`outputs/reports/sampling_rate_all_drivers.md` (native rates).

---

## S3 — Model input is 50 channels: SPN 51, 3030 and 2979 dropped on data quality

**Supersedes S2's "keep 3030".** Same scope rule, applied one step further: a
channel that does not fit the input tensor is removed rather than repaired.

| SPN | Basis | η² (not the reason) |
|--:|---|---|
| 51 Engine Throttle Valve 1 Position 1 | one value **98.35%** of a typical drive, **and** the highest aliased power of any kept channel (**0.536** at 120 s) | 0.001 / 0.040 |
| 3030 Transmission Torque Converter Ratio | **16–36 genuine multi-second blackouts per drive in all 46 drivers**, median worst gap 6.26 s, linearly interpolated across | 0.023 / 0.055 |
| 2979 Vehicle Acceleration Rate Limit Status | a **two-state flag** (`00b` not active, `01b` active) whose `11b = Not available` sentinel occupies **28.57%** of samples and sits numerically **11× above the real 0–1 range**. Interpolating across it manufactures values like 3.7 and 7.4 — **40.2% of its aggregated values are illegal**, with 4,793 fabricated transitions per window | 0.117 (Cramér's V) |

**The basis is data quality, not separability.** η² is recorded above only to show
what is given up; it is not the criterion. Gating channels by η² would have dropped
the brake pedal (117/118/1087, η² ≈ 0.021) and the relative wheel speeds (905/906,
η² ≈ 0.008) — all directly driver-actuated, and low η² is exactly what a
*behavioural* signal should show. η² detects leakage; it does not rank usefulness,
and for a neural encoder reading a waveform it says little about what is usable.

**Upsampling is explicitly not a reason to drop.** 11 channels are upsampled at a
120 s window and 32 at 30 s, but those interpolated points lie *between real
samples* — a 1 Hz brake pressure smoothly filled to 4.27 Hz still carries its
signal. That is categorically different from SPN 3030, where interpolation spans
six seconds of genuine silence. SPN 5052 belongs in the benign category: its worst
gap across the whole dataset is 0.102 s, smaller than one grid step at 120 s.

**No anti-alias filter.** Median aliased power is **0.4%**, so a filter would change
almost nothing; it cannot recover content above Nyquist, only stop it folding back.
And the window sweep found 30 s at 17.07 Hz *lost* to 120 s at 4.27 Hz, which is
evidence the high-frequency band carries no driver signal worth cleaning up. Proper
anti-aliasing on irregularly sampled data also needs three operations where there is
now one.

**Deferred, recorded rather than lost:** masking SPN 3030 with a torque-converter
lockup indicator — its blackout pattern *is* the lockup pattern, and when a driver
lets the converter lock up is driving style that interpolation erases. Also
anti-alias filtering. Neither is built.

**⚑ SPN 2979 is a bookkeeping correction, not new analysis.** S1 already established
it is unusable: *"40.2% of its aggregated values are currently illegal because
interpolation runs across the sentinel. Unusable until sentinel → NaN."* It was
recorded there as **"kept conditionally"** rather than excluded, so it never entered
the exclusion list the build scripts read, and a conditional whose precondition was
then deferred silently became an inclusion. **A condition that cannot be satisfied
within scope should be recorded as an exclusion.** Corrected here.

Three independent measurements agree on it: 40.2% illegal aggregated values
(`aggregation_validity.md`), round-trip error **1.150** — above 1.0, meaning the
interpolated reconstruction is worse than predicting the channel's mean — and the
highest anti-alias delta of any channel at **every** window length (0.688 at 120 s),
the only channel flagged severe at all four.

**Lineage:** 102 raw signals → 49 excluded (S1) → 53 → **50 model channels**
(S1's 49 + SPN 51 + SPN 3030 + SPN 2979 = 52 excluded of 102).

---

## S2 — SPN 3030 and 5052 kept as-is; masking deferred as out of scope

> **⚑ Partly superseded by S3:** SPN 3030 was later dropped on data quality. The SPN 5052 decision below still stands.

**Scope rule applied (user's call, 2026-11-11):** this is a capstone on a deadline,
not a journal paper. A channel that would need extra processing to use correctly is
dropped or kept as-is with a stated limitation — it does not get new machinery.

**The framing that prompted this was wrong, in opposite directions for the two
channels.** Both were reported at "~48% dropout", which suggested half-fabricated
values. Measured directly:

| | effective rate | median worst gap | drivers with any gap > 1 s |
|---|--:|--:|--:|
| 5052 | 26.26 Hz | **0.102 s** | **1 / 46** |
| 3030 | 25.11 Hz | **6.259 s** | **46 / 46**, 16–36 blackouts each |

**SPN 5052 has no silence at all.** Its worst gap across the dataset is a tenth of
a second. The "48% dropout" was an artifact of scoring sample count against a 50 Hz
nominal when its real cadence is ~26 Hz — short 50 Hz bursts with 100 ms pauses. At
a 120 s window each of the 512 grid points spans 234 ms, so its worst gap is smaller
than one grid step. **Nothing to decide; keep.**

**SPN 3030's blackouts are real** — every driver, 16–36 per drive, median worst
6.26 s, which at 120 s is ~26 consecutive fabricated grid points. The asymmetry is
the diagnostic: the research places both SPNs in PGN 61452 (ETC8), so a protocol
cause would hit both identically, and it does not (46/46 vs 1/46). The physical
reading fits instead — torque converter *ratio* is only meaningful while the
converter is unlocked, where input *speed* is measurable either way. On a 20-mile
route with highway segments, 16–36 lockup episodes per drive is expected.

**⚑ Not a standards claim.** Deep research across the public J1939 mirrors, Allison
and Eaton service documentation, Vector/Kvaser/CSS tooling docs and the J1939 logging
literature found **no source stating that ETC8 is transmitted conditionally**. The
one cell that would settle it — ETC8's rate field in J1939DA — is paywalled. The
writeup must say "consistent with" and not "the standard specifies".

**Decision: keep both, 53 channels, no masking.** Masking 3030's blackouts with an
indicator channel is the methodologically better answer, and its pattern is
genuinely behavioural — when a driver lets the converter lock up is driving style,
which interpolation erases. But it is new machinery on a deadline, so it is
**deferred and recorded as future work** rather than built.

**Stated limitation for the writeup:** one of 53 channels is linearly interpolated
across ~20–30 multi-second gaps per drive. Round-trip error measures 0.030, but that
statistic only compares at observed timestamps and therefore **cannot** measure error
inside a gap, where there is no ground truth. The honest statement is that the
fabrication is bounded in extent, not that it is accurate.

Related: the sentinel pattern is the documented J1939 convention for missing data
(Kvaser: "the byte that should have contained this parameter is set to 'not
available' (0xFF)"), which makes silence the unusual case — see SPN 2979 in S1,
which signals `11b = Not available` rather than going quiet.

---

## S1 — The signal exclusion list: 40 → 49, decided from type-matched statistics

**Full reasoning:** `outputs/reports/signal_exclusion_decisions.md`
**Per-signal before/after, all 102 signals:** `outputs/reports/decisions_reconciliation.md`

Until now every signal was screened with **one statistic, η², regardless of type**.
η² compares group means, which is the wrong question for a step signal (an average
gear of 4.3 is not a quantity) and no question at all for an event signal absent 92%
of the drive. The 15 step and 6 event signals had therefore **never been cleared by
any evidence that applied to them**. `all_can_eta2.md` is superseded and now carries
a correction banner.

Replaced by three type-matched reports covering the same 102 signals (81 + 15 + 6),
each carrying **no exclusion labels and no recommendations** — a measurement that
already knows the answer cannot audit it. Decisions live in the artifact above.

**Rule applied: statistics screen · physics decides · empirics verify.** A statistic
never excludes a signal on its own, and — the asymmetry the previous audit missed —
never *keeps* one on its own either.

**Nine new exclusions.** 5015 (constant: one value across 12.9M samples, 46/46
drivers) · 3229/3230/3231/3232 (the "not available" period is a sensor warm-up
duration: 0–26.18% per drive, 57.7% of it in the first 10% of the drive — ambient
temperature and soak time, which under C1 is the driver) · 3239 (dew point is
meteorology) · 2978 (parasitic losses are accessory and thermal load, not driver
input; raw η² 0.244 → **window 0.665**, the thermal family in disguise) · 515
(an ECU setpoint the driver cannot address, holding one value for **99.22%** of
6.47M samples; its only variation is an idle↔setpoint ramp, absent entirely from
9 of the 46 drives).

**No signal is re-introduced.** Channels 62 → 53.

**4154 is excluded on data quality — reversing an earlier "keep".** It was first
assumed constant once sentinels were removed (wrong: it varies for all 46 drivers),
then kept on the watch list because it neither leaks nor is constant. Checking its
definition against `DriverIDSQLiteCSVDataDictionary.pdf` settled it: the legal range
is **0 to 0.875% in 0.125%/bit steps**, and **9.31% of samples sit outside it by
15–158×** (`13.0`, `125.0`, `138.0`; only `0.0` is legal). The observed set is exactly
{0, 13, 125, 13+125} — all sums of two components, the signature of bit-packing — and
`138.0` is also the impossible constant held by SPN 4191. Excluded on the same grounds
already applied to 4191/4206/4207.

**⚑ This is a dataset-wide concern, not four bad columns.** Four columns whose values
their own dictionary forbids points at the **decoder used for the CSV export**. If it
is wrong for these it may be wrong for others. **Action: obtain the DBC**; state it as
a limitation in the writeup regardless.

**Two physics claims are now citations rather than inferences**, both from the
repository's own data dictionary. 2978's exclusion rested on my argument that
parasitic losses track accessory and thermal load; the dictionary names the sources as
"cooling fan, air compressor, air conditioning". And the `SIGNAL_REVIEW` override
recording 4154 as continuous is confirmed almost verbatim — it was right about the
**SPN**; what nobody had checked was whether the **column** honours it.

**A redundancy found in passing:** the dictionary states SPN 5398's value is *included
in* SPN 514, so those two kept channels are not independent. Noted on the watch list.

**2979 is kept conditionally.** Clean on leakage (V 0.117; its 28.44–28.60%
unavailability is identical for all 46 drivers — a deterministic protocol cycle,
the opposite of a fingerprint), but 40.2% of its aggregated values are currently
illegal because interpolation runs across the sentinel. Unusable until sentinel →
`NaN` and zero-order hold land.

**Two honest results worth recording.** Of the 11 signals where window η² exceeds
raw η² by ≥ 0.15, exactly **one** changed a verdict (2978) — the second scale was
argued for as a major addition and delivered a single signal. Mutual information
delivered **none**: no signal has MI ≥ 0.5 while both η² columns sit below 0.5, and
MI is systematically lower than η² here, so it is a weaker detector rather than a
complementary one. Both are kept in the reports as recorded negative results.

**🟡 A soft spot, named rather than hidden.** Nine of the sixteen thermal-family
exclusions score **below 0.2 on both η² scales** and are excluded on mechanism
alone. Their empirical support was the 74% → 29% collapse — but the leakiest thermal
signals (DEF tank 0.986, ambient air 0.968, turbo intake 0.941) were removed in the
*previous* iteration, so how much of that 45-point drop belonged to this group is
**not currently known**. Experiment 2 in the artifact decomposes it.

**Nothing is written to `src/config.py` yet.** A drop list was once accepted here
that collapsed the channel set to 4 signals; the guard is that the channel-set
change and the aggregation change run as **separate** experiments with before/after
control numbers from two model families. Bundled, neither number is interpretable.

---

## B8 — 🔴 `build_processed_data` could not regenerate its own output

The function that writes `data/processed_data/` — `write_filtered_csvs` — was
**commented out**, together with `save_sampling_rate_artifact` and both calls in
the main block. The stage therefore read the reference driver, computed a report
it threw away, and exited **successfully** having written nothing. The 6.7 GB of
processed data that every result in this project rests on **could not be
regenerated from the committed code**.

Found only because the full re-run wrote zero files. Three functions in this one
module had been commented out while still being referenced or needed
(`get_sampling_rate_hz` in B1, and these two) — the same cleanup that hid
PIPELINE.md sections 3–11.

**Restored** and re-run from raw, with the output verified against the backup of
the previous data.

**Guard added:** the runner now treats a stage that exits zero while leaving a
declared output missing, empty or zero-byte as a **failure**. Exit codes cannot
detect commented-out work; checking the artifacts can.

---

## B7 — Staleness checked that outputs *existed*, not that they matched

Moving `data/processed_data/` aside and leaving an empty directory in its place
made `build_processed_data` report **"up to date"** — the directory existed, so
the missing-output check passed, and nothing compared the directory's contents
against the fingerprint the manifest had recorded. A stage whose 6.7 GB of output
had just been removed was declared fresh.

Fixed: each recorded output is now compared by fingerprint, so an emptied,
truncated or externally overwritten output marks the stage stale
("output changed on disk").

**Third bug of the same family** (with B2 and B4): every one let the system
report "fresh" when it was not. The pattern is that I verified the *presence* of
provenance rather than its *agreement with reality*. Worth stating plainly in the
write-up — the useful lesson from building this is that a provenance system needs
its own adversarial tests, and each of these three was found by accident.

---

## B6 — A sweep referenced a config symbol whose meaning had changed

`window_config_sweep` took its "behavioural" arm from `MVP_CHANNEL_SPNS`. When
finding F1 redefined that symbol to *be* the 62 audited channels, both arms of
the comparison became the same set: the re-run printed "62 behavioural" and
"62 audited" with identical numbers, silently destroying the 8-vs-62 evidence
the conclusion rests on. Fixed by naming `BEHAVIOURAL_8_SPNS` and
`AUDITED_CHANNEL_SPNS` explicitly.

**Rule:** a comparison must name its arms with fixed symbols, never with a
symbol that points at "whatever we currently use". Caught only because the
re-run's table had two identical rows — worth remembering that a re-run can
destroy evidence as easily as reproduce it.

---

## B5 — Fine-tuning was not seeded

The three fine-tuning arms ran without `torch.manual_seed`, so weight
initialisation and batch order differed between runs and the reported numbers
were not reproducible — in a project whose whole point is traceability. Seeded
(42) and re-run. Any arm-to-arm difference smaller than a few points should
still be treated as noise: one test window is 0.4 points, and the pooled metric
moves 2.2 points per driver.

---

## B4 — Bug in this framework: registry parameters duplicated as literals

After D6 removed `src/config.py` from the code fingerprints, the only way a
config change can mark a stage stale is through its recorded `params`. But the
registry held `"output_token": "combined"` as a **literal string** rather than a
reference to `MANTIS_OUTPUT_TOKEN`. Changing the config therefore changed
nothing the detector could see: `embed_mantis`, `enroll_and_score` and
`finetune_mantis` were all skipped as "up to date" while the config said
otherwise. Fixed by referencing the config symbols.

**Rule that follows:** a registry parameter must be *derived* from config, never
retyped. Duplicating a value defeats the mechanism that detects it changing.
Found only because the re-run finished implausibly fast — a reminder to check
that a pipeline did what was asked rather than that it exited zero.

---

## B3 — Library limitation: `MantisTrainer` ignores the adapter when predicting

> **⚑ Narrowed after reading the library:** the crash below is real for `fine_tuning_type="head"`, where `predict_proba` pre-encodes raw channels. With `adapter_head`, `predict_proba` applies the adapter (verified, difference 0.0); `full` takes the same code path but was not run. `transform()` ignores the adapter in every mode, so adapted *embeddings* for our read-outs would still need custom code. The adapter remains untested; it is future work, not impossible.


`fit(..., adapter=...)` sizes the classification head for the adapted channel
count, but `predict_proba` encodes each *raw* channel and concatenates, so the
head receives 62 x 512 = 31,744 features where it was built for 10 x 512 = 5,120
(`RuntimeError: running_mean should contain 31744 elements not 5120`). The
channel adapter is therefore unusable with this trainer's predict path. All
fine-tuning arms run without an adapter — slower, but identical across arms and
not dependent on library behaviour we would have to work around.

---

## B2 — Bug in this framework: staleness ignored changed declarations

When the window length moved from 51 s to 120 s, every stage's declared input
path changed (`windows_51s.npz` → `windows_120s.npz`). Staleness compared only
the paths *recorded in the previous manifest*, which still existed untouched, so
`baseline_window_rf` was skipped as "up to date" while pointing at data it had
never seen, and the stage after it failed on a missing input. Fixed: staleness
now also compares the declared input and output *sets* against the manifest.

**Why this one matters beyond the bug:** a provenance system that can report
"fresh" for a stage whose inputs have been redefined is worse than none, because
it invites trust. Caught here only because a downstream stage failed loudly.

---

## B1 — Bug found in inherited code: `get_sampling_rate_hz` was commented out

`src/data/build_processed_data.py` called `get_sampling_rate_hz` at line 144 while
its definition sat commented out at line 82 — so the stage that produces
`processed_data/` could not run at all (NameError). The existing data on disk dates
from 2026-07-16, i.e. from before the function was disabled. Restored, so the
pipeline is reproducible end to end. No data was damaged: the failure occurred in
the reporting step, before any driver CSV is written.

---

## ⚠️ C1 — The confound this project cannot remove: one drive per driver

**Status: permanent limitation. Must be stated in every write-up and defended, not fixed.**

Each of the 46 usable drivers drove the route **exactly once**, on a different
day. So for every driver, "this person's driving style" and "the conditions of
that particular trip" are the same thing in the data — statistically
**confounded**. There is no split, model or metric that separates them, because
the dataset contains no second session for any driver.

**What this means concretely**

| Claim | Can this dataset support it? |
|---|---|
| "The model distinguishes these 46 drivers" | ✅ Yes |
| "It distinguishes them *by driving behaviour*" | ⚠️ Only as far as the audited signal set allows |
| "It would recognise the same driver on another day" | ❌ No — untestable here |
| "It flags a stranger because they *drive* differently" | ❌ Not separable from "that day looked unfamiliar" |

**Why it bites hardest in the open-set task.** Every held-out "unknown" driver
also drove on an unseen day. A rejection score can therefore fire because the
day is unfamiliar — weather, ambient temperature, fuel level, engine warm-up —
rather than because the person drives differently. Our rejection numbers are an
**upper bound** on genuine behavioural rejection.

**What we do about it (mitigation, not a fix)**

1. **Audited inputs.** Only signals that are driver *actions* or their immediate
   mechanical consequence (pedal, speed, engine speed, demanded and actual
   torque, load, throttle, air flow). The whole thermal / ambient / cumulative
   family is excluded — that family alone was worth ~45 percentage points of
   leaked accuracy in the earlier Random Forest work (99.6% → 29%).
2. **Chronological splits within each driver.** Train on early windows, discard a
   gap, test on late ones, so adjacent near-duplicate windows cannot straddle the
   split.
3. **Say so.** Every results report carries this caveat, and the published
   accuracy is framed as same-session, i.e. an upper bound.

**Evidence from the literature that this matters.** Shin et al. (2025) compared a
model trained on a driver's older session against one trained on the same period
as the test data: accuracy fell from **67–78% (same session) to 33–49% (across
sessions)**. Enev et al. (2016) point the other way — one driver re-recorded on
different roads and days was still identified at **91%**. The field disagrees, and
a single-session dataset cannot settle it.

**What would settle it:** KCID (Kidmose et al., 2025) — 16 drivers, 4 vehicles,
**multiple sessions per driver**. The honest closing line for this work is that
cross-session validation requires a dataset ORNL is not, and KCID is.

---

## Findings that changed the design

### F1 — The binding constraint was channel count, not the model
With 8 channels at 51 s, the frozen encoder scored 11.6% top-1 and expert
aggregates 12.1% — *indistinguishable*. That equality was the clue: when two
completely different representations agree, the limit is upstream of both. The
sweep confirmed it (inner validation, 46-way, random floor 2.2%):

| Channels | Window | Val top-1 | Val pooled |
|---|---:|---:|---:|
| 8 behavioural | 51 s | 7.5% | 21.7% |
| 8 behavioural | 120 s | 11.3% | 21.7% |
| 8 behavioural | 180 s | 12.5% | 17.4% |
| **62 audited** | 51 s | 32.7% | 56.5% |
| **62 audited** | **120 s** | **38.2%** | **56.5%** |
| 62 audited | 180 s | 33.9% | 43.5% |

**Decision D2 is therefore reversed:** use all 62 audited channels, not 8. The
compute saving was real but it cost a factor of five in accuracy. 120 s also
reproduces the earlier Random-Forest window study, which found accuracy still
climbing to ~120 s and flat beyond.

**Methodological point worth keeping:** two very different representations
scoring the same is evidence about the *data*, not the models. It is the cheapest
diagnostic in this project.

### F2 — Open-set rejection by distance is at chance, across five scoring rules

> **⚑ Overturned by D12:** the null came from the scoring (PCA 50). With LDA-based scoring chosen on inner validation, driver AUROC is 0.689 ± 0.043.

On 8 channels / 51 s, every rejection rule gave AUROC 0.52–0.54 (chance = 0.50):
Euclidean and cosine distance to the nearest prototype, the nearest/second-nearest
ratio, Mahalanobis distance with a shared within-driver covariance, and
one-minus-max-probability from a Random Forest. All were calibrated on known
drivers only. A single weak score could be blamed on the score; five cannot.
This is re-measured at the winning configuration before any conclusion is drawn.

## Decisions reached from QC

### QC1 — `canloggerTime` is the master clock
*Evidence: `outputs/reports/canlogger_bridge_report.md`, from
`QC/verify_canlogger_bridge.py`.*

The two clocks in the data come from different sources: `gpsTime` is **satellite
UTC**, which the vehicle cannot influence, and `canloggerTime` is the **CAN
logger's local clock** (MDT for these drives), snapshotted into every GPS row.
Their mean gap of ~21,607 s is therefore a **time zone (6 h), not an error**.

Three measurements decided it:

1. **Shift, not drift.** The offset's standard deviation is 0.023–0.044 s across
   a ~50-minute drive. A constant shift is harmless for alignment — it is the
   same correction everywhere — whereas drift would require a different
   correction early and late in the drive.
2. **The wobble cannot cause a wrong-bin error.** The worst excursion anywhere is
   0.086 s, against a 10 Hz grid whose bins are 0.100 s wide. Every driver's
   wobble is smaller than one sample period, so no reading can land in a
   neighbouring window.
3. **No CAN time column falls outside the GPS window** (62 per driver, 0 out of
   range).

**Decision:** align on `canloggerTime`; use `gpsTime` only to *validate* it.
Never validate one Teensy timestamp against another from the same device — that
is circular, since both would share a fault.

**Caveat carried forward:** the mean offset differs *between* drivers (G1S16 is
~78 s from the rest), so each session has its own constant bias. Within-driver
timing is sound; **absolute timestamps are not comparable across drivers**.

## Decisions made autonomously (2026-10-11 onward)

### D14 — Read-out block: frozen moves to block 1; fine-tuned stays at block 3

**Naming first.** Mantis's `return_transf_layer` is **0-based**: the value 2 used
throughout this project is the output after **block 3 of 6**; -1 is after block 6.
Earlier entries and reports that say "layer 2" mean block 3. Numbers are
unaffected; only the wording was wrong.

**Why it was re-opened.** Block index 2 was the Mantis paper's recommendation
(D10), and exp08 Round 1 compared it only with the final block. The frozen grid
(`experiments/exp06_encoder_readout/rescore_frozen.md`) then reported every block
on test, and closed-set accuracy fell with depth at every window. A choice from a
test table is not allowed, so the comparison was re-run on inner validation.

**Rule, fixed before either run:** switch from block index 2 only if another block
beats it by ≥ 2pp at ≥ 3 of the 4 windows (inner validation).

**Frozen arm** (`experiments/exp08_layer_resampling/layer_profile.md`, 46-way LDA,
inner validation, `mean_token`):

| Block | 30 s | 51.2 s | 90 s | 120 s |
|---|--:|--:|--:|--:|
| **1 of 6 (index 0)** | **30.1%** | **38.5%** | **43.4%** | 38.8% |
| 3 of 6 (index 2) | 26.5% | 33.4% | 38.0% | 36.0% |
| 6 of 6 (final) | 20.3% | 24.1% | 24.8% | 23.6% |

Block 1 wins at 4 of 4 windows (+2.8 to +5.4pp). **Rule met: the frozen arm reads
out at block 1**, and its window is re-chosen on the same inner validation:
**90 s** (43.4%). Block index 2 reproduced exp06 `confirm_token.md` exactly.

**Fine-tuned arm** (`round1.py --layer 0` against Round 1's block-3 cell, 36-way,
inner validation, best read-out):

| Window | block 3 | block 1 |
|--:|--:|--:|
| **30 s** | **47.8%** | 34.7% |
| 51.2 s | 39.9% | 44.2% |
| 90 s | 45.0% | 45.5% |
| 120 s | 38.4% | 45.7% |

Block 1 wins by ≥ 2pp at 2 of 4. **Rule not met: the fine-tuned arm stays at block
3, 30 s.** Block 1 helps where training windows are fewest (120 s) and hurts most
where they are most plentiful (30 s) — consistent with a capacity trade-off, not
tested further.

**The two headline arms, test split:**

| Arm | Block, window | 46-way closed (LDA) | open set, driver AUROC |
|---|---|--:|--:|
| frozen | 1 of 6, 90 s | 44.9% | 0.717 ± 0.069 |
| fine-tuned | 3 of 6, 30 s | 43.1% ± 0.9 | 0.689 ± 0.043 |

Frozen's 46-way number has no ± because nothing in it is random (no training,
deterministic LDA). Every difference between the arms is within one standard
deviation: the claim is **comparable**, not better.

The frozen arm's closed-set number is stable across splits (inner 43.4%, test
44.9%); its open-set number is not (inner 0.611 ± 0.049, test 0.717 ± 0.069).
The fine-tuned arm's open-set number is the steadier of the two (inner 0.678 on
one partition, test 0.689).

**Stated limitation.** The open-set scoring (D12) was selected on fine-tuned
block-3 embeddings. The frozen arm inherits it untuned; a frozen-specific
selection could only hold or raise 0.717.

Supersedes the read-out layer of D10 and exp08 Round 1's "layer 2 stays".

### D13 — Output token: `mean_token`, not `cls_token`

D10 chose `cls_token` with a nearest-centroid read-out on the 62-channel
configuration, closed set only, without testing `mean_token`. exp06
`confirm_token.md` re-ran the choice on inner validation, 46-way, best of three
read-outs: **`mean_token` wins at every window by 7–12pp**; `combined` (twice the
features) never beats it. Reported afterwards on test, not used to choose:

- frozen, open set (`rescore_frozen.md`): `mean_token` best at every window;
- fine-tuned, 30 s (`full_token.md`, pre-registered): `mean_token` best closed set
  on 5 of 5 partitions; open set within noise (`cls_token` 0.713 ± 0.078 against
  0.689 ± 0.043).

Supersedes the token of D10.

### D12 — Open-set scoring chosen on inner validation, by the median, then pre-registered

exp07 Phase C swept 1,300 scoring configurations (10 projections × 5 transforms ×
4 prototypes × 13 rules) on inner validation and chose each setting by its
**median** across all configurations sharing it, not by the single best cell:
LDA projection → L2-normalise → whiten → one mean per driver → cosine distance.
It was written down before any test window was scored.

On test (`experiments/exp07_full_window/phase_c_final.md`), same embeddings:
the earlier scoring (PCA 50, Mahalanobis) gives driver AUROC **0.514**; the
pre-registered one **0.689 ± 0.043**. The sweep's single best inner cell (0.806)
fell to **0.549** on test — choosing by the maximum would have failed.

Supersedes D8 and overturns F2.

### D11 — The best window depends on the arm

On inner validation the frozen encoder prefers long windows (exp06: 90 s best)
while the fine-tuned encoder prefers 30 s (exp07 `phase_a.md`: 47.8%, 2.8pp clear
of 90 s). Fine-tuning is limited by the number of training windows, and 30 s
gives four times as many as 120 s. Each arm uses the window chosen for it.

### D9 — Five rejection rules instead of one
Reporting a single rejection score would have left "the score was badly chosen"
as an unanswerable objection. Five standard open-set rules are now computed, all
from known-driver statistics, and the report shows every one.

### D8 — Features are PCA-reduced (50 components) before distance scoring

> **⚑ Superseded by D12:** open-set scoring now projects with LDA.

Fitted on known-driver training windows only. With ~31,700 embedding dimensions
and a few hundred training windows, raw Euclidean distances concentrate — every
point sits at almost the same distance from every prototype — which alone can
produce a chance-level AUROC.

### D10 — Encoder read-out re-selected after the data configuration changed

> **⚑ Superseded:** the token by D13 (`mean_token`), the read-out block by D14. "Layer 2" below means block 3 of 6 (0-based index 2).

The first selection ran on 8 channels / 51 s and picked layer 2 + `combined`
tokens (the paper's recommendation), by 0.5 points over the library default.
Re-run at the final configuration (62 channels, 120 s) the ranking changed:

| Configuration | Val top-1 | Dims |
|---|---:|---:|
| **Mantis-8M, layer 2, cls** | **21.3%** | 15,872 |
| MantisPlus, layer 1, combined | 20.8% | 31,744 |
| UTICA, layer 2, combined | 20.2% | 31,744 |
| Mantis-8M, layer 1, combined | 18.5% | 31,744 |
| Mantis-8M, final layer, cls (library default) | 17.4% | 15,872 |
| Mantis-8M, layer 2, combined (paper's recommendation) | 16.9% | 31,744 |

The published recommendation came **6th of 8** on our data, and the winner uses
half the dimensions. Read-out choices evidently do not transfer across data
configurations — worth stating, because taking the paper's number on trust would
have cost 4.4 points. Selection stages must be re-run after any change to the
data they select over.

### D7 (superseded by D10) — The frozen encoder uses read-out layer 2 with combined tokens
The library default (final layer, [CLS] only) is the configuration the Mantis
paper explicitly advises against. A sweep of 8 configurations across four
published checkpoints (Mantis-8M, MantisPlus, UTICA, MantisV2) picked
`Mantis-8M, layer 2, combined` on inner validation — though the spread was small
(7.1%–9.1%), so this is a marginal choice, not a decisive one.

### D6 — `src/config.py` removed from every stage's code fingerprint
**The problem it caused:** adding MVP settings to `config.py` marked *every* stage
stale, and the runner then tried to rebuild `processed_data` (6.7 GB, ~1 h) before
building windows. **Why the fix is correct, not a workaround:** the config values a
stage actually depends on are already recorded in its `params`, which staleness
compares. Fingerprinting the whole config file made every stage depend on every
other stage's settings. Now `code` covers only the stage's own modules.

### D5 — Channel swap after measuring variability: 51 → 183
SPN 51 (throttle valve) measured **std/mean = 0.016** across drivers — effectively
constant on this engine, carrying no identity information. Replaced with SPN 183
(engine fuel rate, std/mean = 0.95, 879 distinct values), a fast and direct
consequence of pedal input.
**Brake signals were considered and rejected:** SPNs 117/118/1087/1088 are air
*reservoir* pressures (~792 kPa) that drift as the tank depletes and the compressor
refills — slow session state, not a driver action, so a leakage risk. This is worth
stating in the write-up because Enev et al. (2016) found the brake *pedal* to be the
single most discriminative signal; ORNL's J1939 set exposes tank pressure instead,
so that result cannot be reproduced here.

### D1 — The MVP path skips the 10 Hz master timeline
`build_windows` reads `data/processed_data/` at native rates and resamples each
window to 512 steps directly. **Why:** the encoder resizes its input to 512 steps
regardless, so the master timeline adds a slow stage and an in-place mutation
(PROVENANCE.md defect #1) for no benefit on this path. The timeline stays in the
repo for the legacy feature-matrix comparison.

### D2 — Eight channels, not all ~62 audited signals
SPNs 91 (accelerator pedal), 84 (wheel speed), 190 (engine speed), 512 (driver's
demand torque), 513 (actual torque), 92 (engine load), 51 (throttle valve), 132
(intake air flow). **Why:** the encoder embeds each channel independently and
concatenates, so both compute and embedding width scale linearly with channel
count — 62 channels would give ~15,900 dims against ~1,200 training windows.
These eight are the most direct driver actions and responses in the audited set.
**Revisit if** separability is poor: add channels before concluding the method fails.

### D3 — 51-second windows
512 steps at 10 Hz is the encoder's native input length, so no resizing argument
has to be defended in the MVP. **Trade-off:** the earlier Random Forest work found
accuracy still improving up to 120 s, so 51 s may cost a few points. A window
sweep is a week-2 extension, not part of the MVP.

### D4 — Frozen encoder first, fine-tuning second
**Why:** the frozen pass is cheap and answers RQ1 directly. The EEG and e-nose
studies both found frozen features insufficient on signal types absent from
pre-training, so fine-tuning is expected to be necessary — but measuring the
frozen baseline first makes the eventual gain quantifiable.
