# Understanding log

A running record of the user's reasoning during the project: the checkpoint
question asked, the user's answer, and an honest assessment (correct / imprecise
/ missing). Purpose: track how understanding builds, and revisit gaps later.

---

## 2026-07-30 — Why we investigated SPN 2979 / 3030 / 5052 (leakage)

### Checkpoint 1 — why is a trip/state signal dangerous but pedal position safe, and what does "one drive per driver" have to do with it?

**User's answer:**
> Leakage in any way is dangerous, and we have only one drive per driver, so we
> don't have enough data to isolate whether the characteristic is produced by the
> driver or by the signal itself.

**Assessment:**
- ✅ **Got the crux.** One drive per driver ⇒ a driver's *style* and the *trip's*
  fingerprint are **confounded (entangled)** — you cannot separate them from the
  data alone. This is exactly why the methodology forbids using accuracy to judge
  leakage.
- ⚠️ **Terminology to fix:** it's not "driver vs the *signal itself*" — it's the
  driver's **style** vs the **trip's** fingerprint (route/weather/vehicle-state of
  that single drive). The signal doesn't *produce* the characteristic; the trip
  does. The signal is just the *channel* through which either can show up.
- ❗ **Gap (the next thing to see):** the "can't isolate" confound applies to
  **every** signal equally — pedal position has it too. So "not enough data" can't
  be what makes odometer dangerous and pedal safe. If the data alone can't
  separate style from trip, what *can*? → (a) physical reasoning about what the
  signal measures, and (b) η² / overlap. That's the setup for T4.

**Status:** partial — core insight correct; follow-up posed to close the gap.

### Checkpoint 2 — what makes pedal safe and odometer a leak, if not amount of data?

**User's answer:**
> They are cumulative signals / signals that maintain state even though drivers
> change; these signals don't have the variability among themselves to be
> differentiated among drivers.

**Assessment:**
- ✅ **Physics half correct.** "Cumulative / maintains state regardless of driver"
  is exactly the physical-reasoning tool — a counter's between-driver differences
  can't be style.
- 🔴 **Statistics half is backwards.** Said cumulative signals *can't* differentiate
  drivers. Truth is the opposite: the odometer differentiates drivers **perfectly**
  (46 non-overlapping boxes, η² ≈ 1.0) — and that *perfect separation for a
  non-style reason* is precisely what makes it a leak. A leak has *too much*
  separating power, not too little. Pedal overlaps heavily → η² ≈ 0.01 → safe.
- **The rule to internalise:** η² (does it separate drivers?) flags a suspect;
  physics (does that separation make behavioural sense?) convicts or acquits.
  Both, never accuracy.

**Status:** half-right — physics correct, η² direction flipped; Checkpoint 3 posed
to test the flip.

### Checkpoint 3 — does η²≈0.95 prove a leak? If not, what's the one more thing?

**User's answer:**
> High η² doesn't mean a signal leaks — it's just a flag. We confirm it leaks if
> its RF feature-importance far outweighs the other features; then we conclude it
> leaks.

**Assessment:**
- ✅ **Part 1 correct** — high η² is a flag, not proof. The flip from Checkpoint 2
  has stuck.
- 🔴 **Part 2 — the cardinal-rule error.** Chose **RF feature importance** as the
  confirmer. Importance is a **model output** → same forbidden family as accuracy;
  the #1 rule is never judge leakage by model performance. Worse, it *can't* work:
  a leak and a genuine-style feature **both** rank high in importance, so it can
  never distinguish them (circular — the compromised model policing itself).
- ✅ **The right "one more thing" = physics.** Reason about what the signal
  *measures*: coolant temp (η²=0.95) is thermal state (ambient + runtime), not an
  action → leak. (Real: thermal/ambient family ≈ 45 pp of leakage.)
- **Correct role of importance:** the *spotlight* (which high-η² features to
  inspect first), never the *verdict*. Right character, wrong job.
- **Rule, complete:** η² flags → **physics** convicts/acquits → never model output.

