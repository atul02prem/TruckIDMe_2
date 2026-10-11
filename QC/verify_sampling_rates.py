"""Characterise each CAN signal's sampling rate three ways, to justify the
median-rate choice used for fast/slow classification.

For every CAN signal (via its paired TimeXXX column) we compute the inter-sample
gap Δt = diff(timestamps) and summarise it as:
  - mode Δt   -> native cadence (most common gap; truest ECU broadcast period)
  - median Δt -> robust typical gap (what build_processed_data uses); immune to
                 occasional log-off gaps
  - mean Δt   -> throughput = N/duration; DRAGGED DOWN by dropout/log-off, so its
                 reciprocal is the effective values-per-second, not the native rate
Plus max gap (biggest silence) and dropout % (how far throughput falls below the
native-cadence expectation).

Reading the report:
  - mode ≈ median ≈ mean  -> clean, continuously-broadcast signal.
  - mode ≈ median  >  mean -> native rate is fine; the mean is just paying for
                              dropout (see dropout %). Use median/mode, not mean.
  - mode ≠ median          -> genuinely multi-rate signal (e.g. fast driving /
                              slow idle); the fast/slow call needs care.

Source = the reference driver (G1S01), the same driver the fast-signal set is
frozen from, so the numbers match what the pipeline actually decides on.

Writes outputs/reports/sampling_rate_delta_t.md.

Run from repo root:
    python -m QC.verify_sampling_rates
"""

import re

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, OUT_REPORTS

# REF_DRIVER   = "G1_Subject1"
# DT_ROUND     = 3          # round Δt to milliseconds before taking the mode
# DROPOUT_FLAG = 5.0        # flag signals whose throughput is >5% below native
# _SIG_RE      = re.compile(r"^(\d+)\s")   # "190 Engine Speed ..." -> SPN 190


# def delta_t_stats(t: pd.Series) -> dict:
#     """Δt summary (seconds + Hz, three ways) for one timestamp column."""
#     t = t.dropna().sort_values().to_numpy()
#     if t.size < 3:
#         return {}
#     dt = np.diff(t)
#     dt = dt[dt > 0]

#     if dt.size == 0:
#         return {}

#     mode_dt   = pd.Series(np.round(dt, DT_ROUND)).value_counts().idxmax()
#     median_dt = float(np.median(dt))
#     mean_dt   = float(dt.mean())
#     max_gap   = float(dt.max())

#     span      = t[-1] - t[0] # total time span of the signal
#     # dropout: fraction of native-cadence intervals that never arrived.
#     expected  = span / mode_dt if mode_dt > 0 else np.nan # expected # of samples if no dropout
#     dropout   = max(0.0, 1.0 - dt.size / expected) * 100.0 if expected else np.nan

#     return {
#         "n":          int(t.size),
#         "mode_hz":    1.0 / mode_dt if mode_dt else np.nan,
#         "median_hz":  1.0 / median_dt if median_dt else np.nan,
#         "mean_hz":    1.0 / mean_dt if mean_dt else np.nan,
#         "mode_dt":    float(mode_dt),
#         "median_dt":  median_dt,
#         "mean_dt":    mean_dt,
#         "max_gap":    max_gap,
#         "dropout":    dropout,
#     }


# def build_report(csv_path) -> pd.DataFrame:
#     """One row per CAN signal with its Δt stats, sorted fast -> slow."""
#     df = pd.read_csv(csv_path)
#     time_cols = {int(m.group(1)): c
#                  for c in df.columns if (m := re.match(r"^Time(\d+)$", c))}

#     rows = []
#     for col in df.columns:
#         m = _SIG_RE.match(col)
#         if not m:
#             continue
#         spn = int(m.group(1))
#         tcol = time_cols.get(spn)
#         print(f"SPN {spn}: {col} -> {tcol}")
#         if tcol is None:
#             continue
#         stats = delta_t_stats(df[tcol])
#         if not stats:
#             continue
#         rows.append({"spn": spn, "signal": col, **stats})

#     return pd.DataFrame(rows).sort_values("mode_hz", ascending=False, ignore_index=True)


# # ── flagging: turn the docstring's pass/fail rules into machine checks ──────────
# FLAG_HEALTHY   = "🟢"
# FLAG_DROPOUT   = "🟡"
# FLAG_MULTIRATE = "🔴"
# MULTIRATE_TOL  = 0.10   # |median-mode|/mode above this => no stable native rate
# MAJORITY       = 0.50   # flag a signal only if the issue shows in >= this share of drivers


# def classify(mode_hz: float, median_hz: float, dropout: float) -> tuple[bool, bool]:
#     """(is_multirate, is_dropout) for one (driver, signal) Δt reading."""
#     multirate = abs(median_hz - mode_hz) / mode_hz > MULTIRATE_TOL if mode_hz else False
#     dropped   = dropout > DROPOUT_FLAG
#     return multirate, dropped


# def _driver_id(stem: str) -> str:
#     m = re.match(r"^G(\d+)_Subject(\d+)$", stem)
#     return f"G{m.group(1)}S{int(m.group(2)):02d}"


# def build_all_drivers_report() -> pd.DataFrame:
#     """Δt stats per CAN signal aggregated over every usable driver.

#     A signal is flagged only if its issue appears in >= MAJORITY of drivers, so a
#     single-driver fluke (e.g. one driver's start-of-drive gap) does not brand a
#     healthy signal. `native_std` = spread of native (mode) Hz across drivers.
#     """
#     from src.config import EXCLUDE_DRIVERS

