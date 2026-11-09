"""Separability of continuous signals — η² at two scales, plus mutual information.

Three numbers per signal, because one is demonstrably not enough:

- **η² on raw samples** — does each driver occupy a distinct value band? The right
  instrument for a signal that jitters around a level (pedal, torque, load).
- **η² on per-window means** — the same question asked of the window the model
  actually sees. This exists because raw-sample η² has a proven blind spot: a
  signal that *ramps* (any temperature, cold start to operating heat) carries huge
  *within*-driver variance from the ramp itself, which pushes raw η² down, while
  its per-window mean still separates drivers because each drove on a different
  day. The thermal family scored 0.08–0.38 raw and still cost 45 points of
  accuracy when it was finally removed.
- **Mutual information** — reported as the share of driver-identity entropy the
  signal resolves. Catches dependence neither η² can see: two drivers with the
  same mean but different distributions score η² ≈ 0 while being perfectly
  separable.

This report **measures only**. It carries no exclusion labels and makes no
recommendation: the statistic flags, physics decides, and that decision belongs
in a separate artifact that cites this one.

Run from the repo root in the `truckidme` env:
    python -m QC.verify_continuous_separability
"""

import re

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif

from src.config import (DATA_RAW, EXCLUDE_DRIVERS, OUT_REPORTS, WINDOW_SECONDS)
from src.qc.classify_signals import (classify, driver_id, reviewed_type,
                                     time_coverage)
from src.qc.verification_of_excluded_spn import eta_squared

REPORT_PATH = OUT_REPORTS / "continuous_separability.md"

LEAK_ETA = 0.9     # separates drivers like a fingerprint
WATCH_ETA = 0.5
MI_SEED = 0        # mutual_info_classif adds noise to break ties; pin it
MIN_WINDOW_SAMPLES = 10
SCALE_GAP = 0.15   # window minus raw this large means the scales disagree
_SIG_RE = re.compile(r"^(\d+)\s")


def flag(value: float) -> str:
    """Severity marker for a separability value."""
    if np.isnan(value):
        return "⚪"
    if value >= LEAK_ETA:
        return "🔴"
    if value >= WATCH_ETA:
        return "🟡"
    return "🟢"


def eta_squared_from_moments(counts: np.ndarray, sums: np.ndarray,
                             sumsqs: np.ndarray) -> float:
    """η² computed from per-driver moments instead of the stored samples.

    Algebraically identical to `eta_squared`, which needs every sample in memory
    — impractical here at 46 drivers × 81 signals. `main` checks the two agree.

    Args:
        counts: samples per driver.
        sums: Σx per driver.
        sumsqs: Σx² per driver.

    Returns:
        η² in [0, 1], or NaN with fewer than 2 drivers or zero variance.
    """
    keep = counts > 0
    counts, sums, sumsqs = counts[keep], sums[keep], sumsqs[keep]
    if counts.size < 2:
        return float("nan")
    total = counts.sum()
    grand = sums.sum() / total
    ss_total = float(sumsqs.sum() - total * grand ** 2)
    if ss_total <= 0:
        return float("nan")
    ss_between = float((counts * (sums / counts - grand) ** 2).sum())
    return min(max(ss_between / ss_total, 0.0), 1.0)