**Status:** part 1 solid; part 2 was the key misconception (model-output to judge
leakage) — corrected. Checkpoint 4 posed to test that physics, not importance, is
the confirmer.

### Checkpoint 4 — two features tied for #1 importance (coolant vs brake-abruptness); can importance pick the leak?

**User's answer:**
> Both η² and importance tell me which features to focus on next, but the final
> call to in/exclude is the physics part. So Feature A (coolant) is excluded —
> physics says it encodes information not actuated by the driver.

**Assessment:**
- ✅ **Core mastered** — physics is the decider; importance cannot pick the leak;
  coolant excluded for the right reason.
- ⚠️ **Sharpened:** don't lump η² with importance. **Importance = model output
  (spotlight only). η² = the leakage detector itself, and it's allowed precisely
  because it's model-independent** (computed from raw values + driver labels, no
  classifier → can't be contaminated by the leak). Importance is circular because
  the model producing it is already exploiting the leak.
- ✅ **Implicit half confirmed:** Feature B (brake abruptness) **stays** — same
  η²≈0.9, opposite verdict, because physics says it's a driver action → genuine
  style. Two identical flags, opposite fates, decided by physics = the method in
  one image.

**Status:** method mastered; η²-vs-importance distinction sharpened. Checkpoint 5:
apply it to the actual signals (3030/5052/2979).

### Checkpoint 5 — given η²≈0.01, what's the verdict + did physics vote? And if η² didn't flag them, what did?

**User's answer:**
> Their characteristics (cadence/mode vs median) don't agree, and the signals
> logged off between drivers, which meant they could leave a fingerprint with
> this characteristic.

**Assessment:**
- ✅ **Got the reorganizing insight:** it was the **sampling-rate characteristics**
  (dropout / mode≠median) that flagged these three, **not η²**.
- ⚠️ **Stopped at the hypothesis.** "Could leave a fingerprint" is the *reason we
  investigated*, not the verdict. Missed that we then **tested and REFUTED** it —
  both the presence-pattern (T1–T3: present ~100%, distributed thinning) and the
  values (T4: η²≈0.01). The "could" was disproved.
- ⚠️ **Skipped the verdict (Q1):** low η² → **KEEP**, and — the elegant part —
  **physics never voted**, because low η² is a complete alibi by itself (nothing
  separates drivers → nothing to leak; physics only matters in the η²-high rows).
- ✅ **Kicker (implicit):** the rate flag was a sampling *artifact*, not a leak
  indicator; T1–T3 chased a false lead (legitimate due diligence); η² was decisive.
- **Minor precision:** for 3030/5052 the disagreeing stat was **mean** (dropout);
  for 2979 it was **mode≠median** (multi-rate).

**Status:** reconstructed the flag-source correctly; key remaining gap was
suspicion≠verdict and "low η² acquits without physics." Corrected + full
end-to-end synthesis given. Method understood.

---

## Topic: Why time-series foundation models? (capstone proposal, 2026-09-15)

### Checkpoint 1 — what problem does a pre-trained TSFM solve here that RF / a from-scratch CNN doesn't?

**User's answer:**
> TSFMs are pre-trained on time-series data and driver classification from CAN
> seemed the perfect application; also we don't have enough data per driver
> (~40 min × 50 drivers). I don't want to engineer features because that
> introduces subject-matter-expert bias — minimal pre-processing, little feature
> engineering, pass the headache to the model.

**Assessment:**
- ✅ **Data scarcity is the right core justification.** ~40 min/driver ≈ 24k
  steps at 10 Hz ≈ ~47 non-overlapping 512-step windows ≈ ~33 train windows per
  driver after a 70% chronological split — genuinely few-shot. Pre-trained
  representations reduce sample complexity; that is the defensible argument.
