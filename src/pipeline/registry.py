"""Declarative registry of every pipeline stage.

This file is the single source of truth: the runner executes from it, the
README chart is rendered from it, and the provenance manifests record it.
Adding a stage means adding one entry here — nothing else.

Each stage declares repo-relative inputs and outputs; the dependency graph is
derived from where those overlap.
"""

from dataclasses import dataclass, field
from typing import Any

from src.config import EXCLUDE_DRIVERS, EXCLUDE_SPNS

BUILT = "built"        # implemented and runnable
WIP = "wip"            # exists but incomplete
PLANNED = "planned"    # part of the plan, not yet written


@dataclass(frozen=True)
class Stage:
    """One unit of work with declared inputs, outputs and parameters."""

    name: str
    description: str
    module: str                       # run as: python -m <module>
    group: str                        # data | qc | features | models | tsfm
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    code: tuple[str, ...] = ()        # source files whose change invalidates it
    params: dict[str, Any] = field(default_factory=dict)
    status: str = BUILT
    in_place: bool = False            # rewrites one of its own inputs

    @property
    def command(self) -> list[str]:
        """The command used to run this stage."""
        return ["python", "-m", self.module]


_DRIVERS = sorted(EXCLUDE_DRIVERS)
_SPNS = sorted(EXCLUDE_SPNS)

