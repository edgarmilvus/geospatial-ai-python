import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import numpy as np
import pathlib
from shapely.geometry import box, Polygon

# --- Two substitutions, and why ---
#
# 1. Data. `gpd.datasets.get_path('naturalearth_lowres')` was removed in GeoPandas 1.0, so the
#    continent is fourteen synthetic polygons: eleven over the mainland, three round the
#    Aleutians so the inset has something to show. Fixed shape, no randomness.
# 2. No Cartopy dataset is used: `ax.coastlines()` and `cfeature.LAND` would download Natural
#    Earth shapefiles on first run, which offline means a hang. The land is the frame we build,
#    handed to each GeoAxes with `crs=ccrs.PlateCarree()` so Cartopy performs the projection.
#
# The locator box is the interesting part: it is the inset's extent, expressed in the inset's
# projection and converted into the main map's projection with `transform_points`, which is the
# Cartopy equivalent of the `to_crs` call the book used on a GeoSeries.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

WGS84 = ccrs.PlateCarree()

CENTRES = [(-160.0, 63.0), (-150.0, 60.0), (-135.0, 58.0), (-120.0, 50.0),
           (-110.0, 45.0), (-100.0, 40.0), (-90.0, 35.0), (-80.0, 30.0),
           (-70.0, 45.0), (-95.0, 55.0), (-75.0, 50.0),
           (-178.0, 53.0), (-172.0, 54.0), (-166.0, 56.0)]  # the last three are Aleutian
NAMES = ["Alaska Interior", "Yukon", "British Columbia", "Washington", "Idaho",
         "Colorado", "Texas", "Florida", "Newfoundland", "Manitoba", "Quebec",
         "Attu", "Kiska", "Unalaska"]


def synthetic_continent():
    """Fourteen irregular polygons in WGS 84, fixed shape, no randomness."""
    polygons, names = [], []
    angles = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    for index, ((lon0, lat0), name) in enumerate(zip(CENTRES, NAMES)):
        # The mainland blobs are wide enough to overlap their neighbours into one body; the
        # three Aleutian ones stay small, which is why the inset has something to enlarge.
        base = 1.1 if lon0 < -160.0 else 6.0
        radii = base * (1.0 + 0.15 * np.sin(3.0 * angles + index))
        ring = [(lon0 + r * np.cos(a) / np.cos(np.radians(lat0)), lat0 + r * np.sin(a))
                for a, r in zip(angles, radii)]
        polygons.append(Polygon(ring))
        names.append(name)
    return gpd.GeoDataFrame({"name": names, "continent": "North America"},
                            geometry=polygons, crs="EPSG:4326")


# 1. Data loading and preparation
world = synthetic_continent()

# Define the two projections. The main map is a continental equal-area projection; the inset is
# a UTM zone, whose units are metres over a few hundred kilometres.
CRS_MAIN = ccrs.AlbersEqualArea(central_longitude=-96.0, central_latitude=37.5,
                                standard_parallels=(29.5, 45.5))
# The book's inset is UTM zone 5N. A UTM zone is a six-degree strip, and the Aleutian chain
# crosses four of them, so an azimuthal equidistant projection centred on the chain shows the
# whole inset without cutting it at a zone boundary.
CRS_INSET = ccrs.AzimuthalEquidistant(central_longitude=-175.0, central_latitude=54.0)

# Filter main data (North America)
main_data = world[world["continent"] == "North America"]

# Filter inset data: a rough box in WGS 84 round the Aleutians
aleutians_bbox_wgs84 = box(-180, 50, -160, 60)
# Keep the features whose centre falls inside the window. The book clipped the frame to the
# box; a clipped fragment of the mainland is a long wedge that fills the inset, so the inset
# gets whole islands instead.
inset_data = world[world.geometry.representative_point().within(aleutians_bbox_wgs84)]

print("--- Data ---")
print(f"Main features: {len(main_data)} in WGS 84, drawn on a {type(CRS_MAIN).__name__} axes")
print(f"Inset features: {len(inset_data)} in WGS 84, drawn on a {type(CRS_INSET).__name__} axes")

# 2. Figure and axes instantiation: two GeoAxes, two projections
fig = plt.figure(figsize=(12, 10))

# Main axes (add_subplot for standard placement)
ax_main = fig.add_subplot(1, 1, 1, projection=CRS_MAIN)
ax_main.add_geometries(list(main_data.geometry), crs=WGS84,
                       facecolor="lightgray", edgecolor="black", linewidth=0.5)
