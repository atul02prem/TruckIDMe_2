# Provenance & pipeline framework

How this project stays traceable: what runs, in what order, from which inputs,
with which code, and when. Nothing here is manual bookkeeping — the registry is
the source of truth and everything else is generated from it.

---

## 1. The three moving parts

| Part | File | Role |
|---|---|---|
| **Registry** | `src/pipeline/registry.py` | Declares every stage: inputs, outputs, params, source files, status |
| **Provenance** | `src/pipeline/provenance.py` | Fingerprints artifacts, records git state, decides staleness |
| **Runner / renderer** | `src/pipeline/runner.py`, `render.py` | Runs stages in dependency order; regenerates the README overview |

The dependency graph is **derived**, not declared: if stage B lists an input
that stage A lists as an output, B depends on A. There is no second place to
keep in sync.

## 2. What a manifest records

Every stage run writes `provenance/<stage>.json`:

```json
{
  "stage": "build_processed_data",
  "command": ["python", "-m", "src.data.build_processed_data"],
  "started_utc": "2026-10-11T18:22:04",
  "duration_s": 412.8,
  "git_commit": "2f56db7…", "git_branch": "main", "git_dirty": false,
  "code_fingerprint": "sha256 over the stage's source files",
  "params": {"exclude_spns": [96, 105, …], "n_exclude_spns": 40},
  "inputs":  [{"path": "data/raw_data", "kind": "dir", "method": "dir-listing",
               "value": "…", "n_files": 49}],
  "outputs": [{"path": "data/processed_data", "…": "…"}],
  "exit_code": 0
}
```

**Manifests are committed to git even though `data/` is not.** The data files are
too large to version, but their lineage is permanent: for any result in
`outputs/reports/`, the manifest chain says which code version and which input
fingerprints produced it.

### Fingerprint methods

| Artifact | Method | Why |
|---|---|---|
| File ≤ 64 MB | `sha256` of contents | exact |
| File > 64 MB | `size:mtime_ns` | hashing ~100 MB driver CSVs on every status check is too slow |
| Directory | `sha256` over sorted `(name, size, mtime)` | detects added, removed or rewritten files |

## 3. Staleness rules

A stage re-runs when any of these is true:

1. it has never run (no manifest);
2. its last run failed (non-zero exit);
3. one of its declared outputs is missing;
4. an input fingerprint differs from the recorded one;
5. its parameters differ from the registry;
6. its **source files** changed (`code_fingerprint`).

Rule 6 is the one most pipelines miss: editing `build_master_timeline.py`
invalidates the timeline even though no data file changed.

## 4. Commands

```bash
python -m src.pipeline status                  # what is fresh / stale / planned
python -m src.pipeline graph                   # regenerate the README overview
python -m src.pipeline run <stage> --dry-run   # show the plan without running
python -m src.pipeline run <stage>             # run it, and any stale upstream
python -m src.pipeline run --all               # the whole pipeline
python -m src.pipeline adopt <stage>           # one-off: record existing outputs
```

`adopt` exists only for artifacts built **before** this framework. It writes a
manifest marked `"retrofitted": true` and `[RETROFITTED]` in the description, so
it is never mistaken for a real, reproducible run. Ten stages were adopted on
2026-10-11; every one of them will be replaced by a genuine manifest the first
time it re-runs.

## 5. Adding a stage

1. Write the module so it can run as `python -m src.<group>.<name>`.
2. Add one `Stage(...)` entry to `registry.py` — inputs, outputs, params, `code`.
3. `python -m src.pipeline graph` to refresh the README.

Stages carry a `status`: `built`, `wip`, or `planned`. Planned stages appear in
the chart as dashed boxes and are never executed, so the published overview shows
the whole design, not only the finished parts.

## 6. Known defects (to fix, in order)

| # | Defect | Consequence | Fix |
|---|---|---|---|
| 1 | **`build_master_timeline` rewrites `data/interim_data/` in place** | You cannot tell from disk whether interim files are pre- or post-alignment; the DAG needs a stamp file to express the dependency | Write the aligned timeline to its own directory (`data/master_timeline/`) and update the four consumers |
| 2 | Reports in `outputs/reports/` do not name the stage that generated them | A reader cannot connect a report to a manifest | Have each stage write a provenance footer into its report |
| 3 | `data/processed_data/` holds both per-driver CSVs and `feature_matrix.csv` | Mixes pipeline stages in one directory | Move feature matrices to `data/features/` |
| 4 | Two stages have no artifacts yet (`build_windowed_feature_matrix`, `run_window_sweep_chrono`) | Their earlier results exist in reports but cannot be reproduced | Re-run both once the timeline is rebuilt |

## 7. Rules

- **Never hand-edit** the block between `<!-- PIPELINE:START -->` and
  `<!-- PIPELINE:END -->` in the README; it is overwritten on every `graph`.
- **Never hand-edit a manifest.** If it is wrong, re-run the stage.
- Parameters that affect an output belong in `src/config.py` and in the stage's
  `params`, never as literals inside a function.
- Commit before a long run, so `git_dirty` is `false` and the manifest points at
  a real, retrievable commit.
