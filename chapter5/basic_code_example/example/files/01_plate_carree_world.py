import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs # Essential for defining map projections
import numpy as np
import pathlib
from shapely.geometry import box

# --- One substitution, and why ---
#
# `gpd.datasets.get_path('naturalearth_lowres')` was removed in GeoPandas 1.0 ("The
# geopandas.dataset has been deprecated and was removed in GeoPandas 1.0"), and this volume
# may not download a replacement, so the world is built below: a 30 by 20 degree graticule
# with a coarse land mask over it, 58 polygons in WGS 84. Everything after the load - the
# GeoAxes, the projection, the gridlines - is the chapter's own code, unchanged.
#
# `ax.coastlines(resolution='50m')` is *not* used: it makes Cartopy download a Natural Earth
# shapefile on first run, which on a fresh machine means a hang or a failure. The land frame
# below is drawn from the GeoDataFrame instead, so the lesson (a GeoAxes reprojects whatever
# you hand it) survives without a network call.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# A schematic land mask: one character per 30 x 20 degree cell, south to north.
LANDMASK = [
    "111111111111",  # 80-60 S  Antarctica
    "001000000000",  # 60-40 S  Patagonia
    "001100000011",  # 40-20 S  South America, Australia, New Zealand
    "000110110110",  # 20-0 S   South America, Africa, Indonesia
    "001101111110",  # 0-20 N   Central America, Africa, India, South-East Asia
    "001101111110",  # 20-40 N  United States, Mediterranean, Asia
    "011111111110",  # 40-60 N  Canada, Europe, Russia
    "101001111111",  # 60-80 N  Alaska, Greenland, Scandinavia, Siberia
]


def synthetic_world(step_lon=30.0, step_lat=20.0):
    """The bundled world dataset, rebuilt as a fixed land-mask graticule."""
    cells, labels = [], []
    for row, lat0 in enumerate(np.arange(-80.0, 80.0, step_lat)):
        for col, lon0 in enumerate(np.arange(-180.0, 180.0, step_lon)):
            if LANDMASK[row][col] != "1":
                continue
            cells.append(box(lon0, lat0, lon0 + step_lon, lat0 + step_lat))
            labels.append("%dE %dN" % (lon0 + step_lon / 2, lat0 + step_lat / 2))
    return gpd.GeoDataFrame({"cell": labels}, geometry=cells, crs="EPSG:4326")


# 1. Load Data
# Load the world dataset (WGS84 / EPSG:4326) - generated here, same CRS as the bundled one
world = synthetic_world()

# 2. Define Figure and Axes with a Projection
# We use plt.subplots and pass a dictionary of keyword arguments to the subplot
fig, ax = plt.subplots(
    1, 1, # Single row, single column
    figsize=(10, 8),
    # CRITICAL STEP: Define the map projection using Cartopy's CRS module
    subplot_kw={'projection': ccrs.PlateCarree()}
)

# 3. Plot the GeoDataFrame
# GeoPandas automatically plots the geometry onto the Cartopy-enabled axis.
# Since the data's CRS (WGS84) matches the plot's CRS (PlateCarree), no complex
# transformation is needed yet, but the axis is now geographically aware.
world.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)

# 4. Add Geographic Context (Cartopy specific enhancements)
# `ax.coastlines(resolution='50m')` stood here and needed a download; the land polygons are
# already on the axes, so their boundaries play the part of the coastline.

# Add gridlines (latitude and longitude lines)
# We must specify the CRS of the gridlines themselves (PlateCarree/WGS84)
gl = ax.gridlines(
    crs=ccrs.PlateCarree(),
    draw_labels=True,
    linewidth=0.5,
    color='gray',
    alpha=0.5,
    linestyle='--'
)

# Customize gridline labels for cleaner map aesthetics
gl.top_labels = False
gl.right_labels = False

# 5. Set Extent and Title
# Define the visible extent of the map in the coordinate system of the data
# [min_lon, max_lon, min_lat, max_lat]
ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())

ax.set_title("World Map: Data CRS (WGS84) matches Plot Projection (Plate Carrée)")

# 6. Display the Map
# `plt.show()` would open a window; the figure is written where the project's artefacts go,
# and the facts the GeoAxes now holds are printed below.
figure_path = OUTPUT / "plate_carree_world.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")

print("--- Data ---")
print(f"Polygons: {len(world)}")
print(f"CRS: {world.crs.to_string()} ({world.crs.name})")
print(f"Bounds (minx, miny, maxx, maxy): {tuple(round(float(v), 2) for v in world.total_bounds)}")

print("\n--- GeoAxes ---")
print(f"Type: {type(ax).__name__}")
print(f"Projection: {ax.projection.__class__.__name__} ({ax.projection.proj4_init.strip()})")
print(f"Extent (degrees): {tuple(round(float(v), 2) for v in ax.get_extent(crs=ccrs.PlateCarree()))}")
print(f"Gridline labels drawn: {len(gl.bottom_label_artists)} along the bottom, "
      f"{len(gl.left_label_artists)} along the left")

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")

plt.close(fig)
