"""Build the capstone proposal deck (15 slides).

Emphasis: proposed work, not the literature survey.
Source of content: outputs/reports/capstone_proposal.md + paper_notes.md

Run from the repo root:
    python scripts/build_proposal_deck.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pptx.util import Inches  # noqa: E402

from deck_style import (AMBER, CHARCOAL, HEAD_FONT, MUTED, TINT_GREY, WHITE,  # noqa: E402
                        blank, bullet_slide, fill, new_deck, table_slide, textbox,
                        three_card_slide, two_card_slide, write)
from paper_slides import add_paper_slides  # noqa: E402

OUT_PATH = Path(__file__).resolve().parent.parent / "outputs" / "lit_survey_deck.pptx"


def build() -> Path:
    prs = new_deck()

    # 1 — title
    s = blank(prs)
    fill(s, CHARCOAL)
    tf = textbox(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(2.4))
    write(tf, "Open-Set Driver Identification", size=44, color=WHITE, bold=True,
          font=HEAD_FONT, space_after=6, first=True)
    write(tf, "from Heavy-Duty J1939 CAN Data", size=44, color=WHITE, bold=True,
          font=HEAD_FONT, space_after=14)
    write(tf, "using Time-Series Foundation Models", size=28, color=AMBER, font=HEAD_FONT)
    tf2 = textbox(s, Inches(1.0), Inches(5.3), Inches(11.3), Inches(1.2))
    write(tf2, "Capstone proposal", size=16, color=TINT_GREY, space_after=6, first=True)
    write(tf2, "Atul Prem Patnala  ·  University of North Carolina Wilmington", size=13,
          color=MUTED, space_after=4)
    write(tf2, "Building on TruckIDMe, IEEE AIMS 2025 (Vienna)", size=13, color=MUTED)

    # 2 — problem I
    two_card_slide(
        prs,
        "Behaviour-based biometrics: a new frontier in driver verification",
        "Who is actually driving this truck — and can we tell without adding hardware?",
        ("CONVENTIONAL VERIFICATION",
         ["Keys, fobs, PINs — verify **once, at login**",
          "Face / fingerprint readers: **invasive** and privacy-sensitive",
          "**Require extra hardware** in every cab",
          "**Vulnerable to spoofing**, sharing and theft",
          "Nothing detects a driver swap **after** the engine starts"]),
        ("BEHAVIOUR-BASED VERIFICATION",
         ["Uses signals the truck **already broadcasts**",
          "**Passive** — verification *during* driving, not just at login",
          "**Privacy-preserving**: no camera, no biometric enrolment hardware",
          "**Harder to spoof** — style is not a credential that can be handed over",
          "**Hardware-free** → deployable across an existing fleet"]),
        notes="Frame the security need first: fleets need continuous verification, not a one-time check.")

    # 3 — problem II
    three_card_slide(
        prs, "Why J1939 CAN data, and what we are asking",
        "The hidden fingerprint inside every commercial truck",
        [("WHY CAN SIGNALS",
          ["The bus carries every pedal press, torque request and brake application",
           "Rich internal dynamics: torque demand, engine load, fuel rate, turbo",
           "Fine-grained behavioural signal at **native rates (10 ms–1 s)**",
           "No extra sensors: no GPS, IMU, camera or phone required"]),
         ("WHY J1939 IS SPECIAL",
          ["**Standardised PGNs / SPNs** across all commercial trucks",
           "Identical signal meaning regardless of manufacturer",
           "**Vendor-agnostic** → scalable to thousands of vehicles",
           "Supports fleet-wide behavioural modelling, not one-car studies"]),
         ("WHAT WE ASK",
          ["Can a truck driver be identified from **CAN behaviour alone**?",
           "And the harder question: can the system recognise a driver it has **never enrolled**?",
           "Fleet need: unauthorised swaps, misuse, tampering, theft",
           "**Closed-set** answers the first. **Open-set** answers the second."])],
        notes="Slide 2 is the motivation; this slide narrows to the research question. The open-set question is the project.")

    # 4 — dataset
    two_card_slide(
        prs, "The dataset: ORNL Driver Identification",
        "Collected by Colorado State University for Oak Ridge National Laboratory",
        ("WHAT IT CONTAINS",
         ["**50 drivers**, 2014 Kenworth T270 (Class 6)",
          "Identical **20-mile / 50-minute** route, Fort Collins CO",
          "CAN-bus (J1939), GPS, IMU, heart rate + scripted cyberattack",
          "Three groups: Control 17 · Aware 16 · Aware+Protocol 17",
          "Native sampling rates, plus a 1 Hz downsampled release"]),
        ("WHAT IT MEANS FOR THIS WORK",
         ["**46 usable drivers** — G1S04 (low CAN rate) and G1S10–12 (clock failure) excluded",
          "The attack hit only the **instrument cluster**, a separate bus → behaviour signals are truthful",
          "Largest driver pool at native CAN rates in the published literature",
          "⚠ **One drive per driver** — identity and trip are confounded",
          "⚠ One vehicle, one route, one city"]),
        notes="Be explicit about the single-session limitation here; it returns in the evaluation design.")

    # 5 — prior work (brief)
    bullet_slide(
        prs, "Prior work: TruckIDMe (IEEE AIMS 2025, Vienna)",
        "Where this project starts — closed-set identification on the same dataset",
        ["**Pipeline:** 1 Hz downsampling → 5 aggregates per signal (min, max, mean, std, median) → sparsity filtering → windowing",
         "**Split:** driver-wise, chronological, with a one-window gap between train and test to prevent temporal leakage",
         "**Selection:** Random-Forest importance ranked 262 columns → top 6 features (>90% cumulative importance)",
         "**Results:** Decision Tree ~94.9% · Random Forest ~0.98 · KNN ~0.994 · MLP ~91.3%; AUC > 0.97",
         "**Its own stated future work:** modern sequence models, better feature selection, behavioural drift and generalisability",
         "**This proposal takes up that future work** — and asks the question the paper could not: what about drivers the model has never seen?"],
        notes="Keep this brief and forward-looking: the prior paper closes on exactly the questions this proposal opens.")

    # 6 — lit 1/3
    table_slide(
        prs, "Literature 1/3 — the data the field relies on",
        "Almost everything published rests on decoded OBD-II at 1 Hz or slower, with few drivers — full inventory of all 25 datasets in the backup slides",
        ["Dataset", "Drivers", "Vehicles", "Data type", "Rate", "Route"],
        [["ORNL (ours)", "46 usable", "1 truck", "raw J1939 → SPNs", "native (10 ms–1 s)", "fixed"],
         ["CIAIR (2007)", "274", "1 van", "speech + video + sensors", "—", "naturalistic"],
         ["KCID (2025)", "16", "4", "raw CAN", "1,000–2,500 Hz", "daily + fixed"],
         ["Hallac (2016)", "64", "10", "real-world sensors", "—", "single turn"],
         ["HCRL (2016)", "10", "1", "decoded OBD-II", "1 Hz", "fixed"],
         ["Barreto 19drivers", "19", "1", "decoded OBD-II", "0.14 Hz", "fixed"],
         ["UK 19 Drivers (2021)", "19", "1", "decoded OBD-II", "1 Hz", "fixed"]],
        col_w=[2.3, 1.1, 1.1, 2.4, 1.9, 1.6],
        notes="Kidmose et al. 2025 make this case: decoded data, low rates, fixed routes, single vehicles, no demographics.")

    # 7 — lit 2/3
    three_card_slide(
        prs, "Literature 2/3 — what has been tried, and what it missed",
        "Four representative studies: strong results, weak evaluation",
        [("FOUNDATIONS",
          ["**Enev 2016** (PoPETs): 15 drivers; the **brake pedal alone** gives 87% from 15 min, 100% from 1.5 h",
           "Decimation to 60 Hz justified by human actuation bandwidth",
           "Fingerprint survives different roads and days (91%)",
           "**Kwak 2017**: 51 → 15 features, statistics per 60 s window, threshold-based verification, >99%"]),
         ("DEEP LEARNING",
          ["**Hu 2023** (IET): CNN + BLSTM ensemble, 20 drivers, 0.96",
           "Augmentation matters most when data is scarce: **+15.2 pts at 1 min** of training data",
           "**Shin 2025**: CAN → images → ResNet-18, continuous retraining",
           "Detects an unregistered driver, but with a softmax over 3 drivers"]),
         ("THE COMMON FLAWS",
          ["10–20 drivers at **1 Hz**, single vehicle, fixed route",
           "**Overlapping windows under random splits** — near-duplicates on both sides",
           "**No leakage audit**: Kwak's top features are transmission oil temperature and fuel trim — values a driver *cannot* control",
           "**Same-session evaluation**: Shin shows 67–78% within a session vs **33–49% across** sessions"])],
        notes="The third card is the argument: published accuracies are inflated by evaluation design, not by better modelling.")

    # 8 — lit 3/3
    three_card_slide(
        prs, "Literature 3/3 — the tools this proposal brings in",
        "Time-series foundation models, cross-domain transfer, and few-shot enrollment",
        [("MANTIS (2026)",
          ["Foundation model built for time-series **classification**",
           "**4.2M parameters** — fine-tunable on a single GPU",
           "Frozen encoder beats larger models: **UCR 0.820** vs MOMENT 0.779",
           "Channel adapters (PCA / linear) for multivariate input",
           "Pre-trained on **purely synthetic** data"]),
         ("DOES IT TRANSFER? (EEG, 2025)",
          ["Fine-tuned Mantis beats **EEGNet** and **CBraMod**, an EEG-specific foundation model",
           "**\"Freezing the encoder leads to a huge decrease\"** → fine-tuning is necessary",
           "Pre-training gains are modest: **+0.3 to +5 points** over random init",
           "Compresses 6,000 samples → 512 and still wins"]),
         ("FEW-SHOT ENROLLMENT (P-AttEnc, 2025)",
          ["Driver = **mean embedding** of a few labelled windows (a *prototype*)",
           "New driver enrolled by storing windows — **no retraining**",
           "This is what makes open-set possible",
           "⚠ Their unknown-driver result (65.7%) is a **2-way** test; chance is 50%"])],
        notes="Mantis is the model, EEG is the transfer evidence, P-AttEnc is the enrollment mechanism.")

    # 9 — gap
    bullet_slide(
        prs, "Research gap", "Five gaps; this proposal addresses the first two directly",
        ["**1 — Open-set is rudimentary.** Thresholds exist (Kwak 2017, Shin 2025) but none is calibrated, none reports a threshold-free metric, none evaluates at scale",
         "**2 — No foundation models have been applied to CAN driver identification.** Evidence exists for UCR/UEA, human activity, EEG and gas sensors — not for vehicle buses",
         "**3 — Leakage is rarely audited.** Cumulative counters, fuel level and thermal state separate drivers perfectly for non-behavioural reasons; almost no study screens for it",
         "**4 — Same-session evaluation inflates results.** 67–78% within a session vs 33–49% across sessions (Shin 2025)",
         "**5 — Multi-rate CAN is never addressed.** J1939 spans 10 ms to 1 s per signal; published datasets arrive pre-aligned at 1 Hz, so the problem is invisible"],
        notes="Gaps 3-5 are methodological and shape the evaluation; gaps 1-2 are the contribution.")

    # 10 — hypothesis
    two_card_slide(
        prs, "Hypothesis and research questions",
        "One hypothesis, four questions, each answerable within the term",
        ("HYPOTHESIS",
         ["Only **~40 minutes of data exist per driver** — too little to train a deep model from scratch",
          "A model **pre-trained on large time-series corpora** should therefore identify drivers more effectively than hand-engineered features",
          "And its embedding space should support **rejecting drivers it never enrolled**",
          "Open question, not an assumption: **no CAN data appears in any pre-training corpus**"]),
        ("RESEARCH QUESTIONS",
         ["**RQ1 — Separability.** Do frozen embeddings separate drivers on audited CAN signals?",
          "**RQ2 — Expert vs generic prior.** Do they beat hand-engineered features under one identical split?",
          "**RQ3 — Open-set.** Can a calibrated rejection rule separate 10 unenrolled drivers from 36 known ones?",
          "**RQ4 — Data efficiency.** How does accuracy decay as labelled data per driver shrinks?"]),
        notes="RQ2 is the scientific core: expert prior versus generic temporal prior under scarcity.")

    # 11 — proposed work 1
    bullet_slide(
        prs, "Proposed work 1/3 — pipeline", "From raw J1939 to model input, with leakage controlled at the front",
        ["**Signal integrity first.** Keep only audited signals: η² (between-driver variance) plus physical reasoning about what each signal measures. Cumulative counters, fluid levels and the thermal/ambient family are excluded as trip-state proxies",
         "**Multi-rate alignment.** Fast signals: mean per 100 ms (decimation with a built-in anti-alias filter). Slow signals: zero-order hold — literally CAN semantics",
         "**Windowing.** Non-overlapping windows; two lengths compared: 51 s (512 steps, the model's native input) and 120 s (resized), where our own accuracy saturates",
         "**Representation.** Mantis embeddings, intermediate layer, [CLS] + mean-token concatenation; PCA channel adapter if the channel count demands it",
         "**Frozen first, fine-tune second** — frozen is a cheap measurement; the EEG and e-nose evidence says fine-tuning will be needed"],
        size=14,
        notes="The audit is the part no prior CAN study does; it is what makes the eventual number believable.")

    # 12 — proposed work 2
    two_card_slide(
        prs, "Proposed work 2/3 — the open-set design",
        "Enrollment by prototype; rejection by distance",
        ("ENROLLMENT (no retraining)",
         ["Each driver is represented by a **prototype**: the mean embedding of their earliest windows",
          "A new driver is added by **storing windows**, not by retraining the model",
          "Query windows are matched to the **nearest prototype**",
          "Mechanism borrowed from prototypical networks (P-AttEnc)"]),
        ("REJECTION (the open-set part)",
         ["A softmax over 36 drivers can never output \"unknown\" — the probabilities always sum to one",
          "So rejection uses a **separate score**: distance to the nearest prototype",
          "Threshold **calibrated on known drivers only** — never on the unknown set",
          "Reported threshold-free as **AUROC**, so the result does not depend on one cutoff"]),
        notes="This is the methodological contribution: calibrated rejection, not a fourth class.")

    # 13 — proposed work 3
    bullet_slide(
        prs, "Proposed work 3/3 — evaluation", "Designed so the numbers survive scrutiny",
        ["**Driver split:** 36 known / 10 unknown, repeated over **5 random partitions** stratified by awareness group, reported as mean ± std",
         "**Temporal split:** within each known driver — train first 70%, **discard a 5% gap**, test last 25%, so train and test cover different route positions",
         "**Metrics:** top-1/2/5 among the 36 known (chance 2.8%) · **AUROC** for known vs unknown · learning curve over enrollment size",
         "**Baselines under the identical split:** our 9-aggregate Random Forest (50% top-1 from 2 min) and Catch22 features",
         "**Central ablation:** the same architecture from **random init**, from the **synthetic** checkpoint, and from the **real-data** checkpoint — the gap between them *is* the value of pre-training"],
        size=14,
        notes="Every prior study we reviewed fails at least one of these; that is the point.")

    # 14 — contributions and risks
    two_card_slide(
        prs, "Expected contributions and risks",
        "What this produces, and what could go wrong",
        ("CONTRIBUTIONS",
         ["First application of a **time-series foundation model** to CAN driver identification",
          "**Open-set evaluation** with a calibrated rejection threshold and AUROC, at 46-driver scale",
          "A **leakage-audited** benchmark on native-rate J1939 — an honest baseline the field currently lacks",
          "A direct measurement of **expert features vs a generic temporal prior** under data scarcity"]),
        ("RISKS AND MITIGATIONS",
         ["**Frozen embeddings may not separate drivers** → fine-tuning budgeted from week 5",
          "**Trip confound**: one drive per driver, so identity and session cannot be fully separated → audited signals + declared as a limitation",
          "**Dimensionality**: ~62 channels × 512 dims vs ~1,200 windows → PCA adapter, regularised head",
          "**Transfer evidence is about signals, not identity** — EEG studies split *by subject*; we do the opposite"]),
        notes="Naming the risks up front is stronger than being asked about them.")

    # 15 — timeline
    table_slide(
        prs, "Timeline — 10 weeks", "22 September → Thanksgiving week (26 November 2026)",
        ["Phase", "Weeks", "Dates", "Deliverable"],
        [["Foundation", "1–2", "22 Sep – 3 Oct", "Audited windowed tensor; environment + Mantis running; frozen embeddings extracted"],
         ["Separability + baselines", "3–4", "6 – 17 Oct", "RQ1 measured (KNN / nearest-centroid, t-SNE); RF and Catch22 baselines on the identical split"],
         ["Open-set", "5–6", "20 – 31 Oct", "Prototype enrollment, rejection score, AUROC over 5 partitions (RQ3)"],
         ["Fine-tuning + efficiency", "7–8", "3 – 14 Nov", "Random vs synthetic vs real ablation (RQ2); learning curve over enrollment size (RQ4)"],
         ["Analysis + write-up", "9–10", "17 – 26 Nov", "Ablations, error analysis by group, figures, final report and defence slides"]],
        col_w=[2.0, 0.9, 2.0, 7.0], row_h=Inches(0.72), body_size=11,
        notes="Week 4 is the decision point: if frozen embeddings separate drivers, weeks 7-8 become extensions; if not, they become fine-tuning.")

    # ── Backup slides (not part of the 15) ──────────────────────────────
    s = blank(prs)
    fill(s, CHARCOAL)
    tf = textbox(s, Inches(1.0), Inches(3.0), Inches(11.3), Inches(1.6))
    write(tf, "Backup slides", size=40, color=AMBER, bold=True, font=HEAD_FONT,
          space_after=10, first=True)
    write(tf, "One slide per reviewed paper — for questions, not for the talk",
          size=15, color=TINT_GREY)
    s.notes_slide.notes_text_frame.text = "Delete from here onward if the deck must be exactly 15 slides."
    add_paper_slides(prs)

    table_slide(
        prs, "Backup — public driver-identification datasets",
        "Every public dataset named across the ten reviewed papers",
        ["Dataset", "Drivers", "Vehicles", "Data type", "Rate", "Sessions"],
        [["ORNL (ours)", "50 → 46 usable", "1 truck", "raw J1939 → SPNs", "native 10 ms–1 s", "1"],
         ["CIAIR (Nagoya)", "274", "1 van", "speech + video + sensors", "—", "multiple"],
         ["KCID (2025)", "16", "4", "raw CAN", "1,000–2,500 Hz", "multiple"],
         ["HCRL / OCSLab (2016)", "10", "1", "decoded OBD-II", "1 Hz", "2 round trips"],
         ["Barreto dailyRoutes (2018)", "14", "14", "decoded OBD-II", "0.14 Hz", "daily"],
         ["Barreto 19drivers (2018)", "19", "1", "decoded OBD-II", "0.14 Hz", "fixed route"],
         ["AEGIS (2019)", "3", "1", "decoded OBD-II + GPS", "20 Hz", "not stated"],
         ["This Car is Mine! (2019)", "4", "1", "decoded OBD-II", "1 Hz", "fixed route"],
         ["UK 19 Drivers (2021)", "19", "1", "decoded OBD-II", "1 Hz", "~32 min/driver"],
         ["Vehicular data trace", "10", "—", "CAN-bus", "not stated", "36 journeys"],
         ["hciLab driving", "10", "—", "GPS + accelerometer", "not stated", "0.5 h total"]],
        col_w=[2.6, 1.3, 1.1, 2.5, 1.7, 1.6], row_h=Inches(0.4), body_size=10,
        notes="Only KCID and ORNL avoid decoded OBD-II. Only ORNL has a single session per driver.")

    table_slide(
        prs, "Backup — private and simulator datasets in the literature",
        "Cited inside the reviewed papers; originals not read (secondary sources)",
        ["Study", "Drivers", "Data", "Reported result", "Type"],
        [["Hallac et al. (2016)", "64", "real-world sensors, 10 vehicles", "76.9% (2 drivers) → 50.1% (5)", "private"],
         ["Lestyán et al.", "33", "raw CAN, 8 vehicles", "RF re-identification", "private"],
         ["Dong et al. (ARNet)", "50", "GPS", "40.4% top-1 / 78.3% top-5", "private"],
         ["Enev et al. (2016)", "15 (+1)", "stock sensors, 60 Hz", "100%; stability 91% across days", "private"],
         ["Rahim et al.", "25", "CAN events", "95.89% (RF)", "private"],
         ["Sánchez et al.", "25", "acceleration → 2-D", "71.89% top-1", "private"],
         ["Jeong / Xun et al.", "20", "CAN", "CNN", "private"],
         ["Hu et al. own (2023)", "20", "8 CAN signals", "0.96 (ensemble)", "private"],
         ["Choi et al.", "9", "CAN", "31.45% (HMM)", "private"],
         ["Shin et al. own (2025)", "3 + 1 intruder", "~300 CAN columns, 1 Hz", "67–78% same-session", "private"],
         ["Wakita et al.", "30", "simulator, guide vehicle", "73%", "SIMULATOR"],
         ["Zhang et al.", "20", "simulator, multi-day sessions", "85% (HMM)", "SIMULATOR"],
         ["Lee et al. (2022)", "7", "simulator", "+19.94% over CNN", "SIMULATOR"]],
        col_w=[2.3, 1.2, 3.2, 3.0, 1.2], row_h=Inches(0.38), body_size=10,
        notes="Flag the simulator rows when comparing: participants reported the simulator imitated braking poorly (Enev).")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    print(f"wrote {build()}")
