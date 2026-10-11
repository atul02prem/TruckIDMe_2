"""Provenance recording for pipeline stages.

Every stage run writes one manifest to `provenance/<stage>.json` describing
exactly how its outputs were produced: the git commit, the fingerprint of every
input and output, the parameters in force, and how long it took.

Manifests are committed to git even though `data/` is not, so the lineage of a
result survives even when the data files do not.
"""

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
PROVENANCE_DIR = ROOT / "provenance"

# Files larger than this are fingerprinted by size+mtime instead of content,
# so a full pipeline status check stays fast on ~100 MB driver CSVs.
CONTENT_HASH_LIMIT_BYTES = 64 * 1024 * 1024


@dataclass
class Fingerprint:
    """Identity of one input or output artifact at a point in time."""

    path: str
    kind: str                 # "file" | "dir" | "missing"
    method: str               # "sha256" | "size-mtime" | "dir-listing" | "none"
    value: str
    n_files: int | None = None
    size_bytes: int | None = None


@dataclass
class Manifest:
    """The full record of one stage run."""

    stage: str
    description: str
    command: list[str]
    started_utc: str
    duration_s: float
    git_commit: str
    git_branch: str
    git_dirty: bool
    code_fingerprint: str
    params: dict[str, Any]
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    exit_code: int = 0


def git_state() -> tuple[str, str, bool]:
    """Current commit, branch, and whether the working tree has changes.

    Returns:
        (commit_sha, branch_name, is_dirty). Values are "unknown" if git fails.
    """
    def _git(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                                  text=True, check=True).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    commit = _git("rev-parse", "HEAD")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    dirty = bool(_git("status", "--porcelain"))
    return commit, branch, dirty


def _sha256_file(path: Path) -> str:
    """Streaming SHA-256 of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(rel_path: str) -> Fingerprint:
    """Fingerprint one artifact, cheaply enough to call on every status check.

    Args:
        rel_path: path relative to the repository root (file or directory).

    Returns:
        A Fingerprint. Small files are hashed by content; large files by
        size+mtime; directories by the listing of (name, size, mtime).
    """
    path = ROOT / rel_path
    if not path.exists():
        return Fingerprint(rel_path, "missing", "none", "")

    if path.is_dir():
        entries = sorted(p for p in path.rglob("*") if p.is_file())
        digest = hashlib.sha256()
        total = 0
        for item in entries:
            stat = item.stat()
            total += stat.st_size
            digest.update(f"{item.relative_to(path)}|{stat.st_size}|{stat.st_mtime_ns}".encode())
        return Fingerprint(rel_path, "dir", "dir-listing", digest.hexdigest(),
                           n_files=len(entries), size_bytes=total)

    stat = path.stat()
    if stat.st_size <= CONTENT_HASH_LIMIT_BYTES:
        return Fingerprint(rel_path, "file", "sha256", _sha256_file(path),
                           size_bytes=stat.st_size)
    return Fingerprint(rel_path, "file", "size-mtime",
                       f"{stat.st_size}:{stat.st_mtime_ns}", size_bytes=stat.st_size)


def code_fingerprint(code_files: tuple[str, ...]) -> str:
    """SHA-256 over the source files that implement a stage.

    Args:
        code_files: repo-relative paths to the stage's source files.

    Returns:
        A single hex digest; changes whenever any stage source file changes.
    """
    digest = hashlib.sha256()
    for rel in sorted(code_files):
        path = ROOT / rel
        digest.update(rel.encode())
        digest.update(_sha256_file(path).encode() if path.exists() else b"missing")
    return digest.hexdigest()


def manifest_path(stage_name: str) -> Path:
    """Path of the manifest file for one stage."""
    return PROVENANCE_DIR / f"{stage_name}.json"


def read_manifest(stage_name: str) -> Manifest | None:
    """Load a stage's last manifest, or None if it has never run."""
    path = manifest_path(stage_name)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Manifest(**data)


def write_manifest(manifest: Manifest) -> Path:
    """Write a manifest to provenance/ and return its path."""
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    path = manifest_path(manifest.stage)
    path.write_text(json.dumps(asdict(manifest), indent=2) + "\n")
    return path


def build_manifest(stage, command: list[str], started: datetime,
                   duration_s: float, exit_code: int) -> Manifest:
    """Assemble a manifest by fingerprinting a stage's inputs and outputs now.

    Args:
        stage: the Stage that was run.
        command: the exact command executed.
        started: UTC start time.
        duration_s: wall-clock seconds.
        exit_code: process exit code.

    Returns:
        A populated Manifest, not yet written to disk.
    """
    commit, branch, dirty = git_state()
    return Manifest(
        stage=stage.name,
        description=stage.description,
        command=command,
        started_utc=started.replace(tzinfo=timezone.utc).isoformat(),
        duration_s=round(duration_s, 2),
        git_commit=commit,
        git_branch=branch,
        git_dirty=dirty,
        code_fingerprint=code_fingerprint(stage.code),
        params=stage.params,
        inputs=[asdict(fingerprint(p)) for p in stage.inputs],
        outputs=[asdict(fingerprint(p)) for p in stage.outputs],
        exit_code=exit_code,
    )


def staleness(stage) -> tuple[bool, str]:
    """Decide whether a stage needs to run again.

    Args:
        stage: the Stage to check.

    Returns:
        (is_stale, reason). A stage is stale if it never ran, failed, lost an
        output, or if any input fingerprint, parameter or source file changed.
    """
    manifest = read_manifest(stage.name)
    if manifest is None:
        return True, "never run"
    if manifest.exit_code != 0:
        return True, f"last run failed (exit {manifest.exit_code})"

    for recorded in manifest.outputs:
        current = fingerprint(recorded["path"])
        if current.kind == "missing":
            return True, f"output missing: {recorded['path']}"

    for recorded in manifest.inputs:
        current = fingerprint(recorded["path"])
        if current.value != recorded["value"]:
            return True, f"input changed: {recorded['path']}"

    if manifest.params != stage.params:
        return True, "parameters changed"
    if manifest.code_fingerprint != code_fingerprint(stage.code):
        return True, "stage code changed"
    return False, "up to date"
