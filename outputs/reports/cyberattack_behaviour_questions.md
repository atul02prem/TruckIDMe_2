# TruckIDMe — Cyberattack Behaviour Sub-Study: Open Questions

Second research thread (separate from driver-ID): *did drivers respond to the
cyberattack as their group instructed, and does awareness change behaviour?*

Groups: G1 (no warning, 13), G2 (warned may occur, 16), G3 (warned + instructed
to pull over, 17). Attack triggers shortly after passing **North Overland Trail
on Laporte Avenue**, stops after **1 min or when the driver pulls over**.

## Source paper (Lanigan et al., external_data/3002667.pdf)

The dataset's own paper. Key facts (verified from the PDF):
- **3×2 design:** awareness {Control, Aware, Aware+Protocol} = our {G1,G2,G3}
  (n=17/16/17) × experience {Standard=31, Professional=19}. Professional = CDL,
  or >5000 mi/yr, or trained (8 firefighters). **Experience labels are in the
  survey data and we are NOT yet using them.**
- Attack = MITM Teensy behind the instrument cluster, at a **fixed location**
  (~halfway, low-traffic 1-mile stretch, continuous shoulder, 40 mph). Active
  60 s, or until the driver stops ≥5 s.
- Human-factors results: stop rate Control-Standard 9% / Control-Professional
  83% / Aware+Protocol 100%. Distance-during-attack: Control-Std 828 m →
  Aware+Protocol-Std 224 m. Reaction time: Control 30.3 s, Aware 16.1 s,
  Aware+Protocol 7.5 s. The paper's own analysis **downsampled to 1 Hz** — we
  work at native CAN rates (higher resolution than the source paper).

## Methodological cautions (settle these first)

- **CORRECTED (was wrong before): the attack does NOT corrupt the J1939 data we
  use.** §2.4: the instrument cluster is on a *separate CAN* from the J1939 main
  bus; the MITM spoofed only the dashboard display/audio, "independent of standard
  vehicle systems." Confirmed empirically: on a Control driver (G1S13, full 60 s
  attack) neither `190 Engine Speed` nor `190 Engine Speed CAN0` shows a 60 s zero
  window. **SPN 84 / 190 / pedal are truthful throughout — no masking needed for
  driver ID.** (Earlier "spoofs speed to 0, use GPS" caution was incorrect.)
- **The spoofed SPN 190→0 is on the instrument CAN, recorded on a separate logger
  channel that is NOT in our high-res SPN CSVs.** So the attack window is not
  recoverable from the 190 columns. Get it from the downsampled dataset's
  `cyberattack_active`, or reconstruct from the fixed attack GPS location + the
  60 s / stop rule.
- GPS speed is still the cleanest way to detect actual stops/pull-overs, but now
  because it is direct — not because CAN is corrupted.

## Confounder to check: awareness vs experience

Our robust "G3 (Aware+Protocol) hardest to classify" finding may be partly an
**experience effect**: professionals behave more uniformly (100% stop), which is
harder to tell apart. Add the Professional/Standard label and test whether
experience, not awareness, drives the separability difference.

## A. Pull-over detection — did they actually do it?

1. For each driver, *where* does the maximum `sector_dist_m` occur — in the
   start/end parking lot, or mid-route (a genuine roadside pull-over)?
2. Using GPS speed, does each driver have an extended near-zero-speed episode
   mid-route (not at a normal intersection)? How long?
3. Do G3 drivers show a mid-route stop + lateral off-route deviation that G1
   drivers lack?
4. How many G3 drivers *actually pulled off the roadway* vs merely slowed/stopped
   in-lane vs kept driving?

## B. Group-level comparison

5. Overlay all 46 GPS traces, coloured by group — do G3 traces visibly diverge
   from the common route where G1/G2 don't?
6. Distribution of max off-route distance by group — is G3 systematically higher?
7. Count and duration of stops per driver, grouped — is G3 > G2 > G1?
8. Did any G2 drivers (warned, not instructed) pull over anyway? Did any G3
   (instructed) fail to pull over? These exceptions are the interesting cases.

## C. Attack localisation & timing

9. Which sector contains North Overland Trail × Laporte? Mark it on the map.
10. For each driver, what happens in the ~60 s after they pass the trigger point?
11. Can attack onset be detected from behaviour alone (sudden deceleration, lane
    change) without using any label?

## D. Speed / dynamics

12. GPS speed vs time per driver, with the attack window shaded and stops marked.
13. CAN wheel speed (SPN 84) vs GPS speed during the window — does CAN → 0 while
    GPS stays real?
14. Deceleration profiles at attack onset by group — do warned drivers brake more
    smoothly / anticipate?

## F. Did the attack actually tamper the CAN bus? (verify, don't assume)

The README states the attack sets speedometer + tachometer to 0. Confirm this
empirically from the bus rather than trusting the description — the real
signature may be richer.

17. Which signals actually deviate during the attack window? Plot each candidate
    (SPN 84 Wheel-Based Speed, SPN 190 Engine Speed, and neighbours) against its
    normal profile and against GPS truth.
18. Is the tamper a **zero**, a **freeze** (last value held), or an **injected
    constant / pattern**? The three imply different attack mechanisms.
19. Does the spoof hit only the dash-facing signals (84, 190), or does it
    propagate to *derived* signals (512 Driver Demand Torque, 513 Actual Torque,
    523 Current Gear, wheel-speed-derived features)?
20. Time-aligned, quantify CAN speed vs GPS speed divergence during the window —
    how large, how abrupt at onset/offset?
21. Is the tamper signature **identical across all 46 drivers** (same attack
    payload) or does it vary by drive?
22. Does the CAN-anomaly onset coincide with the spatial trigger (North Overland
    × Laporte) and last ~60 s / until pull-over — i.e. does the bus evidence match
    the stated trigger rule?
23. Can we build an automatic **tampered-interval detector** (e.g. CAN speed ≈ 0
    while GPS speed > threshold) to mask exactly the corrupted signal-intervals,
    rather than blanket-dropping the whole attack minute? This is the surgical
    version of pipeline question 15.

## E. Feedback into the driver-ID pipeline

15. Which CAN signals are corrupted during the attack minute, and should the
    attack window be masked / excluded / flagged when building ID features?
16. Is "attack response" itself a driver fingerprint, or does it homogenise
    behaviour (early finding: G3 was hardest to classify — possibly because the
    pull-over instruction makes G3 drivers behave alike)?