STAGES: tuple[Stage, ...] = (
    # ── data preparation ────────────────────────────────────────────────
    Stage(
        name="build_processed_data",
        description="Raw driver CSVs → processed: keep CAN + SparkFun, drop VBOX/Empatica, drop EXCLUDE_SPNS",
        module="src.data.build_processed_data",
        group="data",
        inputs=("data/raw_data",),
        outputs=("data/processed_data", "outputs/reports/column_sampling_rates.md"),
        code=("src/data/build_processed_data.py", "src/config.py"),
        params={"exclude_drivers": _DRIVERS, "exclude_spns": _SPNS,
                "n_exclude_spns": len(_SPNS)},
    ),
    Stage(
        name="build_sector_map",
        description="RDP route simplification on the reference driver → sector waypoints",
        module="src.data.build_sector_map",
        group="data",
        inputs=("data/processed_data",),
        outputs=("data/external_data/sector_map.csv", "outputs/figures/sector_map.png"),
        code=("src/data/build_sector_map.py", "src/config.py"),
        params={"reference_driver": "G1_Subject1"},
    ),
    Stage(
        name="assign_sectors",
        description="GPS rows → nearest sector via KDTree → interim per-driver CSVs",
        module="src.data.assign_sectors",
        group="data",
        inputs=("data/processed_data", "data/external_data/sector_map.csv"),
        outputs=("data/interim_data",),
        code=("src/data/assign_sectors.py", "src/config.py"),
        params={},
    ),
    Stage(
        name="build_master_timeline",
        description="Align every CAN signal to the 10 Hz canloggerTime grid (mean per 100 ms / zero-order hold)",
        module="src.data.build_master_timeline",
        group="data",
        inputs=("data/processed_data", "data/interim_data"),
        outputs=("data/interim_data", "provenance/stamps/master_timeline.json"),
        code=("src/data/build_master_timeline.py", "src/config.py"),
        params={"grid_hz": 10, "reference_driver": "G1_Subject1"},
        in_place=True,
    ),

    # ── quality control / leakage gates ─────────────────────────────────
    Stage(
        name="verify_column_uniformity",
        description="Assert every processed driver file has an identical column schema",
        module="src.qc.verify_column_uniformity",
        group="qc",
        inputs=("data/processed_data",),
        outputs=("outputs/reports/column_uniformity.md",),
        code=("src/qc/verify_column_uniformity.py",),
    ),
    Stage(
        name="verify_canlogger_bridge",
        description="Check gpsTime ↔ canloggerTime offset is stable for every driver",
        module="QC.verify_canlogger_bridge",
        group="qc",
        inputs=("data/processed_data",),
        outputs=("outputs/reports/canlogger_bridge_report.md",),
        code=("QC/verify_canlogger_bridge.py",),
    ),
    Stage(
        name="verify_sampling_rates",
        description="Per-signal native sampling rates across all drivers",
        module="QC.verify_sampling_rates",
        group="qc",
        inputs=("data/processed_data",),
        outputs=("outputs/reports/sampling_rate_all_drivers.md",),
        code=("QC/verify_sampling_rates.py",),
    ),
    Stage(
        name="eta2_audit_all_can",
        description="η² per raw CAN signal — the model-independent leakage gate",
        module="QC.verify_all_can_eta2",
        group="qc",
        inputs=("data/raw_data",),
        outputs=("outputs/reports/all_can_eta2.md",),
        code=("QC/verify_all_can_eta2.py", "src/qc/verification_of_excluded_spn.py"),
        params={"exclude_spns": _SPNS},
    ),
    Stage(
        name="verify_feature_leakage",
        description="η² per engineered feature — convergence check on the audit loop",
        module="src.qc.verify_feature_leakage",
        group="qc",
        inputs=("data/processed_data/feature_matrix.csv",),
        outputs=("outputs/reports/feature_leakage_audit.md",),
        code=("src/qc/verify_feature_leakage.py",),
    ),

    # ── features ────────────────────────────────────────────────────────
    Stage(
        name="build_feature_matrix",
        description="Per (driver, sector): 9 aggregates per CAN signal",
        module="src.features.build_feature_matrix",
        group="features",
        inputs=("data/interim_data", "provenance/stamps/master_timeline.json"),
        outputs=("data/processed_data/feature_matrix.csv",),
        code=("src/features/build_feature_matrix.py", "src/config.py"),
        params={"aggregates": ["mean", "median", "std", "min", "max", "p10", "p90",
                               "dmean", "dstd"]},
    ),
    Stage(
        name="build_windowed_feature_matrix",
        description="Per (driver, fixed-duration window): the same 9 aggregates",
        module="src.features.build_windowed_feature_matrix",
        group="features",
        inputs=("data/interim_data", "provenance/stamps/master_timeline.json"),
        outputs=("data/processed_data/windowed_feature_matrix_120s.csv",),
        code=("src/features/build_windowed_feature_matrix.py",),
        params={"window_seconds": 120, "overlap": 0},
    ),

    # ── baseline models ─────────────────────────────────────────────────
    Stage(
        name="build_baseline_classifier",
        description="Random Forest on sector features, 5-fold stratified CV + top-k",
        module="src.models.build_baseline_classifier",
        group="models",
        inputs=("data/processed_data/feature_matrix.csv",),
        outputs=("outputs/reports/baseline_rf_results.md",
                 "outputs/figures/baseline_rf_confusion_matrix.png"),
        code=("src/models/build_baseline_classifier.py",),
        params={"n_estimators": 300, "folds": 5, "seed": 42},
    ),
    Stage(
        name="run_window_sweep_chrono",
        description="Window-length sweep under the per-driver chronological split",
        module="src.models.run_window_sweep_chrono",
        group="models",
        inputs=("data/interim_data", "provenance/stamps/master_timeline.json"),
        outputs=("outputs/reports/window_sweep_chrono.md",
                 "outputs/figures/window_sweep_chrono_curve.png"),
        code=("src/models/run_window_sweep_chrono.py",),
        params={"train_end": 0.70, "test_start": 0.75, "seed": 42},
    ),
    Stage(
        name="build_pertick_baseline",
        description="Single-tick (100 ms) classification baseline",
        module="src.models.build_pertick_baseline",
        group="models",
        inputs=("data/interim_data", "provenance/stamps/master_timeline.json"),
        outputs=("outputs/reports/pertick_baseline_results.md",),
        code=("src/models/build_pertick_baseline.py",),
    ),

    # ── foundation-model track (planned) ────────────────────────────────
    Stage(
        name="build_windows",
        description="Audited signals → (window, timestep, channel) tensor for the encoder",
        module="src.features.build_windows",
        group="tsfm",
        inputs=("data/interim_data", "provenance/stamps/master_timeline.json"),
        outputs=("data/interim_data/windows_51s.npz",),
        code=("src/features/build_windows.py",),
        params={"window_seconds": 51, "grid_hz": 10, "resize_steps": 512},
        status=PLANNED,
    ),
    Stage(
        name="embed_mantis",
        description="Frozen Mantis encoder → per-window embeddings (intermediate layer)",
        module="src.models.embed_mantis",
        group="tsfm",
        inputs=("data/interim_data/windows_51s.npz",),
        outputs=("data/interim_data/embeddings_51s.npz",),
        code=("src/models/embed_mantis.py",),
        params={"checkpoint": "mantis-synthetic", "layer": "intermediate",
                "pooling": "cls+mean"},
        status=PLANNED,
    ),
    Stage(
        name="enroll_and_score",
        description="Prototypes for 36 known drivers + distance-based rejection of 10 unknown (AUROC)",
        module="src.models.enroll_and_score",
        group="tsfm",
        inputs=("data/interim_data/embeddings_51s.npz",),
        outputs=("outputs/reports/open_set_results.md",
                 "outputs/figures/open_set_auroc.png"),
        code=("src/models/enroll_and_score.py",),
        params={"n_known": 36, "n_unknown": 10, "partitions": 5,
                "train_end": 0.70, "test_start": 0.75},
        status=PLANNED,
    ),
    Stage(
        name="finetune_mantis",
        description="Fine-tune Mantis + MLP head; random vs synthetic vs real pre-training ablation",
        module="src.models.finetune_mantis",
        group="tsfm",
        inputs=("data/interim_data/windows_51s.npz",),
        outputs=("outputs/reports/finetune_results.md",),
        code=("src/models/finetune_mantis.py",),
        params={"head": "3-layer MLP (ELU, dropout)", "optimizer": "AdamW",
                "lr": 1e-4, "batch_size": 64, "weight_decay": 0.01},
        status=PLANNED,
    ),
)


