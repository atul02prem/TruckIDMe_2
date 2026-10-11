"""Assign sector_id to every GPS row of every usable driver via spatial NN.

Pipeline (per driver):
  1. Load processed CSV: canloggerTime + all SparkFun GPS columns.
  2. Project (latitude, longitude) to local meters using the projection
     reference stored in sector_map.csv (ref_lat, ref_lon).
  3. Query a KDTree built over a densified version of the RDP polyline
     (intermediate points every 5 m along each segment, each carrying its
     parent segment's sector_id).
  4. Inherit sector_id from the nearest dense point; record sector_dist_m
     as the Euclidean distance to that point.
  5. Save per-driver to data/interim_data/{driver}.csv.

Also writes a verification scatter (one reference driver colored by sector_id)
to outputs/figures/sectors_G1_Subject1.png.

Run from project root:
    python -m src.data.assign_sectors
"""

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from src.data.build_sector_map import latlon_to_local_meters
from src.config import (
    DATA_EXTERNAL,
    DATA_INTERIM,
    DATA_PROCESSED,
    EXCLUDE_DRIVERS,
    OUT_FIGURES,
)


SECTOR_MAP_FILE  = DATA_EXTERNAL / "sector_map.csv"
DENSE_SPACING_M  = 5.0

SPARKFUN_COLS = [
    "canloggerTime",
    "gpsTime",
    "timestampsLocation",
    "longitude",
    "latitude",
    "timestampHeading",
    "gpsSpeed",
    "headingDegree",
    "timestampSat",
    "numSats",
]

_DRIVER_ID_RE = re.compile(r"^G(\d+)_Subject(\d+)$")


def filename_to_driver_id(stem: str) -> str:
    """Convert a CSV stem like 'G1_Subject4' to canonical 'G1S04'."""
    m = _DRIVER_ID_RE.match(stem)
    if not m:
        raise ValueError(f"Cannot parse driver ID from {stem!r}")
    return f"G{m.group(1)}S{int(m.group(2)):02d}"


def load_sector_map(path: Path) -> tuple[pd.DataFrame, float, float]:
    """Load the principal sector map CSV and extract its projection reference.

    Args:
        path: path to sector_map.csv (must contain ref_lat, ref_lon columns).

    Returns:
        (waypoints_df, ref_lat, ref_lon). ref_lat/ref_lon are scalars taken
        from the first row (they are constant across rows).
    """
    df = pd.read_csv(path)
    ref_lat = float(df["ref_lat"].iloc[0])
    ref_lon = float(df["ref_lon"].iloc[0])
    return df, ref_lat, ref_lon


