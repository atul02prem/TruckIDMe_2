"""Run pipeline stages in dependency order, recording provenance for each.

A stage runs only when it is stale: never run, failed, missing an output, or
with changed inputs, parameters or source code.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.pipeline import provenance as prov
from src.pipeline.registry import PLANNED, Stage, stage_by_name, topological_order

STAMP_DIR = prov.ROOT / "provenance" / "stamps"


def _write_stamp(stage: Stage) -> None:
    """Record that an in-place stage completed, so downstream stages can depend on it.

    Args:
        stage: the in-place stage that just finished.
    """
    STAMP_DIR.mkdir(parents=True, exist_ok=True)
    commit, _, dirty = prov.git_state()
    stamp = STAMP_DIR / f"{stage.name.replace('build_', '')}.json"
    stamp.write_text(json.dumps({
        "stage": stage.name,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "git_dirty": dirty,
        "params": stage.params,
    }, indent=2) + "\n")


def plan(targets: list[str] | None, force: bool) -> list[tuple[Stage, bool, str]]:
    """Decide what would run, in order.

    Args:
        targets: stage names to build (with their upstreams); None means all.
        force: treat every stage as stale.

    Returns:
        List of (stage, will_run, reason) in dependency order.
    """
    decisions = []
    for stage in topological_order(targets):
        if stage.status == PLANNED:
            decisions.append((stage, False, "planned — not implemented yet"))
            continue
        stale, reason = prov.staleness(stage)
        decisions.append((stage, True, "forced") if force else (stage, stale, reason))
    return decisions


def run_stage(stage: Stage) -> int:
    """Execute one stage and write its manifest.

    Args:
        stage: the stage to run.

    Returns:
        The process exit code.
    """
    command = [sys.executable, "-m", stage.module]
    started = datetime.now(timezone.utc).replace(tzinfo=None)
    clock = time.perf_counter()
    result = subprocess.run(command, cwd=prov.ROOT)
    duration = time.perf_counter() - clock

    if result.returncode == 0 and stage.in_place:
        _write_stamp(stage)

    manifest = prov.build_manifest(stage, command, started, duration, result.returncode)
    path = prov.write_manifest(manifest)
    mark = "ok" if result.returncode == 0 else f"FAILED ({result.returncode})"
    print(f"  [{mark}] {stage.name} in {duration:.1f}s → {path.relative_to(prov.ROOT)}")
    return result.returncode


def run(targets: list[str] | None, force: bool, dry_run: bool) -> int:
    """Run the requested stages and their stale upstreams.

    Args:
        targets: stage names; None means the whole pipeline.
        force: run even stages that are up to date.
        dry_run: print the plan without executing anything.

    Returns:
        0 if everything succeeded or was skipped, else the first failing code.
    """
    decisions = plan(targets, force)
    todo = [(s, r) for s, will, r in decisions if will]
    skipped = [(s, r) for s, will, r in decisions if not will]

    print(f"\nplan: {len(todo)} to run, {len(skipped)} skipped\n")
    for stage, reason in todo:
        print(f"  RUN   {stage.name:<32} ({reason})")
    for stage, reason in skipped:
        print(f"  skip  {stage.name:<32} ({reason})")
    if dry_run or not todo:
        return 0

    print()
    for stage, _ in todo:
        code = run_stage(stage)
        if code != 0:
            print(f"\nstopped: {stage.name} failed")
            return code
    return 0


def adopt(targets: list[str]) -> int:
    """Record existing artifacts as a stage's outputs without re-running it.

    Used once, for stages that ran before provenance tracking existed: the
    manifest is written with `retrofitted` set, so it is clear the inputs and
    code version at the original run time are unknown.

    Args:
        targets: stage names to adopt.

    Returns:
        0 on success, 1 if any stage has missing outputs.
    """
    failed = 0
    for name in targets:
        stage = stage_by_name(name)
        if stage.in_place:
            _write_stamp(stage)       # the stamp is ours to write, not the module's
        missing = [o for o in stage.outputs
                   if prov.fingerprint(o).kind == "missing"]
        if missing:
            print(f"  cannot adopt {stage.name}: missing {', '.join(missing)}")
            failed = 1
            continue
        started = datetime.now(timezone.utc).replace(tzinfo=None)
        manifest = prov.build_manifest(stage, stage.command, started, 0.0, 0)
        manifest.description = f"[RETROFITTED] {manifest.description}"
        manifest.params = {**stage.params, "retrofitted": True}
        path = prov.write_manifest(manifest)
        print(f"  adopted {stage.name} → {path.relative_to(prov.ROOT)}")
    return failed


def status() -> list[dict[str, str]]:
    """Current state of every stage, for the CLI and the README table.

    Returns:
        One row per stage with its freshness, last run time and commit.
    """
    rows = []
    for stage in topological_order():
        manifest = prov.read_manifest(stage.name)
        if stage.status == PLANNED:
            state, reason = "planned", "not implemented"
        else:
            stale, reason = prov.staleness(stage)
            state = "stale" if stale else "fresh"
        rows.append({
            "stage": stage.name,
            "group": stage.group,
            "state": state,
            "reason": reason,
            "last_run": (manifest.started_utc[:16].replace("T", " ")
                         if manifest else "—"),
            "commit": (manifest.git_commit[:7] + ("+dirty" if manifest.git_dirty else "")
                       if manifest else "—"),
            "duration": f"{manifest.duration_s:.0f}s" if manifest else "—",
        })
    return rows
