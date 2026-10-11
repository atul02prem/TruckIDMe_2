"""Per-paper "their POV vs my POV" slides.

Used as backup/appendix slides in the proposal deck, and standalone as a
detailed literature deck. Content source: outputs/reports/paper_notes.md
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deck_style import new_deck, two_card_slide  # noqa: E402

PAPERS = [
    dict(
        n=1, title="Lanigan et al. (2025) — the dataset",
        venue="Journal of Transportation Security · peer-reviewed",
        theirs=["50 drivers, one 20-mile / 50-minute route, Fort Collins; 2014 Kenworth T270",
                "3×2 design: awareness (Control / Aware / Aware+Protocol) × experience",
                "Cyberattack mid-route: needles to zero, all warning lights, 2 Hz tone",
                "**Instrument cluster only** — no control system affected",
                "Awareness alone is not enough: stop rate 9% → 30% → **100%**",
                "Reaction time 30.3 s → 16.1 s → **7.5 s** with a response protocol"],
        mine=["SOPs matter: awareness **plus** explicit instructions",
              "The attack never touches J1939 → **our behaviour signals are truthful**",
              "**One drive per driver** → driver and trip are confounded",
              "G3's 100% stop rate may explain why G3 is hardest to classify — the protocol **homogenises** behaviour",
              "A window overlapping the attack could leak **group**, not identity"],
        notes="Our data source, but its research question is human factors, not identification."),
    dict(
        n=2, title="Kidmose et al. (2025) — KCID",
        venue="arXiv preprint · dataset review + new raw-CAN dataset",
        theirs=["Reviews 6 public driver-fingerprinting datasets",
                "Frames driver authentication as **anti-theft defence-in-depth**",
                "**All public sets are decoded OBD-II**, mostly ≤ 1 Hz (Barreto: 0.14 Hz)",
                "Raw CAN wins on **coverage, temporal resolution, fidelity**",
                "Costs: **noise** and **interpretability**; Bluetooth adds latency and packet loss",
                "Five gaps: decoded data · low rates · **fixed routes** · single vehicle · no demographics"],
        mine=["Justifies our data choice: native rates, more drivers than any set they review",
              "Their \"filter the noise\" advice **is our leakage audit**, done more rigorously",
              "Two criticisms land on us: **fixed route, single vehicle** — declare both",
              "They never say \"open-set\" and never claim saturation → the framing is **ours to argue**",
              "ORNL is absent from their review — an under-used resource"],
        notes="Cite for motivation, not for the open-set framing itself."),
    dict(
        n=3, title="Enev et al. (2016) — the foundational result",
        venue="Proceedings on Privacy Enhancing Technologies · peer-reviewed",
        theirs=["15 drivers, one 2009 sedan; parking-lot maneuvers + 50-mile open-road loop",
                "**Brake pedal alone**: 87.3% from ~15 min, **100%** from 1.5 hours",
                "All sensors → 100% on open road; accelerator pedal alone only 18–31%",
                "Quadratic interpolation + **decimation to 60 Hz**, justified by Nyquist",
                "**Fingerprint stability**: same driver, different roads and days → 91%"],
        mine=["A single direct-action signal can carry identity → **channel choice beats channel count**",
              "**Free driving beats prescribed maneuvers** (50% vs 87–100%)",
              "We improve the order: filter **before** decimating; they denoise after",
              "Their stability result **contradicts** Shin's drift finding",
              "They scale using **test** data — a leak we will not copy"],
        notes="Everything else in the field builds on this paper."),
    dict(
        n=4, title="Kwak et al. (2017) — Know Your Master",
        venue="arXiv preprint · origin of the HCRL / OCSLab dataset",
        theirs=["10 drivers, KIA Soul, 23 km in Seoul, **1 Hz OBD-II**, two round trips each",
                "51 features → **15** by InfoGain ranking; min–max scaling",
                "**mean / median / std per 60 s window** → DT, RF, KNN, MLP",
                "Statistical features are the win: MLP 0.747 → **0.964**",
                "Verification by **threshold (0.97)** → alert the owner",
                ">99% on all road types; parking lot lowest"],
        mine=["Their top features are **transmission oil temperature** and **long-term fuel trim**…",
              "…praised precisely because **\"the driver cannot manipulate these data\"**",
              "That is the error we correct: if it can't be manipulated, it isn't **behaviour**",
              "60 s windows stepping **1 s** + 10-fold CV → near-duplicates across every fold",
              "Thresholded rejection exists since 2017 → our contribution is **calibration, AUROC, scale**"],
        notes="The clearest published example of the leakage problem our work addresses."),
    dict(
        n=5, title="Hu et al. (2023) — ensemble deep learning",
        venue="IET Intelligent Transport Systems · peer-reviewed",
        theirs=["**M 1-D CNN + BLSTM** bagging ensemble; 20 drivers, 8 CAN signals",
                "**No attention mechanism**",
                "Ensemble 0.9595 vs 0.9475 / 0.9133 — the gain is mostly **stability**",
                "Parameters: MLP 762k · ResNet 514k · **M 1-D CNN 90k** · LSTM 6k",
                "Four augmentations: sliding window · noise · reversal · random drift",
                "Test set = **last 30%** of the drive (chronological)"],
        mine=["**Augmentation pays most when data is scarce: +15.2 pts at 1 min, +1.3 pts at 15 min**",
              "Ranked for us: sliding window → **drift** → noise → reversal",
              "Drift may make the model **invariant to slow trip-state offsets**",
              "Reversal turns braking into acceleration → do it last",
              "Accuracy doesn't track parameter count → small models are viable"],
        notes="The scarcity curve is the strongest argument for our data-efficiency framing."),
    dict(
        n=6, title="Shin et al. (2025) — MLOps, MTF images, drift",
        venue="Electronics (MDPI) · peer-reviewed journal",
        theirs=["CAN → **Markov Transition Field images** → ResNet-18 on Google Cloud",
                "Continuous retraining; only models > 70% validation accuracy deploy",
                "Old-data model 33–49% vs recent-data model **67–78%**",
                "Detects **unregistered drivers** via multi-maneuver voting",
                "Only **turns** exceed 70% — straight, stop and start fail"],
        mine=["Images give **structure at the cost of precision** — and unlock the CNN ecosystem",
              "Their \"drift\" test is really **cross-session vs same-session** (~20-month gap)",
              "→ the best evidence that our same-session numbers are **upper bounds**",
              "Unregistered-driver detection **already exists** → our claim must be sharper",
              "Borrow their visualisation habit: **t-SNE by driver, then by trip phase**"],
        notes="Reframe their drift result as session variability; our best citation for the trip confound."),
    dict(
        n=7, title="Lee et al. (2025) — P-AttEnc: few-shot prototypes",
        venue="arXiv preprint",
        theirs=["Driver ID framed as **multivariate time-series classification**",
                "**Attention-only encoder**: 87.6% fewer parameters, 44–79% faster",
                "**Prototypical network**: driver = mean embedding of a few labelled windows",
                "Classified by **Euclidean distance** to the nearest prototype",
                "Closed-set 99.0–99.9%; 10-way 1-shot 69.8%; \"unknown drivers 65.7%\""],
        mine=["The **mechanism transfers**: Mantis embeddings → prototype → nearest match",
              "= **enrollment without retraining**, which is what makes open-set possible",
              "\"65.7% on unknown drivers\" is a **2-way** test — chance is 50%",
              "10 drivers per dataset; 30 s windows with 50% overlap, random split",
              "**No channel selection, no multi-rate handling, no sampling rate stated**"],
        notes="Take the mechanism, not the evaluation."),
    dict(
        n=8, title="Feofanov et al. (2026) — Mantis",
        venue="arXiv preprint · classification-native time-series foundation model",
        theirs=["**4.2M parameters**; contrastive pre-training on **purely synthetic** data",
                "Input resized to **512 steps** → 32 tokens",
                "Frozen encoder beats larger models: UCR **0.820** vs MOMENT 0.779",
                "Out-of-distribution sensors: Mantis **0.582** vs MOMENT 0.308",
                "**Channel adapters** (PCA or linear, d → 10) improved all 10 multivariate sets",
                "Best features come from an **intermediate** layer, not the last"],
        mine=["**One channel at a time** — the encoder never sees two signals together",
              "**True zero-shot is impossible** for identity: their \"zero-shot\" still trains a classifier",
              "**Open-set rejection needs a separate score** — Mantis provides none",
              "Its tokeniser already encodes **first-order differences** = our \"jerkiness\" finding",
              "It keeps **unnormalised** patch mean/std → absolute levels survive → audit still required"],
        notes="Primary candidate: classification-native, small enough to fine-tune."),
    dict(
        n=9, title="Gnassounou et al. (2025) — does it transfer?",
        venue="arXiv preprint · generic TSFMs applied to EEG · same authors as Mantis",
        theirs=["Fine-tuned **Mantis** on EEG: motor imagery (109 + 25 subjects), sleep staging (8 datasets)",
                "Beats **EEGNet** and **CBraMod**, an EEG-specific foundation model",
                "Wins every sleep dataset (MASS 84.1 vs 81.1 vs 79.9)",
                "**Synthetic** pre-training matches or beats real-data pre-training",
                "Channel-independent Mantis beats CBraMod's multivariate design"],
        mine=["**\"Freezing the encoder leads to a huge decrease\"** → fine-tuning is necessary",
              "They dropped MOMENT purely because it is **too big to fine-tune**",
              "Pre-training gains are **modest (+0.3 to +5 pts)** over random init",
              "⚠ They split **by subject** — identity is a nuisance there; for us identity **is** the label",
              "**Adopt their design:** random vs synthetic vs real pre-training = our core ablation"],
        notes="Transfer evidence for the proposal — but it shows Mantis handles unfamiliar signals, not that it separates individuals."),
]


def add_paper_slides(prs) -> None:
    """Append one two-column slide per reviewed paper."""
    for p in PAPERS:
        two_card_slide(prs, p["title"], p["venue"],
                       ("THEIR POV", p["theirs"]), ("MY POV", p["mine"]),
                       notes=p["notes"], n=p["n"])


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "outputs" / "appendix_papers.pptx"
    prs = new_deck()
    add_paper_slides(prs)
    prs.save(out)
    print(f"wrote {out}")