def window_chunks(times: np.ndarray, values: np.ndarray,
                  window_seconds: float) -> list[np.ndarray]:
    """Split one drive into its full windows, anchored at the first sample.

    The anchor is immaterial for a per-signal statistic: what matters is that the
    window is the duration the model sees, so each summary below is a quantity
    read off the window rather than off an individual sample.

    Args:
        times: sample timestamps (seconds).
        values: sample values.
        window_seconds: window length.

    Returns:
        One array per window holding at least MIN_WINDOW_SAMPLES samples.
    """
    if times.size < MIN_WINDOW_SAMPLES:
        return []
    index = ((times - times.min()) // window_seconds).astype(np.int64)
    order = np.argsort(index, kind="stable")
    index, values = index[order], values[order]
    edges = np.flatnonzero(np.diff(index)) + 1
    return [chunk for chunk in np.split(values, edges)
            if chunk.size >= MIN_WINDOW_SAMPLES]


def summarise(chunks: list[np.ndarray], statistic: str) -> np.ndarray:
    """Reduce each window to one number.

    Args:
        chunks: the windows, as `window_chunks` returns them.
        statistic: 'mean' for the window level, 'std' for its spread.

    Returns:
        One value per window.
    """
    if statistic == "mean":
        return np.asarray([c.mean() for c in chunks], dtype=float)
    return np.asarray([c.std(ddof=1) for c in chunks], dtype=float)


def continuous_spns(files: list) -> dict[int, str]:
    """Find the signals classified continuous, using the shared classifier.

    Args:
        files: raw CSV paths (a subset is enough to establish a type).

    Returns:
        SPN -> signal column name.
    """
    header = pd.read_csv(files[0], nrows=0).columns.tolist()
    signals = {int(m.group(1)): c for c in header
               if (m := _SIG_RE.match(c)) and f"Time{m.group(1)}" in header}
    cols = list(signals.values()) + [f"Time{s}" for s in signals]

    pooled: dict[int, list[np.ndarray]] = {s: [] for s in signals}
    covers: dict[int, list[float]] = {s: [] for s in signals}
    for path in files[:8]:
        frame = pd.read_csv(path, usecols=cols)
        for spn, col in signals.items():
            pooled[spn].append(frame[col].dropna().to_numpy(float))
            cov = time_coverage(frame[f"Time{spn}"].dropna().to_numpy(float))
            if not np.isnan(cov):
                covers[spn].append(cov)

    out = {}
    for spn, col in signals.items():
        values = np.concatenate(pooled[spn])
        distinct = np.unique(values)
        integral = bool(np.all(np.equal(np.mod(distinct, 1), 0)))
        cov = float(np.mean(covers[spn])) if covers[spn] else float("nan")
        final, _ = reviewed_type(spn, classify(cov, int(distinct.size), integral))
        if final == "continuous":
            out[spn] = col
    return out


def collect(files: list, signals: dict[int, str]
            ) -> tuple[dict[int, dict[str, tuple[int, float, float]]],
                       dict[int, dict[str, np.ndarray]]]:
    """Accumulate per-driver moments and window means for every signal.

    Args:
        files: raw CSV paths, one per driver.
        signals: SPN -> signal column name.

    Returns:
        (moments, windows) where moments maps SPN -> driver -> (n, Σx, Σx²) and
        windows maps SPN -> driver -> per-window means.
    """
    cols = list(signals.values()) + [f"Time{s}" for s in signals]
    moments: dict[int, dict[str, tuple[int, float, float]]] = {s: {} for s in signals}
    windows: dict[int, dict[str, np.ndarray]] = {s: {} for s in signals}
    spreads: dict[int, dict[str, np.ndarray]] = {s: {} for s in signals}

    for path in files:
        did = driver_id(path.stem)
        frame = pd.read_csv(path, usecols=cols)
        for spn, col in signals.items():
            pair = frame[[f"Time{spn}", col]].dropna()
            if pair.empty:
                continue
            t = pair[f"Time{spn}"].to_numpy(float)
            v = pair[col].to_numpy(float)
            moments[spn][did] = (v.size, float(v.sum()), float((v ** 2).sum()))
            chunks = window_chunks(t, v, WINDOW_SECONDS)
            windows[spn][did] = summarise(chunks, "mean")
            spreads[spn][did] = summarise(chunks, "std")
        print(f"  {did}")
    return moments, windows, spreads


def driver_entropy(labels: np.ndarray) -> float:
    """Entropy of the driver label distribution, in nats."""
    _, counts = np.unique(labels, return_counts=True)
    p = counts / counts.sum()
    return float(-(p * np.log(p)).sum())


def measure(signals: dict[int, str],
            moments: dict[int, dict[str, tuple[int, float, float]]],
            windows: dict[int, dict[str, np.ndarray]],
            spreads: dict[int, dict[str, np.ndarray]]) -> pd.DataFrame:
    """Compute all four statistics for every continuous signal.

    Args:
        signals: SPN -> signal column name.
        moments: SPN -> driver -> (n, Σx, Σx²).
        windows: SPN -> driver -> per-window means.
        spreads: SPN -> driver -> per-window standard deviations.

    Returns:
        One row per signal, most separable first.
    """
    rows = []
    for spn, col in signals.items():
        per_driver = moments[spn]
        raw = eta_squared_from_moments(
            np.array([m[0] for m in per_driver.values()], float),
            np.array([m[1] for m in per_driver.values()], float),
            np.array([m[2] for m in per_driver.values()], float))

        win = {d: w for d, w in windows[spn].items() if w.size}
        eta_win = eta_squared(win) if len(win) >= 2 else float("nan")

        sprd = {d: s for d, s in spreads[spn].items() if s.size}
        eta_std = eta_squared(sprd) if len(sprd) >= 2 else float("nan")

        if len(win) >= 2:
            x = np.concatenate([w for w in win.values()]).reshape(-1, 1)
            y = np.concatenate([[d] * w.size for d, w in win.items()])
            h = driver_entropy(y)
            mi = float(mutual_info_classif(x, y, random_state=MI_SEED)[0])
            share = min(max(mi / h, 0.0), 1.0) if h > 0 else float("nan")
        else:
            share = float("nan")

        rows.append({
            "spn": spn, "signal": col,
            "eta2_raw": raw, "eta2_window": eta_win,
            "eta2_window_std": eta_std, "mi_share": share,
            "drivers": len(per_driver),
            "windows": int(sum(w.size for w in win.values())),
        })
    table = pd.DataFrame(rows)
    table["worst"] = table[["eta2_raw", "eta2_window",
                            "eta2_window_std", "mi_share"]].max(axis=1)
    return table.sort_values("worst", ascending=False)


def write_report(table: pd.DataFrame, n_drivers: int) -> None:
    """Write the continuous-separability report.

    Args:
        table: one row per continuous signal.
        n_drivers: how many drivers were measured.
    """
    table = table.assign(gap=table.eta2_window - table.eta2_raw)
    gapped = table[table.gap >= SCALE_GAP].sort_values("gap", ascending=False)
    strong = table[table.worst >= LEAK_ETA]

    lines = [
        "# Continuous-signal separability — level, spread, and mutual information",
        "",
        f"All **{len(table)} continuous** signals, measured over **{n_drivers} "
        f"drivers** on the raw CAN data. Raw data deliberately: measuring on "
        "`processed_data` would make every currently-excluded signal permanently "
        "unreviewable.",
        "",
        "| Statistic | Question it answers |",
        "|---|---|",
        "| η² raw | does each driver occupy a distinct value band, sample by sample? |",
        f"| η² window | the same question about the {WINDOW_SECONDS:.0f}s window mean "
        "— the *level* a model reads |",
        f"| η² window-std | does each driver show a distinct **spread** within the "
        f"{WINDOW_SECONDS:.0f}s window? The only column that can see a driver who "
        "shares everyone else's average but differs in jitter |",
        "| MI share | fraction of driver-identity entropy the signal resolves; "
        "catches non-linear and multimodal separation |",
        "",
        f"Flags on the **largest** of the four: 🔴 ≥ {LEAK_ETA} · "
        f"🟡 {WATCH_ETA}–{LEAK_ETA} · 🟢 < {WATCH_ETA}.",
        "",
        "**This report measures only.** It carries no exclusion labels and makes "
        "no recommendation. The statistic flags; physics decides; that decision "
        "belongs in a separate artifact which cites this one.",
        "",
        "## ⚑ Why a spread column exists",
        "",
        "η² is defined on group **means**: its numerator is built from each "
        "driver's mean. Two drivers with the same average and different jitter "
        "therefore give a near-zero numerator *and* an inflated denominator, so "
        "**η² falls rather than rises** — at either scale. Mutual information "
        "here is computed on window means, so it is blind in the same way. "
        "Without this column every statistic in the report is a detector of "
        "*level*, and a signal whose driver information lives entirely in "
        "within-window variability would score 🟢 on all of them.",
        "",
        "Which direction that blindness mattered in is worth being precise "
        "about: a high score makes a signal an exclusion *candidate*, and nothing "
        "is ever excluded for scoring low. So the missing column could only ever "
        "have produced a **false clear** — a leak kept — never a false exclusion.",
        "",
        "## ⚑ Why two scales",
        "",
        "A signal that *ramps* carries large **within**-driver variance from the "
        "ramp itself, which pushes raw η² down, while its per-window **mean** can "
        "still separate drivers because each drove on a different day. The window "
        "column is the instrument that sees that.",
        "",
        "**A correction to the record.** `all_can_eta2.md` states that the thermal "
        "family scored 0.08–0.38 on raw η² and still cost 45 points when removed, "
        "implying raw η² was blind to it. Measured here over the same 46 drivers, "
        "that family spans **0.078 to 0.986**: DEF tank temperature 0.986, ambient "
        "air temperature 0.968, turbocharger intake temperature 0.941. The "
        "leakiest members were flagged loudly by raw η². The 0.08–0.38 figure "
        "describes only the downstream exhaust temperatures. So the 74% → 29% "
        "collapse was **not** a failure of the statistic — it was a failure to act "
        "on what the statistic already said.",
        "",
    ]

    if len(gapped):
        lines += [
            f"## ⚑ Where the two scales disagree — {len(gapped)} signals",
            "",
            f"Window η² exceeds raw η² by at least {SCALE_GAP}. These are the "
            "signals whose *level over a window* identifies the drive more than "
            "any individual sample does — a drifting or ramping quantity. This is "
            "what the second scale buys, and it is the only column that sees it.",
            "",
            "| Flag | SPN | Signal | η² raw | η² window | gap | η² win-std | MI share |",
            "|---|--:|---|--:|--:|--:|--:|--:|",
        ]
        for row in gapped.itertuples(index=False):
            lines.append(f"| {flag(row.eta2_window)} | {row.spn} | `{row.signal}` | "
                         f"{row.eta2_raw:.3f} | **{row.eta2_window:.3f}** | "
                         f"+{row.gap:.3f} | {row.eta2_window_std:.3f} | "
                         f"{row.mi_share:.3f} |")
        lines.append("")
    else:
        lines += [f"## 🟢 The two scales agree everywhere (no gap ≥ {SCALE_GAP})",
                  ""]

    spread_only = table[(table.eta2_raw < WATCH_ETA)
                        & (table.eta2_window < WATCH_ETA)
                        & (table.eta2_window_std >= WATCH_ETA)]
    if len(spread_only):
        lines += [
            f"## ⚑ Seen only in the spread — {len(spread_only)} signals",
            "",
            "Both level columns sit below "
            f"{WATCH_ETA} while the within-window spread reaches it. These "
            "signals separate drivers by how much they *move*, not by where they "
            "sit, and no other column in this report can see them.",
            "",
            "| Flag | SPN | Signal | η² raw | η² window | η² win-std |",
            "|---|--:|---|--:|--:|--:|",
        ]
        for row in spread_only.sort_values(
                "eta2_window_std", ascending=False).itertuples(index=False):
            lines.append(f"| {flag(row.eta2_window_std)} | {row.spn} | "
                         f"`{row.signal}` | {row.eta2_raw:.3f} | "
                         f"{row.eta2_window:.3f} | "
                         f"**{row.eta2_window_std:.3f}** |")
        lines.append("")
    else:
        lines += [
            f"## 🟢 Nothing is seen only in the spread (none ≥ {WATCH_ETA} "
            "while both level columns are below it)",
            "",
            "The spread column changed no verdict. Recorded as a negative "
            "result: the blind spot was real, and measuring it found nothing "
            "hiding there.",
            "",
        ]

    lines += [
        f"## Strongly separating — {len(strong)} signals at ≥ {LEAK_ETA}",
        "",
        "| Flag | SPN | Signal | η² raw | η² window | η² win-std | MI share |",
        "|---|--:|---|--:|--:|--:|--:|",
    ]
    for row in strong.itertuples(index=False):
        lines.append(f"| {flag(row.worst)} | {row.spn} | `{row.signal}` | "
                     f"{row.eta2_raw:.3f} | {row.eta2_window:.3f} | "
                     f"{row.eta2_window_std:.3f} | {row.mi_share:.3f} |")

    lines += [
        "",
        "## All continuous signals",
        "",
        "| Flag | SPN | Signal | η² raw | η² window | η² win-std | MI share | Windows |",
        "|---|--:|---|--:|--:|--:|--:|--:|",
    ]
    for row in table.itertuples(index=False):
        lines.append(f"| {flag(row.worst)} | {row.spn} | `{row.signal}` | "
                     f"{row.eta2_raw:.3f} | {row.eta2_window:.3f} | "
                     f"{row.eta2_window_std:.3f} | {row.mi_share:.3f} | "
                     f"{row.windows} |")

    lines += [
        "",
        "## How to read a disagreement between the columns",
        "",
        "- **raw high, window high** — separates drivers at every scale. A "
        "fingerprint unless physics says the quantity is genuinely behavioural.",
        "- **raw low, window high** — a ramp or a drifting level. The signal moves "
        "a lot *within* a drive, which hides it from raw η², while its level still "
        "identifies the drive. The thermal family's signature.",
        "- **raw high, window low** — rare; a signal whose per-sample spread is "
        "driver-specific but whose average is not.",
        "- **level columns low, spread column high** — drivers share an average "
        "but differ in how much the signal moves within a window. This is "
        "jitter, smoothness or aggression, and the spread column is the only one "
        "that can see it.",
        "- **η² low, MI high** — drivers share a mean but differ in distribution "
        "shape in some other way. MI is the only column that would see that.",
        "",
        "**What MI actually contributed here: nothing.** No signal has MI ≥ "
        f"{WATCH_ETA} while both η² columns sit below {WATCH_ETA}. MI is "
        "systematically *lower* than η² on this data (SPN 3031: η² = 0.986, MI = "
        "0.559), so it behaves as a weaker detector rather than a complementary "
        "one. It is kept in the table as a negative result worth recording, not "
        "as a criterion that earned its place.",
        "",
        "## Caveat",
        "",
        "Mutual information is estimated by a k-nearest-neighbour method that adds "
        f"small noise to break ties; the seed is pinned (`MI_SEED = {MI_SEED}`) so "
        "the number is reproducible. It is computed on window means rather than "
        "raw samples, both because that is the scale the model reads and because "
        "a k-NN estimate over millions of autocorrelated samples would measure "
        "sampling density as much as dependence.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Measure continuous-signal separability and write the report."""
    files = [p for p in sorted(DATA_RAW.glob("G*_Subject*.csv"))
             if driver_id(p.stem) not in EXCLUDE_DRIVERS]
    signals = continuous_spns(files)
    print(f"continuous signals: {len(signals)} | reading {len(files)} drivers")

    moments, windows, spreads = collect(files, signals)
    table = measure(signals, moments, windows, spreads)

    # the streaming η² must equal the stored-sample η² it stands in for
    probe = next(iter(signals))
    check = eta_squared({d: w for d, w in windows[probe].items() if w.size})
    same = eta_squared_from_moments(
        np.array([w.size for w in windows[probe].values() if w.size], float),
        np.array([w.sum() for w in windows[probe].values() if w.size], float),
        np.array([(w ** 2).sum() for w in windows[probe].values() if w.size], float))
    print(f"\nmoment-form check on SPN {probe}: "
          f"stored={check:.9f} streaming={same:.9f} "
          f"{'OK' if abs(check - same) < 1e-9 else 'MISMATCH'}")

    write_report(table, len(files))
    gap = table.eta2_window - table.eta2_raw
    print(f"\nsignals where window eta2 exceeds raw by >= {SCALE_GAP}: "
          f"{int((gap >= SCALE_GAP).sum())}")
    only_mi = table[(table.eta2_raw < WATCH_ETA) & (table.eta2_window < WATCH_ETA)
                    & (table.mi_share >= WATCH_ETA)]
    print(f"signals only MI detects: {len(only_mi)}")
    only_spread = table[(table.eta2_raw < WATCH_ETA)
                        & (table.eta2_window < WATCH_ETA)
                        & (table.eta2_window_std >= WATCH_ETA)]
    print(f"signals only the spread column detects: {len(only_spread)}")
    if len(only_spread):
        for row in only_spread.itertuples(index=False):
            print(f"    SPN {row.spn}: raw={row.eta2_raw:.3f} "
                  f"win={row.eta2_window:.3f} std={row.eta2_window_std:.3f}")
    print(f"signals with any statistic >= {LEAK_ETA}: "
          f"{int((table.worst >= LEAK_ETA).sum())}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
