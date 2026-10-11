# """Verify the EXCLUDE_SPNS decisions by visualizing how each excluded signal
# varies across drivers.

# Leakage hypothesis: a signal that fingerprints the *trip* (cumulative counter,
# trip-state level, ambient condition) will show each driver occupying a
# distinct, non-overlapping value band. A genuinely behavioural signal will show
# heavy overlap between drivers.

# We quantify this with eta-squared (η²) = between-driver variance / total
# variance — the fraction of a signal's variance explained by driver identity:
#     η² → 1.0  : each driver ≈ a distinct constant → strong trip fingerprint
#                 → exclusion justified.
#     η² → 0.0  : drivers overlap → behavioural → RECONSIDER excluding it.

# Reads from data/raw_data/ (excluded columns still present there, unlike
# processed_data/). Applies EXCLUDE_DRIVERS.

# Outputs:
#   - outputs/figures/excluded_spn_verification/<spn>_<name>.png   (per-SPN boxplots)
#   - outputs/figures/excluded_spn_verification/_eta2_summary.png  (ranked η² bar chart)
#   - outputs/reports/excluded_spn_verification.md                 (η² table + verdicts)

# Run from project root:
#     python -m src.qc.verification_of_excluded_spn
# """

# import re
# from pathlib import Path

# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd

# from src.config import DATA_RAW, EXCLUDE_DRIVERS, EXCLUDE_SPNS, OUT_FIGURES, OUT_REPORTS


# _DRIVER_ID_RE   = re.compile(r"^G(\d+)_Subject(\d+)$")
# # GROUP_COLORS    = {"G1": "#1f77b4", "G2": "#ff7f0e", "G3": "#2ca02c"}


# def filename_to_driver_id(stem: str) -> str:
#     """Convert 'G1_Subject4' to canonical 'G1S04'."""
#     m = _DRIVER_ID_RE.match(stem)
#     if not m:
#         raise ValueError(f"Cannot parse driver ID from {stem!r}")
#     return f"G{m.group(1)}S{int(m.group(2)):02d}"


# def map_spns_to_columns(header_cols: list[str], spns: set[int]) -> dict[int, str]:
#     """Find the signal column name for each excluded SPN in a CSV header.

#     Matches a column that starts with '<spn> ' (SPN followed by whitespace),
#     which selects the signal column and never its 'TimeXXX' partner. If an SPN
#     has a duplicate '...CAN0' variant, the non-CAN0 column is preferred.

#     Args:
#         header_cols: column names of a raw driver CSV.
#         spns: the set of excluded SPN integers.

#     Returns:
#         Dict mapping SPN -> column name, for SPNs present in this CSV.
#     """
#     mapping: dict[int, str] = {}
#     for spn in spns:
#         pattern = re.compile(rf"^{spn}\s")
#         matches = [c for c in header_cols if pattern.match(c)]
#         if not matches:
#             continue
#         non_can0 = [c for c in matches if not c.endswith("CAN0")]
#         mapping[spn] = non_can0[0] if non_can0 else matches[0]
#     return mapping


# def collect_excluded_signal_values(
#     raw_dir: Path,
#     exclude_drivers: set[str],
#     spns: set[int],
# ) -> tuple[dict[int, dict[str, np.ndarray]], dict[int, str]]:
#     """Read excluded-SPN values per driver from the raw CSVs.

#     Args:
#         raw_dir: directory of raw driver CSVs.
#         exclude_drivers: canonical driver IDs to skip.
#         spns: excluded SPN integers.

#     Returns:
#         (per_spn_driver_values, spn_names):
#           per_spn_driver_values[spn][driver_id] = full non-null value array
#           spn_names[spn] = the human-readable signal column name
#     """
#     per_spn: dict[int, dict[str, np.ndarray]] = {spn: {} for spn in spns}
#     spn_names: dict[int, str] = {}

#     for csv_file in sorted(raw_dir.glob("G*_Subject*.csv")):
#         driver_id = filename_to_driver_id(csv_file.stem)
#         if driver_id in exclude_drivers:
#             continue

