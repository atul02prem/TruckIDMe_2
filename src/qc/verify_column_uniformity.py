# """Audit column uniformity across the 45 usable processed driver CSVs.

# A reference driver (alphabetically first non-excluded) is chosen; every other
# usable driver's column set is diffed against it. Drivers whose column set
# differs from the reference are reported, and a markdown artifact is written
# to outputs/reports/ for documentation.

# Run from project root:
#     python -m playground.exp
# """

# import re
# from pathlib import Path

# import pandas as pd

# from src.config import DATA_PROCESSED, EXCLUDE_DRIVERS, OUT_REPORTS


# _DRIVER_ID_RE = re.compile(r"^G(\d+)_Subject(\d+)$")


# def filename_to_driver_id(stem: str) -> str:
#     """Convert a CSV filename stem 'G1_Subject4' to canonical 'G1S04'."""
#     m = _DRIVER_ID_RE.match(stem)
#     if not m:
#         raise ValueError(f"Cannot parse driver ID from {stem!r}")
#     return f"G{m.group(1)}S{int(m.group(2)):02d}"


# def audit_column_uniformity(data_dir: Path, exclude_drivers: set[str]) -> dict:
#     """Diff every non-excluded driver's column set against a reference driver.

#     Args:
#         data_dir: directory of processed driver CSVs.
#         exclude_drivers: canonical driver IDs to skip (e.g. {'G1S04'}).

#     Returns:
#         Dict with reference driver id, reference column list, list of
#         per-driver diffs (driver_id, missing, extra), and total usable count.
#     """
#     files_by_id = {
#         filename_to_driver_id(f.stem): f
#         for f in sorted(data_dir.glob("G*_Subject*.csv"))
#     }
#     usable = {d: f for d, f in files_by_id.items() if d not in exclude_drivers}

#     ref_driver = next(iter(sorted(usable.keys())))
#     ref_cols = pd.read_csv(usable[ref_driver], nrows=0).columns.tolist()
#     ref_set = set(ref_cols)

#     diffs = []
#     for driver, f in sorted(usable.items()):
#         if driver == ref_driver:
#             continue
#         cols = set(pd.read_csv(f, nrows=0).columns)
#         missing = sorted(ref_set - cols)
#         extra = sorted(cols - ref_set)
#         if missing or extra:
#             diffs.append({"driver": driver, "missing": missing, "extra": extra})

#     return {
#         "n_usable_drivers": len(usable),
#         "reference_driver": ref_driver,
#         "reference_cols":   ref_cols,
#         "diffs":            diffs,
#     }


# def save_uniformity_artifact(result: dict, out_path: Path) -> None:
#     """Write the uniformity audit result as a markdown report."""
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     n = result["n_usable_drivers"]
#     ref = result["reference_driver"]
#     ref_cols = result["reference_cols"]
#     diffs = result["diffs"]

#     lines = [
#         "# TruckIDMe — Processed Column Uniformity Audit",
#         "",
#         f"**Usable drivers audited:** {n} (after applying EXCLUDE_DRIVERS)",
#         f"**Reference driver:** `{ref}`",
#         f"**Reference column count:** {len(ref_cols)}",
#         f"**Drivers with differing column sets:** {len(diffs)}",
#         "",
#     ]

#     if not diffs:
#         lines += [
#             "## Result",
#             "",
#             "All usable drivers have an **identical** column set to the reference.",
#             "",
#         ]
#     else:
#         lines += [
#             "## Drivers with column-set differences",
#             "",
#             "| Driver | Missing vs reference | Extra vs reference |",
#             "|---|---|---|",
#         ]
#         for d in diffs:
#             m_str = "<br>".join(f"`{c}`" for c in d["missing"]) if d["missing"] else "—"
#             e_str = "<br>".join(f"`{c}`" for c in d["extra"])   if d["extra"]   else "—"
#             lines.append(f"| `{d['driver']}` | {m_str} | {e_str} |")
#         lines.append("")

#     lines += [
#         "## Reference column list",
#         "",
#         "<details><summary>Click to expand</summary>",
#         "",
#         "```",
#         *ref_cols,
#         "```",
#         "",
#         "</details>",
#         "",
#     ]
#     out_path.write_text("\n".join(lines) + "\n")


# if __name__ == "__main__":
#     print(f"Auditing column uniformity in {DATA_PROCESSED}")
#     print(f"Excluded drivers: {EXCLUDE_DRIVERS}")
#     print()

#     result = audit_column_uniformity(DATA_PROCESSED, EXCLUDE_DRIVERS)
#     print(f"Reference: {result['reference_driver']}  "
#           f"({len(result['reference_cols'])} cols)")
#     print(f"Usable drivers audited: {result['n_usable_drivers']}")
#     print()

#     if not result["diffs"]:
#         print("All usable drivers have IDENTICAL column sets to the reference.")
#     else:
#         print(f"{len(result['diffs'])} drivers differ:")
#         for d in result["diffs"]:
#             print(f"  {d['driver']}:")
#             if d["missing"]:
#                 print(f"    missing: {d['missing']}")
#             if d["extra"]:
#                 print(f"    extra:   {d['extra']}")

#     artifact_path = OUT_REPORTS / "column_uniformity.md"
#     save_uniformity_artifact(result, artifact_path)
#     print()
#     print(f"Artifact written to {artifact_path}")
