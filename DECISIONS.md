# Decisions log

Every judgement call made while building this project, with the reasoning and
who made it. Written so the work can be reviewed end to end rather than taken
on trust. Newest first within each section.

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

### D9 — Five rejection rules instead of one
Reporting a single rejection score would have left "the score was badly chosen"
as an unanswerable objection. Five standard open-set rules are now computed, all
from known-driver statistics, and the report shows every one.

### D8 — Features are PCA-reduced (50 components) before distance scoring
Fitted on known-driver training windows only. With ~31,700 embedding dimensions
and a few hundred training windows, raw Euclidean distances concentrate — every
point sits at almost the same distance from every prototype — which alone can
produce a chance-level AUROC.

### D10 — Encoder read-out re-selected after the data configuration changed
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