ax_main.set_title("North America (Albers Equal Area) with Aleutian Islands Inset",
                  fontsize=16)

# The main map's graticule: Cartopy's own, labelled along the map boundary.
gl_main = ax_main.gridlines(crs=WGS84, draw_labels=True, linewidth=0.4,
                            color="gray", alpha=0.4, linestyle="--")
gl_main.top_labels = False
gl_main.right_labels = False

# 3. The inset: add_axes takes normalized figure placement [left, bottom, width, height], and
#    `projection=` makes it a second GeoAxes with a different CRS.
ax_inset = fig.add_axes([0.65, 0.15, 0.25, 0.25], projection=CRS_INSET)
inset_artists = ax_inset.add_geometries(list(inset_data.geometry), crs=WGS84,
                                        facecolor="teal", edgecolor="black", linewidth=0.7)
# A GeoAxes clips to its projection's boundary, not to the rectangle the inset occupies, so a
# shape that leaves the inset's extent is drawn over the main map. Clipping to the axes' own
# box is what a smaller map in the corner needs.
inset_artists.set_clip_box(ax_inset.bbox)

# The inset's view, in its own projection: the projected bounds of the features it shows.
inset_projected = inset_data.to_crs(CRS_INSET.proj4_init).total_bounds
ib_x0, ib_y0, ib_x1, ib_y1 = inset_projected
ax_inset.set_extent([ib_x0, ib_x1, ib_y0, ib_y1], crs=CRS_INSET)
ax_inset.set_title("Aleutian Islands Detail", fontsize=10)
ax_inset.spines["right"].set_visible(False)
ax_inset.spines["top"].set_visible(False)

# 4. Contextual linkage: the locator box, converted from the inset's projection into the
#    main map's. `transform_points` takes the source CRS, then the x and y arrays.
ex0, ex1, ey0, ey1 = ax_inset.get_extent(crs=CRS_INSET)
corners = CRS_MAIN.transform_points(CRS_INSET,
                                    np.array([ex0, ex1, ex0, ex1]),
                                    np.array([ey0, ey0, ey1, ey1]))
xmin_main, ymin_main = corners[:, 0].min(), corners[:, 1].min()
xmax_main, ymax_main = corners[:, 0].max(), corners[:, 1].max()
width_main = xmax_main - xmin_main
height_main = ymax_main - ymin_main

locator_box = mpatches.Rectangle(
    (xmin_main, ymin_main), width_main, height_main,
    facecolor="none", edgecolor="red", linewidth=2, linestyle="--"
)
ax_main.add_patch(locator_box)

# The main map is framed on the continent's own extent *in the projection*, plus a margin. A
# box in degrees would be stretched by the projection before it reached the axes; a box in
# Albers metres is already the shape the axes draws.
m_x0, m_y0, m_x1, m_y1 = main_data.to_crs(CRS_MAIN.proj4_init).total_bounds
m_margin = 0.04 * max(m_x1 - m_x0, m_y1 - m_y0)
ax_main.set_extent([m_x0 - m_margin, m_x1 + m_margin, m_y0 - m_margin, m_y1 + m_margin],
                   crs=CRS_MAIN)

# 5. Save the figure
figure_path = OUTPUT / "main_map_with_inset.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")

print("\n--- The two GeoAxes ---")
print(f"Main:  {type(ax_main.projection).__name__}, extent "
      f"{tuple(round(float(v), 0) for v in ax_main.get_extent(crs=CRS_MAIN))} m")
print(f"Inset: {type(ax_inset.projection).__name__}, extent "
      f"{tuple(round(float(v), 0) for v in ax_inset.get_extent(crs=CRS_INSET))} m")
print(f"Main gridline labels: {len(gl_main.bottom_label_artists)} bottom, "
      f"{len(gl_main.left_label_artists)} left")

print("\n--- Locator box ---")
print(f"Width x height in the main projection: {width_main:,.0f} x {height_main:,.0f} m")
print(f"Area of the box: {width_main * height_main / 1e6:,.0f} sq km")
print(f"Box centre: ({(xmin_main + xmax_main) / 2:,.0f}, "
      f"{(ymin_main + ymax_main) / 2:,.0f}) m")

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")

plt.close(fig)