- ⚠️ **"Time series → perfect fit" is a surface match.** Time series is a data
  *type*, not a domain. Pre-training corpora (weather, energy, ECG, traffic)
  contain no CAN data; what transfers is generic temporal structure. Whether
  that captures driver micro-behaviour (throttle/torque modulation rate) is the
  empirical question — which is what makes it a hypothesis, not a given.
- ⚠️ **Scarcity has two halves; pre-training fixes only one.** Few minutes per
  driver (fixable by transfer) AND one session per driver (trip ≡ driver). The
  second is a confound, not a sample-size problem — no pre-trained prior removes it.
- ⚠️ **"No features = no bias" is not quite right.** Bias doesn't disappear, it
  moves: pre-trained weights are an inductive bias from the pre-training corpus.
  With scarce data, bias is *useful* (bias–variance). Reframe: **expert prior
  (hand features + RF) vs. generic temporal prior (TSFM)** — a clean, testable
  research question.
- ⚠️ **Must distinguish feature engineering from data validity.** How to
  *represent* behaviour can be delegated to the model; what must *not be in the
  input* (cumulative counters, fuel level, ambient/thermal state) cannot. The
  model takes the easiest path — earlier leaky RF hit 99.6%. The η² leakage audit
  is scientific control, not SME feature bias.

**Status:** motivation sound (scarcity + representation learning); gaps are
transfer-as-assumption, session confound, and conflating the leakage audit with
feature-engineering bias. Checkpoint 2: what stops a TSFM on minimally-processed
CAN from identifying the trip instead of the driver?

### Checkpoint 2 — a TSFM hits 95%: what would you check to know it identified the driver, not the trip?

(Needed re-explaining: one drive per driver ⇒ "driver" and "that day's trip" are
the same label; analogy = one exam per student, each on different-coloured paper.)

**User's answer:**
> Make sure input features are not leaking identity in any way — go through the
> features and eliminate based on whether they contribute to leakage. Since these
> models sort of understand the domain of our data, we will use the majority of
> driving data for testing.

**Assessment:**
- ✅ **Right instinct:** screen inputs for leakage *before* training — consistent
  with the Stage-1 audit.
- ⚠️ **Imprecise:** "contribute to leakage" must be judged by η² + physics on raw
  values (model-independent), never by whether accuracy moves.
- ⚠️ **Answered "before", not "after".** Pre-screening is necessary, not
  sufficient. Post-hoc checks on a suspicious 95%: chronological split with gap
  (does accuracy survive?); ablate suspect families (thermal/ambient/levels) and
  retrain; compare to RF on identical audited channels (a huge unexplained gap is
  itself a red flag).
- ❌ **Misconception 1 (carried over from Checkpoint 1):** TSFMs do **not**
  "understand our domain" — no CAN data in their pre-training corpora.
- ❌ **Misconception 2:** pre-training cannot tell the model *which person* is
  G2S07 — it has never seen these 46 drivers. A classification head must still be
  trained on each driver's labelled windows (closed-set ID has no zero-shot).
  What pre-training *can* do is need **fewer** labelled windows. Correct version of
  the idea = a **learning curve**: fixed test set (last 25% of each drive), vary
  training fraction (e.g. 10/25/50/70%), compare how fast TSFM vs RF degrade.

**Status:** leakage instinct solid; "domain understanding" belief and
"test-heavy split" need correcting. Reframed into the learning-curve experiment.
Checkpoint 3: if the TSFM never saw G2S07, where does it learn which windows are G2S07's?

### Checkpoint 3 — if the TSFM never saw G2S07, where does it learn which windows are G2S07's?

**User's answer:**
> If the model has never looked at a driver, how can it identify him? The TSFM
> will model/fingerprint each driver as unique behaviour, then we test. I want the
> TSFM to fingerprint driver windows uniquely by itself — following the approach
> of the prototypical-encoder paper (P-AttEnc).

**Assessment:**
- ✅ **Correct direction — and a better design than a closed-set classifier.**
  Prototypical / metric learning: encoder → embedding per window; driver
  prototype = mean embedding of that driver's support windows; classify a query
  window by nearest prototype. This is the right family for scarce data and
  unseen drivers.