#         header = pd.read_csv(csv_file, nrows=0).columns.tolist()
#         spn_to_col = map_spns_to_columns(header, spns)
#         if not spn_to_col:
#             continue

#         df = pd.read_csv(csv_file, usecols=list(spn_to_col.values()))
#         for spn, col in spn_to_col.items():
#             vals = df[col].dropna().to_numpy(dtype=float)
#             if vals.size == 0:
#                 continue
#             per_spn[spn][driver_id] = vals
#             spn_names.setdefault(spn, col)

#         print(f"  read {driver_id}: {len(spn_to_col)} excluded signals")

#     return per_spn, spn_names


# def eta_squared(driver_values: dict[str, np.ndarray]) -> float:
#     """Fraction of a signal's variance explained by driver identity (0..1).

#     η² = SS_between / SS_total, computed across the pooled per-driver samples.

#     Args:
#         driver_values: driver_id -> value array for one signal.

#     Returns:
#         η² in [0, 1], or NaN if fewer than 2 drivers or zero total variance.
#     """
#     groups = [v for v in driver_values.values() if v.size > 0]
#     if len(groups) < 2:
#         return float("nan")
#     all_vals = np.concatenate(groups)
#     grand_mean = all_vals.mean()
#     ss_total = float(((all_vals - grand_mean) ** 2).sum())
#     if ss_total == 0.0:
#         return float("nan")
#     ss_between = float(sum(g.size * (g.mean() - grand_mean) ** 2 for g in groups))
#     return ss_between / ss_total


# def plot_spn_boxplots(
#     spn: int,
#     name: str,
#     driver_values: dict[str, np.ndarray],
#     eta2: float,
#     out_path: Path,
# ) -> None:
#     """Boxplot of one excluded signal, one box per driver, ordered by group."""
#     drivers = sorted(driver_values.keys())
#     data = [driver_values[d] for d in drivers]
#     colors = [GROUP_COLORS.get(d[:2], "#888888") for d in drivers]

#     fig, ax = plt.subplots(figsize=(16, 7))
#     bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6)
#     for patch, color in zip(bp["boxes"], colors):
#         patch.set_facecolor(color)
#         patch.set_alpha(0.6)
#     for median in bp["medians"]:
#         median.set_color("black")

#     ax.set_xticks(range(1, len(drivers) + 1))
#     ax.set_xticklabels(drivers, rotation=90, fontsize=7)
#     ax.set_ylabel(name, fontsize=9)
#     ax.set_title(
#         f"SPN {spn} — {name}\n"
#         f"η² = {eta2:.3f}  (between-driver variance / total; 1.0 = perfect trip separation)",
#         fontsize=11,
#     )
#     handles = [
#         plt.Rectangle((0, 0), 1, 1, fc=c, alpha=0.6) for c in GROUP_COLORS.values()
#     ]
#     ax.legend(handles, GROUP_COLORS.keys(), title="Group", loc="upper right")
#     ax.grid(True, axis="y", alpha=0.3)
#     fig.tight_layout()
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     fig.savefig(out_path, dpi=130)
#     plt.close(fig)


# def plot_eta2_summary(eta2_by_spn: dict[int, float], spn_names: dict[int, str],
#                       out_path: Path) -> None:
#     """Ranked horizontal bar chart of η² across all excluded SPNs."""
#     items = sorted(
#         [(spn, e) for spn, e in eta2_by_spn.items() if not np.isnan(e)],
#         key=lambda kv: kv[1],
#     )
#     spns   = [f"{spn} {spn_names[spn][:38]}" for spn, _ in items]
#     values = [e for _, e in items]
#     colors = ["#d62728" if v < 0.5 else "#ff7f0e" if v < 0.9 else "#2ca02c"
#               for v in values]

