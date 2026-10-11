"""Build a sector map from the reference driver's GPS trace via Ramer-Douglas-Peucker.

Pipeline:
  1. Load G1S01's GPS trace (canloggerTime, latitude, longitude).
  2. Project lat/lon to local meters (equirectangular around the trace centroid).
     Sub-meter accurate over the ~7 km Fort Collins route — far below our 20 m
     RDP tolerance, so no UTM dependency needed.
  3. Apply RDP simplification to keep only the vertices we need.
  4. Project the kept vertices back to lat/lon.

Outputs:
  - data/external_data/sector_map.csv     (sector_id, lat, lon, x_m, y_m)
  - outputs/figures/sector_map.png         (overlay on reference trace)

Each sector_i is the line segment from waypoint i to waypoint i+1; the last
waypoint marks the end of the final sector.

Run from project root:
    python -m src.data.build_sector_map
"""

import math
from pathlib import Path

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import DATA_EXTERNAL, DATA_PROCESSED, OUT_FIGURES


REFERENCE_DRIVER_FILE = "G1_Subject1.csv"
RDP_EPSILON_M         = 20.0
EARTH_R_M             = 6_371_000.0


def load_reference_gps(csv_path: Path) -> pd.DataFrame:
    """Load (canloggerTime, latitude, longitude) for the reference driver.

    Args:
        csv_path: path to a processed driver CSV.

    Returns:
        DataFrame with NaN rows dropped, sorted ascending by canloggerTime.
    """
    df = pd.read_csv(csv_path, usecols=["canloggerTime", "latitude", "longitude"])
    df = df.dropna(subset=["latitude", "longitude", "canloggerTime"])
    return df.sort_values("canloggerTime").reset_index(drop=True)


