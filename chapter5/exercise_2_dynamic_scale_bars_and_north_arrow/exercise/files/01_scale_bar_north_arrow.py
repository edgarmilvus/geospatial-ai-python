import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import numpy as np
import pathlib
from shapely.geometry import Polygon

# --- Two substitutions, and why ---
#
# 1. Data. `gpd.datasets.get_path('naturalearth_lowres')` was removed in GeoPandas 1.0, and this
#    volume may not download a replacement, so the six regions of the Great Lakes and Saint
#    Lawrence are generated below: fixed shape, seeded density, WGS 84.
# 2. The axes is a Cartopy GeoAxes in UTM zone 17N, so the map's units are metres and the scale
#    bar is a real distance. No Cartopy dataset is used: `ax.coastlines()` and
#    `cfeature.LAND` would download Natural Earth shapefiles, so the land is the frame we built.
#
# GeoPandas 1.0 does not reproject for a Cartopy axes, so the regions are handed over with
# `ax.add_geometries(..., crs=ccrs.PlateCarree())` and Cartopy does the transformation.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

WGS84 = ccrs.PlateCarree()

# Great Lakes and Saint Lawrence, 42-48 N: close enough to UTM 17N's central meridian
# (-81 W) that a 150 km bar is a fair approximation rather than a fiction.
CENTRES = [(-82.5, 46.6), (-80.5, 45.2), (-78.7, 44.0),
           (-76.8, 45.2), (-75.0, 43.6), (-73.2, 44.8)]
NAMES = ["Algoma", "Georgian", "Frontenac", "Ottawa", "Estrie", "Beauce"]


def synthetic_regions():
    """Six irregular polygons in WGS 84, fixed shape, no randomness in the geometry."""
    polygons, names = [], []
    angles = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    for index, ((lon0, lat0), name) in enumerate(zip(CENTRES, NAMES)):
        radii = 1.1 * (1.0 + 0.18 * np.sin(3.0 * angles + index))
        ring = [(lon0 + r * np.cos(a) / np.cos(np.radians(lat0)), lat0 + r * np.sin(a))
                for a, r in zip(angles, radii)]
        polygons.append(Polygon(ring))
        names.append(name)
    return gpd.GeoDataFrame({"name": names}, geometry=polygons, crs="EPSG:4326")


# --- Helper functions ---

def draw_north_arrow(ax, location=(0.9, 0.9), size=0.08, color="black"):
    """Draws a stylized North Arrow in axes coordinates."""
    # Location is in axes coordinates (0 to 1)
    x, y = location

    # Use ax.text for the 'N' label
    ax.text(x, y + size * 0.1, "N",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=size * 100, color=color, fontweight="bold")

    # The arrow body, from (x, y - 0.45 size) up to (x, y - 0.05 size). Both ends have to
    # say "axes fraction": `transform=ax.transAxes` moves only the text, and the first draft
    # aimed the arrow at x = 0.9 *metres*, which is off the map and therefore invisible.
    ax.annotate("", xy=(x, y - size * 0.05), xytext=(x, y - size * 0.45),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(facecolor=color, edgecolor=color, width=2.0,
                                headwidth=9.0, headlength=9.0, shrink=0))


def draw_scale_bar(ax, target_km, location=(0.1, 0.05)):
    """Calculates and draws a scale bar for a map in a metric CRS."""

    # 1. Get current map extent in coordinate units (metres of the GeoAxes' projection)
    x_min, x_max = ax.get_xlim()

    # 2. Determine coordinate length for target distance
    target_m = target_km * 1000

    # The bar starts at 10% of the map width from the left edge.
    map_width = x_max - x_min
    start_x = x_min + location[0] * map_width

    # Calculate the end x-coordinate based on the target distance
    end_x = start_x + target_m

    # Vertical position, also as a fraction of the map height.
    y_min, y_max = ax.get_ylim()
    map_height = y_max - y_min
    y_pos = y_min + location[1] * map_height

    # 3. Draw alternating black and white segments
    segment_length = target_m / 4  # Four segments
    bar_height = map_height * 0.015

    for i in range(4):
        color = "black" if i % 2 == 0 else "white"
        rect = mpatches.Rectangle(
            (start_x + i * segment_length, y_pos),
            segment_length, bar_height,
            facecolor=color, edgecolor="black", linewidth=0.5, zorder=6
        )
        ax.add_patch(rect)

    # 4. Add label
    ax.text(end_x, y_pos - bar_height * 0.5, f"{target_km} km",
            fontsize=9, ha="right", va="top", fontweight="bold", zorder=6)

    # The number the map claims, in the units a reader can check.
    return start_x, end_x