- ⚠️ **"Never looked at" needs precision.** Even for *unknown* drivers, P-AttEnc
  needs K labelled **support (enrollment) windows** from that driver to build the
  prototype. "Unseen" = not used to *train the encoder*, not "zero data from that
  driver". The answer to the checkpoint: G2S07's identity lives in the prototype
  built from G2S07's enrollment windows.
- ❌ **"By itself" is not what P-AttEnc does.** Its encoder is trained
  episodically with driver labels (Eq. 6, negative log-probability over
  prototype distances). That supervised loss is what pulls same-driver windows
  together. A *frozen* generic TSFM has no such objective — its embeddings group
  by whatever varies most (likely road situation / speed regime on a shared
  route), not by person. Whether frozen embeddings separate drivers is exactly
  the testable hypothesis.
- **Critical reading of P-AttEnc (for the lit survey):** 10-driver datasets;
  30 s windows with 50% overlap + 80/20 split + 5-fold CV (overlapping windows can
  straddle train/test → temporal-adjacency leakage); no leakage audit; the
  "unknown drivers 65.7% (1-shot)" result is a **2-way** test where chance = 50%;
  Experiment I's test drivers were in the training data. Useful method, weak
  evidence.

**Status:** converged on the right design family (few-shot prototypes with
enrollment). Remaining gap: frozen-vs-trained encoder — "fingerprints by itself"
is an assumption to test, not a property. User reading EEG → Mantis → MOMENT
(resume ~2026-09-16). Checkpoint 4: in P-AttEnc, what makes same-driver windows
land close together?

### Checkpoint 4 (user clarified plan instead of answering directly)

**User's statement:**
> My assumption: feed driver data episodically to the TSFM, it constructs
> prototypes, then test. Are you saying a frozen FM can't do that? Maybe 36 of 46
> drivers known to the model, 10 unknown — solve it as open-set, not closed-set.

**Assessment:**
- ⚠️ **Conflated two things: *building* prototypes vs *learning from* episodes.**
  A frozen model CAN build prototypes (a prototype is just a mean embedding — no
  training). What it can't do is *learn* from episodes: with frozen weights every
  episode yields identical embeddings, so "episodic training" is a no-op. Episodes
  only matter if something has trainable weights.
- ✅ **Resolution that keeps the user's plan and fits one month:** precompute
  frozen TSFM embeddings once → train a *small projection head* episodically
  (prototypical loss) on known drivers. Frozen-prototype result (no head) falls
  out for free as the "by itself" reference.
- ✅ **36 known / 10 unseen is the right instinct** — tests generalisation to
  drivers the encoder never trained on. Also resolves the documented finding that
  leave-drivers-out gives 0% for a closed-set classifier: enrollment prototypes
  make unseen-driver evaluation meaningful.
- ⚠️ **Terminology: this is NOT open-set.** It is few-shot identification of
  *novel* drivers — still closed-set at test time (every query belongs to some
  enrolled driver). Open-set = queries may come from a driver who was *never
  enrolled* and the model must reject ("none of these") — the anti-theft/KCID
  framing. Nearest-prototype always picks someone → open-set needs a distance
  threshold.
- ⚠️ **Missing from the split:** one 36/10 partition is high-variance (depends
  on which 10) → repeat over several random partitions, stratified by G1/G2/G3;
  within unseen drivers, enrollment windows early / query windows late with a gap;
  report 10-way (chance 10%), not 2-way.

**Status:** plan essentially right; corrected frozen-vs-trainable and
few-shot-vs-open-set. Checkpoint 5: a never-enrolled driver takes the truck —
what does nearest-prototype output, and what must be added for true open-set?

### Checkpoint 5 (user asked clarifying questions; question was unclear)

**User's questions:**
> Can these models be used as feature extractors? If I get embeddings from a
> frozen model, do I need to train on them — can't I just do KNN or SVM? Where
> does episodic learning come in? I'll train on 36 drivers, test the other 10 and
> see if the model differentiates among them and the trained drivers — open-set,
> right? What is enrollment? Didn't understand the question.