def densify_polyline(
    waypoints: pd.DataFrame,
    spacing_m: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate dense (x_m, y_m, sector_id) points along the RDP polyline.

    For each segment i from waypoint i to waypoint i+1, generates evenly
    spaced points at intervals of ~spacing_m. Each dense point carries
    sector_id = i. Endpoints are included.

    Args:
        waypoints: sector_map DataFrame with x_m, y_m columns in segment order.
        spacing_m: target spacing in meters.

    Returns:
        (xs, ys, sector_ids) — three 1-D arrays of equal length.
    """
    x_w = waypoints["x_m"].values
    y_w = waypoints["y_m"].values
    n = len(waypoints)
    xs, ys, sids = [], [], []
    for i in range(n - 1):
        x0, y0 = x_w[i], y_w[i]
        x1, y1 = x_w[i + 1], y_w[i + 1]
        seg_len = float(np.hypot(x1 - x0, y1 - y0))
        n_steps = max(int(np.ceil(seg_len / spacing_m)), 1)
        ts = np.linspace(0.0, 1.0, n_steps + 1)
        xs.append(x0 + ts * (x1 - x0))
        ys.append(y0 + ts * (y1 - y0))
        sids.append(np.full(len(ts), i, dtype=int))
    return (
        np.concatenate(xs),
        np.concatenate(ys),
        np.concatenate(sids),
    )


def assign_sectors_for_driver(
    csv_path: Path,
    kdtree: KDTree,
    dense_sids: np.ndarray,
    ref_lat: float,
    ref_lon: float,
) -> pd.DataFrame:
    """Assign sector_id and sector_dist_m to every GPS row of one driver.

    Args:
        csv_path:   processed driver CSV path.
        kdtree:     KDTree built over (x_m, y_m) of dense reference points.
        dense_sids: sector_id array aligned to KDTree result indices.
        ref_lat:    projection reference latitude (degrees).
        ref_lon:    projection reference longitude (degrees).

    Returns:
        DataFrame with the full SparkFun GPS column set plus sector_id and
        sector_dist_m, sorted by canloggerTime, rows with missing lat/lon
        or canloggerTime dropped.
    """
    df = pd.read_csv(csv_path, usecols=SPARKFUN_COLS)
    df = df.dropna(subset=["canloggerTime", "latitude", "longitude"])
    df = df.sort_values("canloggerTime").reset_index(drop=True)

    x_m, y_m = latlon_to_local_meters(
        df["latitude"].values, df["longitude"].values, ref_lat, ref_lon,
    )
    query = np.column_stack([x_m, y_m])
    dists, idxs = kdtree.query(query, k=1)

    df["sector_id"]     = dense_sids[idxs]
    df["sector_dist_m"] = dists
    return df


def plot_driver_sectors(driver_df: pd.DataFrame, out_path: Path, driver_label: str) -> None:
    """Plot one driver's GPS scatter colored by sector_id."""
    fig, ax = plt.subplots(figsize=(12, 12))
    sc = ax.scatter(
        driver_df["longitude"], driver_df["latitude"],
        c=driver_df["sector_id"], cmap="tab20",
        s=4, alpha=0.7,
    )
    cbar = plt.colorbar(sc, ax=ax, shrink=0.6)
    cbar.set_label("sector_id")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title(
        f"{driver_label} — GPS rows colored by assigned sector_id "
        f"({driver_df['sector_id'].nunique()} sectors visited)"
    )
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    waypoints, ref_lat, ref_lon = load_sector_map(SECTOR_MAP_FILE)
    print(f"Sector map:  {len(waypoints)} waypoints  "
          f"(ref_lat={ref_lat:.6f}, ref_lon={ref_lon:.6f})")

    dense_x, dense_y, dense_sids = densify_polyline(waypoints, spacing_m=DENSE_SPACING_M)
    print(f"Densified to {len(dense_x):,} reference points at {DENSE_SPACING_M} m spacing")

    kdtree = KDTree(np.column_stack([dense_x, dense_y]))
    print(f"KDTree built ({len(dense_x):,} points)")
    print()

    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    g1s01_df: pd.DataFrame | None = None
    for csv_file in sorted(DATA_PROCESSED.glob("G*_Subject*.csv")):
        driver_id = filename_to_driver_id(csv_file.stem)
        if driver_id in EXCLUDE_DRIVERS:
            print(f"  skipping {driver_id} (excluded)")
            continue
        out_df = assign_sectors_for_driver(csv_file, kdtree, dense_sids, ref_lat, ref_lon)
        out_path = DATA_INTERIM / csv_file.name
        out_df.to_csv(out_path, index=False)
        print(
            f"  {driver_id}: {len(out_df):,} rows  "
            f"dist median={out_df['sector_dist_m'].median():5.2f} m  "
            f"max={out_df['sector_dist_m'].max():7.1f} m  "
            f"sectors visited={out_df['sector_id'].nunique()}/{len(waypoints) - 1}"
        )
        if driver_id == "G1S01":
            g1s01_df = out_df

    if g1s01_df is not None:
        fig_path = OUT_FIGURES / "sectors_G1_Subject1.png"
        plot_driver_sectors(g1s01_df, fig_path, "G1S01")
        print(f"\nVerification plot written to {fig_path}")
