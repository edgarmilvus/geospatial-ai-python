import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import numpy as np
import pathlib
from shapely.geometry import Point, Polygon

# --- Two substitutions, and why ---
#
# 1. Data. The chapter reads `gpd.datasets.get_path('naturalearth_lowres')`, which GeoPandas 1.0
#    removed, and buffers Indonesia to stand in for a water layer. Neither is available offline,
#    so the region is seven synthetic land polygons over South-East Asia plus a synthetic strait,
#    generated below with a fixed shape and no randomness.
# 2. The axes is a GeoAxes in UTM zone 48N. No Cartopy dataset is touched - `cfeature.LAND`
#    would download a Natural Earth shapefile - so the land is the frame we build.
#
# GeoPandas 1.0 does not reproject for a Cartopy axes, so both layers are handed over with
# `ax.add_geometries(..., crs=ccrs.PlateCarree())`: the transformation is what that argument
# asks the GeoAxes to perform, and the point of interest is projected with `transform_point`.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

WGS84 = ccrs.PlateCarree()

CENTRES = [(100.0, 5.0), (104.0, 2.0), (108.0, 0.0), (112.0, -1.0),
           (116.0, -2.0), (120.0, -4.0), (106.0, 12.0)]
NAMES = ["Malaya", "Sumatra", "Borneo", "Java", "Sulawesi", "Flores", "Indochina"]


def synthetic_region():
    """Seven land polygons and one strait, all in WGS 84, fixed shape."""
    land, names = [], []
    angles = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    for index, ((lon0, lat0), name) in enumerate(zip(CENTRES, NAMES)):
        radii = 0.9 * (1.0 + 0.20 * np.sin(3.0 * angles + index))
        ring = [(lon0 + r * np.cos(a) / np.cos(np.radians(lat0)), lat0 + r * np.sin(a))
                for a, r in zip(angles, radii)]
        land.append(Polygon(ring))
        names.append(name)
    # The water layer: the strait between Malaya and Sumatra, standing in for the book's
    # buffered-country placeholder.
    water = Polygon([(99.5, 0.55), (104.0, 0.55), (104.0, 1.35), (99.5, 1.35)])
    return (gpd.GeoDataFrame({"name": names}, geometry=land, crs="EPSG:4326"),
            gpd.GeoDataFrame({"name": ["Java Sea"]}, geometry=[water], crs="EPSG:4326"))


# --- Setup and data simulation ---

# A regional area (South-East Asia) and a metric projection (UTM zone 48N)
CRS_MAP = ccrs.UTM(zone=48)

land_wgs84, water_wgs84 = synthetic_region()

# Define a point of interest, e.g. a port (near Singapore)
poi_wgs84 = Point(103.85, 1.35)

# 1. Refactoring setup: one GeoAxes, whose projection is the map's CRS
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=CRS_MAP)

# Plotting layers
ax.add_geometries(list(land_wgs84.geometry), crs=WGS84,
                  facecolor="#f0e4c4", edgecolor="black", linewidth=0.5)
ax.add_geometries(list(water_wgs84.geometry), crs=WGS84,
                  facecolor="#a0c4ff", edgecolor="none")

# The point of interest is a WGS 84 coordinate; the axes speaks UTM metres, so it has to be
# projected before anything is drawn at it. `transform_point` is Cartopy's forward transform.
poi_x, poi_y = CRS_MAP.transform_point(poi_wgs84.x, poi_wgs84.y, WGS84)

# 2. Refactoring titles and labels: ax.set_title instead of plt.title, plus a figure title
ax.set_title("Regional Infrastructure and Geographic Features", fontsize=14, pad=10)
fig.suptitle(f"Advanced Map Refactoring: South-East Asia in UTM zone {CRS_MAP.utm_zone}",
             fontsize=16, fontweight="bold")

# Axis labels and round ticks, required for the object-model demonstration. A GeoAxes shows
# ticks only where they are placed, and they are placed in the projection's metres.
ax.set_xticks(np.arange(0, 800_001, 200_000))
ax.set_yticks(np.arange(-100_000, 400_001, 100_000))
ax.ticklabel_format(style="plain", axis="both", useOffset=False)
ax.set_xlabel("Easting (Meters)")
ax.set_ylabel("Northing (Meters)")

# 3. Refactoring the legend: explicit handles, because two layers were plotted by hand
land_handle = mpatches.Patch(color="#f0e4c4", label="Land Areas")
water_handle = mpatches.Patch(color="#a0c4ff", label="Water/Buffer")

ax.legend(handles=[land_handle, water_handle],
          loc="upper left",
          title="Map Layers",
          frameon=True)

# 4. Advanced annotation layer

# 4a. POI marker, at the projected coordinate - data coordinates on a GeoAxes are metres.
ax.scatter(poi_x, poi_y,
           color="red",
           marker="*",
           s=90,
           zorder=5,
           label="Point of Interest (POI)")

# 4b. A contextual bounding box, 5 km x 5 km. The projection is in metres, so 5 km = 5000 units.
box_size_m = 5_000
half_box = box_size_m / 2

rect = mpatches.Rectangle(
    (poi_x - half_box, poi_y - half_box),
    box_size_m, box_size_m,
    # No fill: at this zoom the box is 0.8% of the view, so only an outline can be seen.
    facecolor="none",
    edgecolor="darkred",
    linewidth=2.0,
    linestyle="-"
)
ax.add_patch(rect)

# 4c. Callout box
ax.annotate("Critical Port Location",
            xy=(poi_x, poi_y), xycoords="data",
            xytext=(poi_x + 100_000, poi_y + 100_000), textcoords="data",
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2",
                            color="black", lw=1.5),
            bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8),
            horizontalalignment="left", verticalalignment="bottom",
            fontsize=10, zorder=6)

# Set the extent to focus on the region: 600 km across, in the projection's metres.
ax.set_extent([poi_x - 300_000, poi_x + 300_000, poi_y - 300_000, poi_y + 300_000],
              crs=CRS_MAP)

# 5. Save the figure
figure_path = OUTPUT / "refactored_annotation_layers.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")

# --- Report ---
print("--- Data ---")
print(f"Land features: {len(land_wgs84)}; water features: {len(water_wgs84)}")
print(f"CRS: {land_wgs84.crs.to_string()} -> axes {type(ax.projection).__name__} "
      f"(UTM zone {CRS_MAP.utm_zone})")
print(f"POI in WGS 84: ({poi_wgs84.x}, {poi_wgs84.y})")
print(f"POI in the map CRS: ({poi_x:,.0f}, {poi_y:,.0f}) m")
print(f"Land area: "
      f"{land_wgs84.to_crs(CRS_MAP.proj4_init).geometry.area.sum() / 1e6:,.0f} sq km")

print("\n--- GeoAxes ---")
print(f"Extent (metres): {tuple(round(float(v), 0) for v in ax.get_extent(crs=CRS_MAP))}")
print(f"Extent (degrees): "
      f"{tuple(round(float(v), 2) for v in ax.get_extent(crs=WGS84))}")

print("\n--- Annotation layer ---")
print(f"Bounding box: {box_size_m:,} m square, {box_size_m ** 2 / 1e6:,.0f} sq km")
print(f"View: {600_000:,} m wide and {600_000:,} m tall")
print(f"Legend entries: 2 patches; annotations: 1 callout, 1 marker, 1 box")

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")

plt.close(fig)
