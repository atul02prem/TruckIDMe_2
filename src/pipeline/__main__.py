"""Command-line entry point for the pipeline.

    python -m src.pipeline status            # what is fresh, stale or planned
    python -m src.pipeline graph             # regenerate the README overview
    python -m src.pipeline run <stage>...    # run stages and their stale upstreams
    python -m src.pipeline run --all         # run the whole pipeline
    python -m src.pipeline adopt <stage>     # record pre-existing outputs (one-off)
"""

import argparse
import sys

from src.pipeline import render, runner


def main() -> int:
    """Parse arguments and dispatch to the runner or renderer."""
    parser = argparse.ArgumentParser(prog="python -m src.pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="show stage freshness")
    graph = sub.add_parser("graph", help="regenerate the README pipeline section")
    graph.add_argument("--print", action="store_true", help="print instead of writing")

    adopt = sub.add_parser("adopt", help="record existing outputs as provenance (one-off)")
    adopt.add_argument("stages", nargs="+", help="stage names whose outputs already exist")

    run = sub.add_parser("run", help="run stages in dependency order")
    run.add_argument("stages", nargs="*", help="stage names (default: --all required)")
    run.add_argument("--all", action="store_true", help="run every built stage")
    run.add_argument("--force", action="store_true", help="ignore freshness")
    run.add_argument("--dry-run", action="store_true", help="show the plan only")

    args = parser.parse_args()

    if args.command == "status":
        print(render.status_table())
        return 0

    if args.command == "graph":
        if args.print:
            print(render.block())
            return 0
        path = render.inject(render.prov.ROOT / "README.md")
        print(f"wrote pipeline overview into {path.name}")
        return 0

    if args.command == "adopt":
        return runner.adopt(args.stages)

    if not args.stages and not args.all:
        parser.error("name at least one stage, or pass --all")
    targets = None if args.all else args.stages
    return runner.run(targets, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