#     header = pd.read_csv(DATA_PROCESSED / f"{REF_DRIVER}.csv", nrows=0).columns
#     names  = {int(m.group(1)): c for c in header if (m := _SIG_RE.match(c))}

#     per: dict[int, list] = {}
#     n_drivers = 0
#     for f in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
#         if _driver_id(f.stem) in EXCLUDE_DRIVERS:
#             print(_driver_id(f.stem), "excluded")
#             continue
#         n_drivers += 1
#         df = pd.read_csv(f, usecols=lambda c: bool(re.match(r"^Time(\d+)$", c)))
#         for col in df.columns:
#             spn = int(re.match(r"^Time(\d+)$", col).group(1))
#             if spn not in names:
#                 continue
#             s = delta_t_stats(df[col])
#             if s:
#                 per.setdefault(spn, []).append(s)

#     rows = []
#     for spn, recs in per.items():
#         modes = np.array([r["mode_hz"] for r in recs])
#         drop  = np.array([r["dropout"] for r in recs])
#         flags = [classify(r["mode_hz"], r["median_hz"], r["dropout"]) for r in recs]
#         pct_mr = np.mean([mr for mr, _ in flags])
#         pct_dp = np.mean([dp for _, dp in flags])

#         if pct_mr >= MAJORITY:
#             flag = FLAG_MULTIRATE
#         elif pct_dp >= MAJORITY:
#             flag = FLAG_DROPOUT
#         else:
#             flag = FLAG_HEALTHY

#         rows.append({
#             "flag": flag, "spn": spn, "signal": names[spn][:44],
#             "n_drivers": len(recs),
#             "native_hz": float(np.median(modes)), "native_std": float(modes.std()),
#             "dropout_med": float(np.median(drop)),
#             "pct_drop": pct_dp * 100.0, "pct_multirate": pct_mr * 100.0,
#         })

#     rep = pd.DataFrame(rows).sort_values("native_hz", ascending=False, ignore_index=True)
#     rep.attrs["n_drivers"] = n_drivers
#     return rep


# if __name__ == "__main__":
#     rep = build_all_drivers_report()
#     n_drivers = rep.attrs["n_drivers"]
#     flagged = rep[rep["flag"] != FLAG_HEALTHY]

#     OUT_REPORTS.mkdir(parents=True, exist_ok=True)
#     lines = [
#         "# CAN sampling rate — verified across all drivers",
#         "",
#         f"Source: {n_drivers} usable drivers (post `EXCLUDE_DRIVERS`). Δt stats are "
#         "computed per driver, then aggregated. A signal is flagged only if the issue "
#         f"appears in ≥ {int(MAJORITY*100)}% of drivers (structural, not a single-driver "
#         "fluke).",
#         "",
#         f"- {FLAG_MULTIRATE} **multi-rate** — |median−mode|/mode > "
#         f"{int(MULTIRATE_TOL*100)}% (no stable native rate) in a majority of drivers.",
#         f"- {FLAG_DROPOUT} **dropout** — throughput > {DROPOUT_FLAG:.0f}% below native "
#         "in a majority of drivers.",
#         f"- {FLAG_HEALTHY} healthy — mode ≈ median, low dropout.",
#         "",
#         "`native_std` = spread of native (mode) Hz across drivers: 0 = rock-stable, "
#         "large = no stable rate.",
#         "",
#         f"## ⚠️ Flags ({len(flagged)}) — read these first",
#         "",
#     ]
#     if len(flagged):
#         lines += ["| flag | SPN | Signal | native Hz | % drv dropout | % drv multi-rate | note |",
#                   "|:--:|--:|--|--:|--:|--:|--|"]
#         for r in flagged.itertuples(index=False):
#             note = ("no stable native rate (bursty / event-driven)"
#                     if r.flag == FLAG_MULTIRATE else
#                     f"state-conditional silence (~{r.dropout_med:.0f}% of samples absent)")
#             lines.append(f"| {r.flag} | {r.spn} | {r.signal} | {r.native_hz:.0f} | "
#                          f"{r.pct_drop:.0f}% | {r.pct_multirate:.0f}% | {note} |")
#     else:
#         lines.append("_None — every signal is healthy in a majority of drivers._")

#     lines += [
#         "",
#         "## Per-signal (all signals, sorted fast → slow)",
#         "",
#         "| flag | SPN | Signal | #drv | native Hz | native_std | dropout med% | "
#         "%drv drop>5 | %drv multi-rate |",
#         "|:--:|--:|--|--:|--:|--:|--:|--:|--:|",
#     ]
#     for r in rep.itertuples(index=False):
#         lines.append(f"| {r.flag} | {r.spn} | {r.signal} | {r.n_drivers} | "
#                      f"{r.native_hz:.0f} | {r.native_std:.2f} | {r.dropout_med:.1f} | "
#                      f"{r.pct_drop:.0f}% | {r.pct_multirate:.0f}% |")

#     out = OUT_REPORTS / "sampling_rate_all_drivers.md"
#     out.write_text("\n".join(lines) + "\n")

#     print(f"{len(rep)} signals across {n_drivers} drivers. "
#           f"Flagged (≥{int(MAJORITY*100)}% of drivers): {len(flagged)}")
#     for r in flagged.itertuples(index=False):
#         print(f"  {r.flag} SPN {r.spn:>4} {r.signal[:40]:40} "
#               f"drop {r.pct_drop:.0f}% / multirate {r.pct_multirate:.0f}%")
#     print(f"Report written to {out}")