# --- Main plotting script ---

# 1. Data and projection setup
gdf = synthetic_regions()

# Mock population density data (50 to 500)
rng = np.random.default_rng(42)
gdf["DENSITY"] = rng.integers(50, 500, len(gdf))

# The axes owns the projection: UTM 17N, whose units are metres, so a 150 km bar is a real
# distance on the ground rather than 150 km only near the central meridian.
CRS_UTM = ccrs.UTM(zone=17)
fig, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw={"projection": CRS_UTM})

# 2. Custom color ramp, applied per region because the colours are handed to Cartopy, not to a
#    GeoDataFrame column.
colors = ["#fef0d9", "#fdcc8a", "#fc8d59", "#e34a33", "#b30000"]
cmap_name = "CustomDensity"
cm = mcolors.LinearSegmentedColormap.from_list(cmap_name, colors, N=256)
norm = mcolors.Normalize(vmin=gdf["DENSITY"].min(), vmax=gdf["DENSITY"].max())

ax.add_geometries(list(gdf.geometry), crs=WGS84,
                  facecolor=[cm(norm(value)) for value in gdf["DENSITY"]],
                  edgecolor="0.8", linewidth=0.8)

# The view comes first, in the projection's metres: both annotations below are placed from the
# axes' current limits, and a bar drawn before `set_extent` lands outside the map. The extent is
# the regions' own bounds in UTM 17N plus a margin - and `set_extent` clips it to the zone's own
# boundary, which is why the regions were placed inside the zone rather than across it.
x0, y0, x1, y1 = gdf.to_crs(CRS_UTM.proj4_init).total_bounds
margin = 0.02 * max(x1 - x0, y1 - y0)
ax.set_extent([x0 - margin, x1 + margin, y0 - margin, y1 + margin], crs=CRS_UTM)

# The graticule is Cartopy's, and the labels are what make it a graticule rather than lines.
gl = ax.gridlines(crs=WGS84, draw_labels=True, linewidth=0.4, color="gray",
                  alpha=0.5, linestyle="--")
gl.top_labels = False
gl.right_labels = False

ax.set_title(f"Regional Map in Projected CRS (UTM zone {CRS_UTM.utm_zone})", fontsize=14)

# 3. and 4. Integration of the custom elements
draw_north_arrow(ax, location=(0.9, 0.9))
bar_start, bar_end = draw_scale_bar(ax, target_km=150, location=(0.1, 0.08))

# The figure is written where every artefact of this project goes.
figure_path = OUTPUT / "scale_bar_north_arrow.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")

# --- Report ---
lon, lat = CENTRES[0]
proj_x, proj_y = CRS_UTM.transform_point(lon, lat, WGS84)
print("--- Data ---")
print(f"Regions: {len(gdf)}")
print(f"CRS: {gdf.crs.to_string()} -> axes {ax.projection.__class__.__name__} (UTM 17N)")
print(f"Bounds (minx, miny, maxx, maxy): "
      f"{tuple(round(float(v), 0) for v in gdf.to_crs(CRS_UTM.proj4_init).total_bounds)} m")
print(f"Density range: {gdf['DENSITY'].min()}-{gdf['DENSITY'].max()}")
print(f"Algoma at ({lon}, {lat}) -> ({proj_x:,.1f}, {proj_y:,.1f}) m")

print("\n--- GeoAxes ---")
print(f"Type: {type(ax).__name__}")
print(f"Extent (metres): {tuple(round(float(v), 0) for v in ax.get_extent(crs=CRS_UTM))}")
print(f"Extent (degrees): "
      f"{tuple(round(float(v), 2) for v in ax.get_extent(crs=WGS84))}")
print(f"Gridline labels: {len(gl.bottom_label_artists)} bottom, "
      f"{len(gl.left_label_artists)} left")

print("\n--- Scale bar ---")
print(f"Claimed length: 150 km = {150_000:,} m of the projection")
print(f"Drawn from x={bar_start:,.0f} to x={bar_end:,.0f} m")
print(f"Bar length in data units: {bar_end - bar_start:,.0f} m")
print(f"Four segments of {(bar_end - bar_start) / 4:,.0f} m each")

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")

plt.close(fig)