**Assessment:**
- ✅ **Good simplifying instinct — user was right, I over-complicated.** Frozen
  TSFM = feature extractor; embeddings = automatically extracted features. KNN /
  nearest-centroid on them is the correct *first* step (KISS). Episodic head is
  only a fallback if frozen embeddings don't separate drivers.
- ⚠️ **Missed distinction: SVM vs KNN for unseen drivers.** An SVM trained on 36
  drivers has exactly 36 outputs — it can never name driver 37. KNN /
  nearest-centroid just stores labelled embeddings, so a new driver is added by
  storing theirs — no retraining. That is *enrollment*.
- ⚠️ **"Differentiate among them and the trained drivers" merges two tasks:**
  (a) tell the 10 new drivers apart from each other → needs enrollment → few-shot
  identification, not open-set; (b) flag the 10 as "not any of the 36" → open-set
  → needs a rejection rule (distance threshold), no enrollment of the 10.
- Checkpoint question re-explained with the phone face-unlock analogy.

**Status:** conceptual picture now simpler and correct: feature extractor → KNN;
enrollment = storing a new driver's labelled embeddings; open-set = rejection.
Pending: user picks task (a), (b), or both.

### Checkpoint 6 — which task? (re-asked as two stories: "new employee" vs "thief")

**User's choice:** **B — open-set ("unknown driver").** 36 known drivers; the 10
held-out drivers are never enrolled and must be flagged as "not one of mine".

**Assessment (issues to raise before this goes in the proposal):**
- ⚠️ **Open-set recognition has two parts, not one:** identify the 36 known
  drivers (closed-set, needs its own chronological train/test within each known
  drive) AND reject the unknowns. Report both.
- ⚠️ **Rejection threshold must not be tuned on the 10 unknowns** (that leaks the
  test set). Use pseudo-unknowns from the known pool for validation, or report the
  threshold-free AUROC.
- ❌ **Biggest risk — trip confound gets worse in open-set.** Every unknown driver
  also drove on a different *day*. A detector can flag "unknown" because the
  weather/fuel/engine state is unfamiliar, not because the behaviour is. With one
  drive per driver, "new driver" and "new trip" are inseparable in this dataset.
  Mitigations: audited 40-SPN channels; state as a limitation; KCID (multiple
  sessions per driver) is exactly why this matters.

**Status:** choice made (open-set). Checkpoint 7: if the system flags a stranger
as "unknown", how do you know it detected a new *driver* and not a new *day*?

### Checkpoint 7 (user reasoned about embeddings instead)

**User's reasoning:**
> I can access the model's embedding space, but we don't know for certain drivers
> will be easily differentiated there — hence we train a classifier on top of the
> embeddings. I want the model to differentiate among the 36 known AND separate
> known from the 10 unknown: pure open-set.

**Assessment:**
- ✅ **Correct epistemics:** separability of frozen embeddings is unknown a priori
  — it is an empirical question.
- ⚠️ **"Hence train a classifier" skips a step:** *measure* first (KNN accuracy /
  nearest-centroid on known drivers, t-SNE/UMAP) — cheap, no training, and it
  directly answers "do they separate?". Then add a trained head only if needed.
- ⚠️ **A classifier trained on 36 solves only half of open-set.** It learns
  directions that separate the 36, but nothing forces the 10 unknowns to land
  *away* from them; a softmax head has 36 outputs and is typically over-confident
  on unseen classes. Rejection needs a separate score (max-softmax threshold,
  distance to nearest centroid) evaluated with AUROC.
- ✅ **Task definition now precise:** open-set recognition = closed-set ID of 36
  known + rejection of 10 unknown.

**Status:** reasoning sound; gap = classifier-for-separation ≠ classifier-for-
rejection. Checkpoint 8: a 36-class classifier receives a window from unknown
driver #40 — what does its output look like, and why is that a problem?