#     fig, ax = plt.subplots(figsize=(11, max(8, len(items) * 0.28)))
#     ax.barh(range(len(items)), values, color=colors)
#     ax.set_yticks(range(len(items)))
#     ax.set_yticklabels(spns, fontsize=7)
#     ax.set_xlabel("η²  (between-driver variance / total variance)")
#     ax.set_xlim(0, 1)
#     ax.axvline(0.9, color="green", ls="--", lw=1, alpha=0.7)
#     ax.axvline(0.5, color="red",   ls="--", lw=1, alpha=0.7)
#     ax.set_title("Excluded-SPN separability by driver\n"
#                  "green ≥0.9 strong leak · orange 0.5–0.9 · red <0.5 (behavioural — reconsider)")
#     ax.grid(True, axis="x", alpha=0.3)
#     fig.tight_layout()
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     fig.savefig(out_path, dpi=140)
#     plt.close(fig)


# def save_report(eta2_by_spn: dict[int, float], spn_names: dict[int, str],
#                 out_path: Path) -> None:
#     """Write the η² verdict table sorted by separability descending."""
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     rows = sorted(
#         [(spn, e) for spn, e in eta2_by_spn.items()],
#         key=lambda kv: (np.isnan(kv[1]), -(kv[1] if not np.isnan(kv[1]) else 0)),
#     )

#     def verdict(e: float) -> str:
#         if np.isnan(e):
#             return "n/a (constant / single driver)"
#         if e >= 0.9:
#             return "STRONG LEAK — exclusion well justified"
#         if e >= 0.5:
#             return "SUBSTANTIAL separation — exclusion defensible"
#         return "OVERLAPPING — behavioural, RECONSIDER excluding"

#     lines = [
#         "# TruckIDMe — Excluded-SPN Verification (driver separability)",
#         "",
#         "For each excluded SPN, η² = fraction of the signal's variance explained",
#         "by driver identity, computed across all usable drivers' raw values.",
#         "High η² confirms the signal fingerprints the trip (exclusion justified);",
#         "low η² flags a signal that overlaps across drivers (behavioural).",
#         "",
#         "| SPN | Signal | η² | Verdict |",
#         "|---|---|---:|---|",
#     ]
#     for spn, e in rows:
#         e_str = f"{e:.3f}" if not np.isnan(e) else "—"
#         lines.append(f"| {spn} | `{spn_names.get(spn, '?')}` | {e_str} | {verdict(e)} |")
#     out_path.write_text("\n".join(lines) + "\n")


# if __name__ == "__main__":
#     print(f"Verifying {len(EXCLUDE_SPNS)} excluded SPNs across drivers in {DATA_RAW}")
#     print(f"Excluded drivers: {EXCLUDE_DRIVERS}")
#     print()

#     per_spn, spn_names = collect_excluded_signal_values(
#         DATA_RAW, EXCLUDE_DRIVERS, EXCLUDE_SPNS,
#     )

    # print()
    # fig_dir = OUT_FIGURES / "excluded_spn_verification"
    # eta2_by_spn: dict[int, float] = {}
    # for spn in sorted(per_spn.keys()):
    #     driver_values = per_spn[spn]
    #     if not driver_values:
    #         print(f"  SPN {spn}: no data found, skipping")
    #         continue
    #     eta2 = eta_squared(driver_values)
    #     eta2_by_spn[spn] = eta2
    #     name = spn_names.get(spn, str(spn))
    #     safe_name = re.sub(r"[^\w]+", "_", name)[:50]
    #     plot_spn_boxplots(spn, name, driver_values, eta2,
    #                       fig_dir / f"{spn}_{safe_name}.png")
    #     print(f"  SPN {spn:>4} η²={eta2:.3f}  {name}")

    # plot_eta2_summary(eta2_by_spn, spn_names, fig_dir / "_eta2_summary.png")
    # save_report(eta2_by_spn, spn_names, OUT_REPORTS / "excluded_spn_verification.md")

    # print()
    # print(f"Per-SPN boxplots + summary written to {fig_dir}")
    # print(f"Report written to {OUT_REPORTS / 'excluded_spn_verification.md'}")