def latlon_to_local_meters(
    latitude: np.ndarray,
    longitude: np.ndarray,
    lat_ref: float,
    lon_ref: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Equirectangular projection of lat/lon to local meters around a reference point.

    Args:
        latitude:  array of latitudes (degrees).
        longitude: array of longitudes (degrees).
        lat_ref:   reference latitude (degrees), the projection center.
        lon_ref:   reference longitude (degrees), the projection center.

    Returns:
        (x_m, y_m) — east-positive, north-positive — in meters.
    """
    lat_ref_rad = math.radians(lat_ref)
    x = np.radians(longitude - lon_ref) * math.cos(lat_ref_rad) * EARTH_R_M
    y = np.radians(latitude  - lat_ref) * EARTH_R_M
    return x, y


def local_meters_to_latlon(
    x_m: np.ndarray,
    y_m: np.ndarray,
    lat_ref: float,
    lon_ref: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Inverse of latlon_to_local_meters."""
    lat_ref_rad = math.radians(lat_ref)
    lat = lat_ref + np.degrees(y_m / EARTH_R_M)
    lon = lon_ref + np.degrees(x_m / (math.cos(lat_ref_rad) * EARTH_R_M))
    return lat, lon


def rdp_simplify(x: np.ndarray, y: np.ndarray, epsilon: float) -> np.ndarray:
    """Ramer-Douglas-Peucker polyline simplification — returns the keep mask.

    Iterative (stack-based) implementation to handle traces of 25k+ points
    without hitting Python's recursion limit.

    Args:
        x, y:    coordinate arrays of equal length (any consistent unit).
        epsilon: max perpendicular distance from a chord that allows interior
                 vertices to be dropped (same unit as x, y).

    Returns:
        Boolean mask the same length as x: True for vertices to keep.
        First and last vertices are always kept.
    """
    n = len(x)
    if n == 0:
        return np.zeros(0, dtype=bool)
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True

    stack: list[tuple[int, int]] = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        cx, cy = x[i], y[i]
        dx, dy = x[j] - cx, y[j] - cy
        chord_len = math.hypot(dx, dy)
        if chord_len == 0.0:
            # Degenerate chord: rank by raw distance from endpoint.
            d = np.hypot(x[i + 1 : j] - cx, y[i + 1 : j] - cy)
        else:
            # |cross product| / |chord| = perpendicular distance.
            d = np.abs(dx * (y[i + 1 : j] - cy) - dy * (x[i + 1 : j] - cx)) / chord_len
        if len(d) == 0:
            continue
        max_off = int(np.argmax(d))
        if d[max_off] > epsilon:
            split = i + 1 + max_off
            keep[split] = True
            stack.append((i, split))
            stack.append((split, j))
    return keep


def build_sector_map(reference_csv: Path, epsilon_m: float) -> pd.DataFrame:
    """Run the full sector-map build pipeline on a reference driver's CSV.

    Args:
        reference_csv: path to the reference driver's processed CSV.
        epsilon_m:     RDP simplification tolerance in meters.

    Returns:
        DataFrame with one row per kept waypoint:
            [sector_id, lat, lon, x_m, y_m]
    """
    df = load_reference_gps(reference_csv)
    lat_ref = float(df["latitude"].mean())
    lon_ref = float(df["longitude"].mean())

    x_m, y_m = latlon_to_local_meters(
        df["latitude"].values, df["longitude"].values, lat_ref, lon_ref,
    )
    keep = rdp_simplify(x_m, y_m, epsilon=epsilon_m)

    x_kept = x_m[keep]
    y_kept = y_m[keep]
    lat_kept, lon_kept = local_meters_to_latlon(x_kept, y_kept, lat_ref, lon_ref)

    return pd.DataFrame({
        "sector_id": np.arange(len(x_kept)),
        "lat":       lat_kept,
        "lon":       lon_kept,
        "x_m":       x_kept,
        "y_m":       y_kept,
        # Projection reference (same value every row) — lets downstream scripts
        # project new lat/lon into the same meter-coordinate frame without
        # having to re-derive the reference.
        "ref_lat":   lat_ref,
        "ref_lon":   lon_ref,
    })


def plot_sector_map(
    reference_csv: Path,
    sector_map: pd.DataFrame,
    out_path: Path,
    epsilon_m: float,
) -> None:
    """Overlay the RDP waypoints + polyline on the reference GPS scatter."""
    df = load_reference_gps(reference_csv)

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.scatter(df["longitude"], df["latitude"],
               s=2, c="lightgray", alpha=0.5,
               label=f"G1S01 GPS trace ({len(df):,} pts)")
    ax.plot(sector_map["lon"], sector_map["lat"],
            "b-", linewidth=1.5, alpha=0.7, label="RDP polyline")
    ax.scatter(sector_map["lon"], sector_map["lat"],
               s=70, c="red", edgecolors="black", linewidths=1.2,
               zorder=10, label=f"Waypoints (N={len(sector_map)})")
    for _, row in sector_map.iterrows():
        ax.annotate(int(row["sector_id"]),
                    (row["lon"], row["lat"]),
                    textcoords="offset points", xytext=(7, 7), fontsize=8)

    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title(
        f"Sector map — RDP ε = {epsilon_m:.0f} m → {len(sector_map)} waypoints"
    )
    ax.set_aspect("equal")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def render_sector_map_html(
    reference_csv: Path,
    sector_map: pd.DataFrame,
    out_path: Path,
    trace_subsample: int = 20,
) -> None:
    """Render the sector map as an interactive HTML map on OpenStreetMap tiles.

    Args:
        reference_csv:   path to the reference driver's processed CSV.
        sector_map:      waypoints DataFrame from build_sector_map().
        out_path:        destination .html file.
        trace_subsample: keep every Nth row of the 10 Hz reference trace
                         (default 20 → 0.5 Hz) to keep the HTML file small.
                         The reference trace is just visual context, not data.
    """
    df = load_reference_gps(reference_csv)
    trace = df.iloc[::trace_subsample]

    center_lat = float(df["latitude"].mean())
    center_lon = float(df["longitude"].mean())

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="OpenStreetMap",
    )

    folium.PolyLine(
        locations=list(zip(trace["latitude"], trace["longitude"])),
        color="gray", weight=2, opacity=0.5,
        tooltip="G1S01 GPS trace",
    ).add_to(m)

    folium.PolyLine(
        locations=list(zip(sector_map["lat"], sector_map["lon"])),
        color="blue", weight=3, opacity=0.7,
        tooltip="RDP simplified polyline",
    ).add_to(m)

    for _, row in sector_map.iterrows():
        sector_id = int(row["sector_id"])
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.DivIcon(
                icon_size=(28, 28),
                icon_anchor=(14, 14),
                html=(
                    '<div style="font-size:10pt; color:white; background:#c00; '
                    'border:2px solid black; border-radius:50%; '
                    'width:24px; height:24px; text-align:center; line-height:20px; '
                    f'font-weight:bold;">{sector_id}</div>'
                ),
            ),
            tooltip=f"sector {sector_id} ({row['lat']:.5f}, {row['lon']:.5f})",
        ).add_to(m)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_path))


if __name__ == "__main__":
    csv_path = DATA_PROCESSED / REFERENCE_DRIVER_FILE
    sector_map = build_sector_map(csv_path, epsilon_m=RDP_EPSILON_M)

    print(f"Reference driver:        {REFERENCE_DRIVER_FILE}")
    print(f"RDP epsilon:             {RDP_EPSILON_M} m")
    print(f"Number of waypoints:     {len(sector_map)}")
    print(f"(implies {len(sector_map) - 1} sector segments)")
    print()
    print(sector_map.to_string(index=False))

    out_csv = DATA_EXTERNAL / "sector_map.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    sector_map.to_csv(out_csv, index=False)
    print(f"\nSector map written to {out_csv}")

    out_png = OUT_FIGURES / "sector_map.png"
    plot_sector_map(csv_path, sector_map, out_png, RDP_EPSILON_M)
    print(f"Static plot written to {out_png}")

    out_html = OUT_FIGURES / "sector_map.html"
    render_sector_map_html(csv_path, sector_map, out_html)
    print(f"Interactive map written to {out_html}")
    print("  Open it in a browser to inspect waypoints on real streets.")