### Checkpoint 8 — a 36-class classifier gets a window from stranger #40: what is its output, and why is that a problem?

**User's answer:**
> The model is predicting wrong — it predicts the driving style matches G2S07,
> it's getting confused, which is what we don't want. No, probabilities can never
> show "none of these".

**Assessment:**
- ✅ **Correct, and for the right reason.** A softmax over 36 classes always sums
  to 1, so "none of these" is not in its vocabulary. The stranger is forcibly
  assigned to the nearest known identity, often with high confidence.
- ✅ **Follows through to the design consequence:** open-set therefore needs a
  *rejection score* outside the class probabilities (distance to nearest
  prototype/centroid, or max-softmax with a threshold), evaluated by AUROC.
- Minor: "predicting wrong" is right, but the sharper framing is that the model
  is *incapable* of being right here — no output of the network can express
  "unknown".

**Follow-up questions raised by user (answered):**
1. *Does "univariate pre-training" mean Mantis can't do multivariate?* No. Mantis
   is pre-trained on single-channel series and at inference encodes **each channel
   independently**, concatenating embeddings (Mantis §3.1, VERIFIED). So it handles
   multivariate input, but cross-channel interaction is only modelled by the
   downstream classifier, never inside the encoder. EEG evidence: channel-independent
   Mantis still beat multivariate CBraMod.
2. *Feature extractor vs zero-shot vs fine-tune?* True zero-shot is impossible for
   identity (labels are required to attach a name). Staged answer: (1) frozen
   feature extractor + simple classifier — this IS what the papers call "zero-shot
   feature extraction" — to measure separability cheaply; (2) fine-tune Mantis only
   if step 1 is weak, which EEG/E-nose evidence suggests is likely.

**Status:** open-set mechanics understood. Checkpoint 9: with ~62 channels ×
~512 dims per channel and only ~1,200 training windows, what goes wrong?

### Checkpoint 9 — more features than training examples: what goes wrong, and the simplest fix?

**User's answer:**
> Overfitting happens, and we need some kind of adapter work on the original
> feature set.

**Assessment:**
- ✅ **Overfitting: correct.**
- ✅ **"Adapter" instinct is right — and it is literally what Mantis does**
  (Appendix C.2, VERIFIED): a channel-level adapter `a: R^d → R^d_new` prepended
  *before* the encoder, mixing d channels into d_new = 10. Two variants: **PCA**
  (unsupervised, first min(10,d) components) and **Linear** (trainable layer).
  Adapters improved accuracy on all 10 UEA multivariate datasets tested (e.g.
  Handwriting 0.281 → 0.514 Linear; EigenWorms 0.814 → 0.863 PCA).
- ⚠️ **Two different reductions, don't conflate:** (1) channel adapter reduces the
  *number of input channels* before the encoder (also restores some cross-channel
  modelling); (2) PCA / L2-regularised classifier on the *concatenated embeddings*
  reduces the final feature count. With ~10 audited signals, d≈d_new so (1) buys
  little — (2) is the relevant lever.
- Note (VERIFIED, Mantis C.2): the authors argue gains from modelling
  cross-channel relationships "do not appear significant", citing Chronos-2 Fig 4a.

**User's follow-up questions (answered):**
- *Can it ingest only one channel at a time?* It loops over channels internally —
  you feed all signals; the encoder just never sees two at once (interaction only
  at the head).
- *Only 512 numbers at a time?* 512 = length of ONE window per channel, not a cap
  on total data. 40 min @ 10 Hz = ~24k steps → many windows. Mantis resizes any
  window to 512; a 120 s window (1,200 steps) compresses to ~4.3 Hz effective —
  still above the ~1 Hz pedal-control band (Feng 2016), so acceptable; a 51 s
  window fits natively.

**Status:** overfitting + adapter reasoning sound. Checkpoint 10: which window
length to try first — 51 s (fits 512 natively) or 120 s (resized, matches the RF
saturation point)?
