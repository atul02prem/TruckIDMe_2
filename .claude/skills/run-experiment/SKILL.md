---
name: run-experiment
description: Scaffold, run, and document a reproducible TruckIDMe ML experiment in its own self-contained folder with a full data-lineage (dimensions) record. Use whenever starting any new modeling / feature / signal-selection experiment (e.g. "run an experiment where...", "let's try X for identification", a new baseline or ablation).
---

# Running a reproducible TruckIDMe experiment

Every experiment is **self-contained in its own folder** under `experiments/`, with
its scripts and a documented data lineage. Never scatter experiment scripts in
`playground/` — that is for shared/pipeline code only.

## 1. Create the experiment folder

```
experiments/expNN_shortname/
├── README.md      # objective, data lineage w/ DIMENSIONS, split, commands, results
├── <scripts>.py   # self-contained; may import helpers from src/ and playground/
└── results.md     # the output report (script writes it here, not outputs/reports/)
```

- `NN` = next zero-padded sequence number (`ls experiments/` to find it).
- `shortname` = terse kebab/underscore slug, e.g. `03_slow_signals_only`.
- Scripts run as modules from repo root: `python -m experiments.expNN_shortname.<script>`.
  (Add empty `__init__.py` if imports need it.)

## 2. Recreate the data FROM SCRATCH inside the experiment

Each experiment **builds its own dataset from the source signals** — do not rely
on a shared pre-built master timeline. Start from `data/processed_data/`
(native-rate CAN signals + their `TimeXXX` columns + GPS/`canloggerTime`), then
filter / window / aggregate exactly what this experiment needs, in the
experiment's own script. This keeps every experiment reproducible from source and
independent of pipeline state elsewhere.

The README **must document the data-creation steps** (the from-scratch build), not
just consume an existing file.

## 3. Document the data lineage WITH DIMENSIONS (required)

The README must record the full pipeline as a **chain of shapes**, so anyone can
see exactly how data is manipulated and how many rows/cols/features exist at each
stage. Template:

```
## Data lineage (dimensions at each stage)
| Stage | What | Shape |
|---|---|---|
| raw_data/       | 49 driver CSVs (native-rate CAN + Time + GPS + VBOX + Empatica) | ~250k rows × 306 cols |
| processed_data/ | filtered (drop VBOX/Empatica/id + EXCLUDE_SPNS)                 | 46 usable, ~250k × 134 |
| interim_data/   | master timeline: CAN aligned to 10 Hz + GPS/sector            | 46, ~26k × 154 (142 CAN ch) |
| signal filter   | <describe: e.g. keep only <=5 Hz signals>                     | 11 signals |
| windowing       | <e.g. non-overlap 120 s windows>                             | ~21 windows/driver |
| features        | <e.g. 11 signals × 9 aggregates>                             | 99 features/window |
| split           | <e.g. per-driver chronological 70% train / 5% gap / 25% test> | X_tr ~690×99, X_te ~230×99 |
| model           | <e.g. RandomForest 300 trees>                                | 46 classes |
```

Always state, in prose or table, WHAT changed the shape at each arrow.

## 3. Pin everything needed to reproduce

In the README, record:
- **EXCLUDE_SPNS state** (count + note it is the audited 40-SPN list, or list deltas).
- **EXCLUDE_DRIVERS** (G1S04, G1S10/11/12 → 46 usable).
- **Which master timeline** the experiment reads (mean-only 62-channel, or
  142-channel with within-100ms aggregates) — this matters and has bitten us before.
- **Split** protocol, **seed**, **model hyperparameters**, **metrics** (top-1/2/5).
- **Exact commands** to reproduce, in order.

## 4. Null / completeness check after EVERY data-altering stage (required)

After each step that changes dimensionality or data (filter, window, aggregate,
merge, impute), call `null_report` (from `playground.dataqc`) on the resulting
DataFrame:

```python
from playground.dataqc import null_report
null_report(df, stage="after_slow_filter", out_dir=QC_DIR)   # QC_DIR = <exp folder>/qc
```

It writes a missingno matrix + bar image and a per-column null-% table into the
experiment's `qc/` folder, and prints a one-line summary. Reference the resulting
null percentages in the README so silent NaN introduction (leading nulls, ffill
artifacts, empty windows) is always visible and explained.

## 5. Guardrails (reuse existing helpers)

- Import `check_channel_uniformity` (from `playground.build_feature_matrix`) at any
  driver-stacking point so a schema mismatch fails loudly, naming the driver.
- Reuse `aggregate_signals`, `get_can_signal_cols`, `filename_to_driver_id`,
  `driver_id_to_group` rather than reimplementing.
- Any signal-set / aggregate decision must be **global** (decided once, applied to
  all drivers) — never per-driver — or the schema drifts.

## 5. Record results in the folder

The script writes `results.md` **inside the experiment folder** (not the shared
`outputs/reports/`), and the README's results section is updated with the headline
numbers + a one-line interpretation. Also add a one-line pointer to the experiment
in `outputs/reports/research_plan.md` so the master log stays complete.

## 6. Report back

Relay: the headline metric, how it compares to the relevant baseline, and whether
it confirms/refutes the hypothesis. Keep the raw report in the folder; summarize
in chat.
