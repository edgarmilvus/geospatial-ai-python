import matplotlib
matplotlib.use("Agg")  # the listing writes two PNGs; there is no interactive window to open

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import numpy as np
import pathlib
from shapely.geometry import Polygon

# --- Two substitutions, and one repair ---
#
# 1. Data. `gpd.datasets.get_path('naturalearth_lowres')` was removed in GeoPandas 1.0, so the
#    Florida window is filled with six synthetic polygons in WGS 84, generated below and fixed:
#    they are what the two extents are chosen to frame.
# 2. The axes is a GeoAxes in UTM zone 17N, so its data coordinates are metres and the scale
#    bar's length is a real distance. No Cartopy dataset is used - `cfeature.LAND` and
#    `ax.coastlines()` would download Natural Earth shapefiles - so the land is our own frame.
# 3. `find_optimal_nice_number` is repaired. The book's version starts at
#    `int(floor(log10(width) - 1))` and walks *up*, so for a 150 km wide map it finds no
#    candidate in the 30-45 km window, overshoots the safety break, and returns 500 km - a bar
#    three times wider than the map. The search now walks the decades that can hold a fifth to
#    a third of the width, and falls back to the largest nice number that fits.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

WGS84 = ccrs.PlateCarree()

CENTRES = [(-81.5, 28.5), (-80.5, 27.5), (-82.0, 26.5), (-80.0, 26.0),
           (-82.5, 29.0), (-79.0, 28.0)]
NAMES = ["Marion", "Orange", "Polk", "Highlands", "Alachua", "Brevard"]


def synthetic_region():
    """Six irregular polygons in WGS 84, fixed shape, no randomness."""
    polygons, names = [], []
    angles = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    for index, ((lon0, lat0), name) in enumerate(zip(CENTRES, NAMES)):
        radii = 0.45 * (1.0 + 0.20 * np.sin(3.0 * angles + index))
        ring = [(lon0 + r * np.cos(a) / np.cos(np.radians(lat0)), lat0 + r * np.sin(a))
                for a, r in zip(angles, radii)]
        polygons.append(Polygon(ring))
        names.append(name)
    return gpd.GeoDataFrame({"name": names}, geometry=polygons, crs="EPSG:4326")


# --- Helper functions ---

def find_optimal_nice_number(target_length):
    """Finds the largest 'nice' number (1, 2, 2.5, 5 x 10^n) between 20% and 30% of the
    map width, and the largest one that still fits when that window is empty."""

    # Target range: a fifth to a third of the full map width.
    min_length = target_length * 0.20
    max_length = target_length * 0.30

    # Nice numbers: everything a cartographer is willing to print on a bar.
    nice_bases = np.array([1.0, 2.0, 2.5, 5.0])
    decades = 10.0 ** np.arange(0, int(np.ceil(np.log10(target_length))) + 2)

    candidates = np.concatenate([nice_bases * decade for decade in decades])

    # First choice: the largest nice number inside the window.
    inside = candidates[(candidates >= min_length) & (candidates <= max_length)]
    if len(inside) > 0:
        chosen = float(np.max(inside))
    else:
        # When no nice number lands in the window (a common case), take the largest that at
        # least fits inside the map instead of silently overshooting it.
        chosen = float(np.max(candidates[candidates <= max_length]))

    # Returned in kilometres, the unit the bar is labelled in.
    return chosen / 1000.0


def draw_dynamic_scale_bar(ax, location=(0.1, 0.05)):
    """Calculates optimal scale and draws the bar. The GeoAxes' data units are metres."""

    x_min, x_max = ax.get_xlim()
    map_width_m = x_max - x_min

    # Calculate optimal scale length in km
    L_opt_km = find_optimal_nice_number(map_width_m)
    L_opt_m = L_opt_km * 1000  # back to metres (coordinate units)

    # Bar placement
    y_min, y_max = ax.get_ylim()
    map_height = y_max - y_min

    start_x = x_min + location[0] * map_width_m
    y_pos = y_min + location[1] * map_height
    bar_height = map_height * 0.015

    # Alternating segments (4 segments)
    segment_length = L_opt_m / 4

    for i in range(4):
        color = "black" if i % 2 == 0 else "white"
        rect = mpatches.Rectangle(
            (start_x + i * segment_length, y_pos),
            segment_length, bar_height,
            facecolor=color, edgecolor="black", linewidth=0.5, zorder=6
        )
        ax.add_patch(rect)

    # Add label
    ax.text(start_x + L_opt_m, y_pos - bar_height * 0.5, f"{int(L_opt_km)} km",
            fontsize=10, ha="right", va="top", fontweight="bold", zorder=6)

    return L_opt_km


