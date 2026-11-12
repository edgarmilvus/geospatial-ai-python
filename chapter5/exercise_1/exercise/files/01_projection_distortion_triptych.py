import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
import numpy as np
import pathlib
from shapely.geometry import box

# --- Two substitutions, and why ---
#
# 1. Data. `gpd.datasets.get_path('naturalearth_lowres')` was removed in GeoPandas 1.0, and
#    this volume may not download a replacement, so the world is a fixed 30 x 20 degree
#    graticule with a coarse land mask: 58 polygons in WGS 84, enough to see what each
#    projection does to a rectangle of known size.
# 2. `from cartopy import crs as ccrs` was imported by the chapter and then unused, because the
#    book reprojected the frame itself. Here the import does the work: every one of the three
#    panels is a GeoAxes with its own projection, and the frame stays in WGS 84 throughout.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

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
    """A fixed land-mask graticule standing in for the bundled world dataset."""
    cells, labels = [], []
    for row, lat0 in enumerate(np.arange(-80.0, 80.0, step_lat)):
        for col, lon0 in enumerate(np.arange(-180.0, 180.0, step_lon)):
            if LANDMASK[row][col] != "1":
                continue
            cells.append(box(lon0, lat0, lon0 + step_lon, lat0 + step_lat))
            labels.append("%dE %dN" % (lon0 + step_lon / 2, lat0 + step_lat / 2))
    return gpd.GeoDataFrame({"cell": labels}, geometry=cells, crs="EPSG:4326")


WGS84 = ccrs.PlateCarree()

# 1. Data acquisition and preparation
world = synthetic_world()
world = world.to_crs(epsg=4326)  # already WGS 84, kept explicit as the book does

# The three projections are Cartopy CRS objects now, not EPSG strings: the axes are what
# carries the projection, and it is the same object we measure the areas with.
crs_geographic = ccrs.PlateCarree()      # degrees, the data as received
crs_equal_area = ccrs.EckertIV()         # area is preserved
crs_compromise = ccrs.epsg(3857)         # Web Mercator: shape preserved, area explodes

# The numbers behind the three pictures. A degree squared is not an area; the equal-area and
# the Mercator totals are both in square metres, so those two *can* be compared. Asking a
# geographic frame for `.area` earns a UserWarning - that warning is the lesson, so it is
# silenced here rather than printed into the transcript.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    area_deg2 = world.geometry.area.sum()
area_eckert = world.to_crs(crs_equal_area.proj4_init).geometry.area.sum()
area_mercator = world.to_crs(crs_compromise.proj4_init).geometry.area.sum()

print("--- The same 58 cells in three projections ---")
print(f"Geographic (EPSG:4326): {area_deg2:,.2f} square degrees - a number with no unit")
print(f"Equal area (Eckert IV): {area_eckert / 1e6:,.0f} sq km")
print(f"Web Mercator (EPSG:3857): {area_mercator / 1e6:,.0f} sq km")
print(f"Mercator / Eckert IV: {area_mercator / area_eckert:.2f}x")

# 2. Figure setup: three GeoAxes, one projection each
fig = plt.figure(figsize=(18, 6))
fig.suptitle("Visualizing Geographic Projection Distortion: Area vs. Conformality",
             fontsize=16, y=1.02)

# 3. Projection application and plotting. The frame never changes; the axes does.
panels = [
    (fig.add_subplot(1, 3, 1, projection=crs_geographic),
     "1. Geographic CRS (WGS 84 / EPSG:4326)", "lightgrey", area_deg2),
    (fig.add_subplot(1, 3, 2, projection=crs_equal_area),
     "2. Equal Area Projection (Eckert IV)", "skyblue", area_eckert),
    (fig.add_subplot(1, 3, 3, projection=crs_compromise),
     "3. Compromise Projection (Web Mercator / EPSG:3857)", "salmon", area_mercator),
]

for ax, title, color, _area in panels:
    # One call, and the GeoAxes reprojects every polygon from WGS 84 into its own projection.
    ax.add_geometries(list(world.geometry), crs=WGS84, facecolor=color,
                      edgecolor="black", linewidth=0.3)
    ax.set_title(title, fontsize=10)
    ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.4)

# Panel 1 covers the whole globe; panel 2 follows the projection's own bounds; panel 3 is cut
# at about +/- 85 degrees of latitude, where Web Mercator ends.
panels[0][0].set_global()
panels[1][0].set_global()
x_limit_3857 = 20037508.34
panels[2][0].set_extent([-x_limit_3857, x_limit_3857, -x_limit_3857, x_limit_3857],
                        crs=crs_compromise)

for ax, _title, _color, _area in panels:
    ax.set_xticks([])
    ax.set_yticks([])

plt.tight_layout(rect=[0, 0, 1, 0.95])

# 4. Save the figure (the book ends on `plt.show()`; a script writes a file)
figure_path = OUTPUT / "projection_distortion_triptych.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")

print("\n--- The three GeoAxes ---")
for ax, title, _color, area in panels:
    extent = ax.get_extent(crs=ax.projection)
    print(f"{type(ax.projection).__name__:16s} extent "
          f"({extent[0]:,.0f}, {extent[1]:,.0f}) x ({extent[2]:,.0f}, {extent[3]:,.0f})")
# The same longitude and latitude, on each axes: this is what "the axes owns the projection"
# means, and why the cells keep their place while changing their shape.
lon, lat = 10.0, 60.0
for ax, _title, _color, _area in panels:
    x, y = ax.projection.transform_point(lon, lat, WGS84)
    print(f"({lon}, {lat}) on {type(ax.projection).__name__:16s} -> ({x:,.1f}, {y:,.1f})")

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")
print(f"Panels: {len(panels)}; features per panel: {len(world)}")
print(f"Mercator extent: +/-{x_limit_3857:,.2f} m")

plt.close(fig)