def stage_by_name(name: str) -> Stage:
    """Look up one stage, raising a clear error if the name is unknown.

    Args:
        name: stage name as declared in STAGES.

    Returns:
        The matching Stage.
    """
    for stage in STAGES:
        if stage.name == name:
            return stage
    known = ", ".join(s.name for s in STAGES)
    raise KeyError(f"unknown stage {name!r}; known stages: {known}")


def producers() -> dict[str, str]:
    """Map each output path to the stage that produces it."""
    mapping: dict[str, str] = {}
    for stage in STAGES:
        for out in stage.outputs:
            mapping.setdefault(out, stage.name)
    return mapping


def dependencies(stage: Stage) -> list[str]:
    """Names of stages that must run before this one.

    Args:
        stage: the Stage to resolve.

    Returns:
        Upstream stage names, excluding the stage itself (in-place stages
        declare one of their own outputs as an input).
    """
    produced_by = producers()
    upstream = []
    for item in stage.inputs:
        owner = produced_by.get(item)
        if owner is None:
            # an input nobody produces is a root artifact, e.g. data/raw_data
            continue
        if owner != stage.name and owner not in upstream:
            upstream.append(owner)
    return upstream


def topological_order(names: list[str] | None = None) -> list[Stage]:
    """Order stages so every stage follows its dependencies.

    Args:
        names: restrict to these stages and their upstreams; None means all.

    Returns:
        Stages in a runnable order.
    """
    wanted = {s.name for s in STAGES} if names is None else set()
    if names is not None:
        queue = list(names)
        while queue:
            current = queue.pop()
            if current in wanted:
                continue
            wanted.add(current)
            queue.extend(dependencies(stage_by_name(current)))

    ordered: list[Stage] = []
    placed: set[str] = set()
    remaining = [s for s in STAGES if s.name in wanted]
    while remaining:
        ready = [s for s in remaining
                 if all(d in placed or d not in wanted for d in dependencies(s))]
        if not ready:                      # cycle: fall back to declaration order
            ready = [remaining[0]]
        for stage in ready:
            ordered.append(stage)
            placed.add(stage.name)
        remaining = [s for s in remaining if s.name not in placed]
    return ordered