def set_optimal_grid(ax, grid_interval_m=50_000):
    """Sets ticks on round projected coordinates. A GeoAxes shows the ticks it is given, in the
    projection's metres, which is why they are multiples of the interval and not data bounds."""

    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    # Round intervals, not the data's own bounds
    x_start = np.ceil(x_min / grid_interval_m) * grid_interval_m
    x_end = np.floor(x_max / grid_interval_m) * grid_interval_m
    y_start = np.ceil(y_min / grid_interval_m) * grid_interval_m
    y_end = np.floor(y_max / grid_interval_m) * grid_interval_m

    x_ticks = np.arange(x_start, x_end + 1, grid_interval_m)
    y_ticks = np.arange(y_start, y_end + 1, grid_interval_m)

    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)

    # Metric coordinates, printed in full: offsets would hide the easting.
    ax.ticklabel_format(style="plain", axis="both", useOffset=False)

    ax.grid(True, linestyle=":", alpha=0.6, color="gray")


# --- Main plotting and testing ---

# 1. Setup. UTM zone 17N covers Florida and Georgia, so the data coordinates are metres.
CRS_MAP = ccrs.UTM(zone=17)
gdf = synthetic_region()

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=CRS_MAP)

# Plot the data: handed over in WGS 84, projected by the GeoAxes.
ax.add_geometries(list(gdf.geometry), crs=WGS84, facecolor="lightgreen", edgecolor="black")

# 2. Initial extent: a local view, about 150 km wide, in the projection's metres
ax.set_extent([400_000, 550_000, 2_900_000, 3_050_000], crs=CRS_MAP)

# 3. and 4. Dynamic scale bar
L_km = draw_dynamic_scale_bar(ax)
ax.set_title(f"Dynamic Scale and Grid Map (Scale Bar: {int(L_km)} km)", fontsize=14)

# 5. Interactive grid: 50 km interval = 50 000 metres
set_optimal_grid(ax, grid_interval_m=50_000)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

figure_local = OUTPUT / "dynamic_scale_local.png"
fig.savefig(figure_local, dpi=150, bbox_inches="tight")

# --- Test 2: a much wider extent (simulating a zoom out) ---
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=CRS_MAP)
ax.add_geometries(list(gdf.geometry), crs=WGS84, facecolor="lightgreen", edgecolor="black")

# About 800 km wide
ax.set_extent([300_000, 1_100_000, 2_800_000, 3_600_000], crs=CRS_MAP)

L_km_2 = draw_dynamic_scale_bar(ax)
ax.set_title(f"Dynamic Scale and Grid Map (Scale Bar: {int(L_km_2)} km)", fontsize=14)

# A 100 km grid for the wider view
set_optimal_grid(ax, grid_interval_m=100_000)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

figure_wide = OUTPUT / "dynamic_scale_wide.png"
fig.savefig(figure_wide, dpi=150, bbox_inches="tight")

# --- Report ---
print("--- Data ---")
print(f"Regions: {len(gdf)} in {gdf.crs.to_string()}, drawn on a {type(ax.projection).__name__} "
      f"(UTM zone {CRS_MAP.utm_zone})")
print(f"Bounds (minx, miny, maxx, maxy): "
      f"{tuple(round(float(v), 0) for v in gdf.to_crs(CRS_MAP.proj4_init).total_bounds)} m")

print("\n--- GeoAxes ---")
print(f"Wide view extent (metres): {tuple(round(float(v), 0) for v in ax.get_extent(crs=CRS_MAP))}")
print(f"Wide view extent (degrees): "
      f"{tuple(round(float(v), 2) for v in ax.get_extent(crs=WGS84))}")
print(f"Grid ticks: {len(ax.get_xticks())} on x, {len(ax.get_yticks())} on y")

print("\n--- Scale decisions ---")
print(f"Local view: 150,000 m wide -> bar of {L_km:.0f} km "
      f"({L_km * 1000 / 150_000 * 100:.1f}% of the width)")
print(f"Wide view:  800,000 m wide -> bar of {L_km_2:.0f} km "
      f"({L_km_2 * 1000 / 800_000 * 100:.1f}% of the width)")
print(f"Nice-number probe at 150,000 m: {find_optimal_nice_number(150_000):,.0f} km")
print(f"Nice-number probe at 800,000 m: {find_optimal_nice_number(800_000):,.0f} km")
print(f"Nice-number probe at  40,000 m: {find_optimal_nice_number(40_000):,.0f} km")

print("\n--- Figures ---")
for path in (figure_local, figure_wide):
    print(f"Saved: {path.relative_to(OUTPUT.parent)} ({path.stat().st_size} bytes)")

plt.close("all")
