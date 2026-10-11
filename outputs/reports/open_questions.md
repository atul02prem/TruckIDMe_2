# TruckIDMe — Open Questions / Methodological Caveats

Running list of things to revisit. (Cyberattack-specific questions live in
`cyberattack_behaviour_questions.md`.)

## Q1. Fixed time windows compare "apples to oranges"

For driver ID we switched from route-sectors to fixed-duration (e.g. 2-min)
windows, and accuracy jumped (33% → 50%). But arbitrary time windows are **not
route-aligned**: window *k* of driver A might be a highway stretch while window
*k* of driver B is a city intersection. So the classifier may be comparing
behaviourally different situations across drivers — apples to oranges.

Open sub-questions:
- Is the higher accuracy of fixed windows genuine (better/uniform behavioural
  sampling), or does it partly come from the model exploiting **route/position
  differences** across windows — a subtle confound rather than pure behaviour?
- Would **sector-aligned** windows (compare drivers on the *same* road segment,
  apples to apples) be more principled, even if lower accuracy? This is the
  original motivation for sectors.
- Concretely: build a sector-normalised comparison (per driver × sector feature
  vectors) and check whether same-sector cross-driver differences are what drive
  ID, or whether route/position is leaking. Compare fixed-window vs
  sector-aligned accuracy and interpret the gap.

Status: noted; ID pipeline currently uses fixed windows. Sectors retained for
this analysis and the cyberattack study.

## Q2. Sector-coverage anomalies (from investigate_sector_coverage.py)

Sector lengths: min 33 m (sector 15), median 347 m, max 3167 m. Three distinct
reasons drivers don't hit all 31 sectors:

- **Sector 15 (33 m, the shortest): missed by ~26 drivers — a nearest-neighbor
  ARTIFACT.** A 33 m segment between much longer neighbors gets "shadowed": a
  driver with slight GPS offset has all its rows there assigned to sector 14/16.
  They *did* drive it. Harmless for ID (sector_id unused), but sector 15 is
  unreliable for any sector-based analysis. (Fix idea: merge very short sectors,
  or assign by nearest-segment perpendicular distance instead of nearest dense
  point.)
- **G1S03 misses sector 19 (1002 m): NOT real — out-and-back overlap artifact.**
  Sectors 12 (outbound, westbound) and 19 (return, eastbound) are the SAME road
  at lat ~40.589 (long −105.134…−105.146), opposite directions. NN assignment
  knows only position, not heading/time, so on the overlap a driver's points go
  to whichever dense point is marginally nearer — sector 12 wins for most drivers,
  so they never get credited sector 19. G1S03 drove it fine (points there have
  dist ~3 m, labeled sector 12). Reference G1S01 shows 31/31 by luck.
  **Method limitation: NN sectorization cannot disambiguate out-and-back on the
  same road. Fix = heading-aware assignment (we have `headingDegree`: require the
  sector's travel direction to match the driver's instantaneous heading).**
- **G3S01 misses sectors 23–24 (West Mulberry, ~440 m): REAL — nearest GPS is
  731 m away.** G3S01 is the pull-over group; this is almost certainly the
  cyberattack response (pulled over, rejoined elsewhere). Signal for the attack
  sub-study, not an error. Also has the largest sector_dist (406 m).

To do: investigate G1S03/sector-19 the same way; fold G3S01's West-Mulberry skip
into the cyberattack behaviour analysis.


## Q3. Sector-wise episodic training (candidate experiment, raised 2026-09-18)

Idea (user's): build few-shot *episodes* from windows of the **same sector** across
drivers, so each episode asks "who is driving *this stretch of road*?" — a matched-context
comparison that directly addresses Q1's apples-to-oranges concern, reusing the existing
RDP sector map.

Cautions before trying it:
- Sector assignment is unreliable on the out-and-back overlap (12↔19) and the 33 m
  sector 15 — fix with heading-aware assignment first, or exclude those sectors.
- Short sectors yield few windows per driver; some drivers miss sectors entirely
  (G3S01 skipped 23–24 during the cyberattack response).
- Sector-conditioned training bakes in the fixed route — the design KCID (2025) calls
  unrealistic for authentication. Strengthens interpretability, weakens deployment claims.
- Requires trainable weights (a frozen encoder cannot learn from episodes).

Status: candidate secondary experiment; primary remains fixed-duration windows.
