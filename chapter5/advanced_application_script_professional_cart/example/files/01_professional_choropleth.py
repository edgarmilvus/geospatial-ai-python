import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
import numpy as np
import pathlib
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, LinearSegmentedColormap
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
from shapely.geometry import Polygon, box

# --- Two substitutions, and why ---
#
# 1. Data. The chapter reads `gpd.datasets.get_path('naturalearth_lowres')` and filters the
#    United States out of it. GeoPandas 1.0 removed those datasets, and this volume may not
#    download a replacement, so the map is drawn over a synthetic eleven-district region in
#    the same place (central California, 35-40 N), generated below and seeded.
# 2. The basemap. The chapter calls
#    `cx.add_basemap(ax, crs=..., source=cx.providers.Stamen.TonerLite)`, which fetches XYZ
#    tiles over the network and now also needs a Stadia key. It is replaced by two polygons of
#    our own - water and land - handed to the same GeoAxes with their CRS, so Cartopy performs
#    exactly the reprojection contextily's tiles would have needed. No network call.
#
# GeoPandas 1.0 no longer reprojects for a Cartopy axes: `gdf.plot(ax=geoax)` draws degrees on
# an axes whose units are metres. The layers are therefore handed to the GeoAxes with
# `ax.add_geometries(..., crs=ccrs.PlateCarree())`, which is the Cartopy call that does the
# transformation, and the choropleth's colours and colour bar are built explicitly.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

WGS84 = ccrs.PlateCarree()

# An 11-district mosaic on a grid 1.2 degrees wide, so the districts are separate shapes.
DISTRICT_CENTRES = [
    (-122.6, 39.6), (-121.4, 39.6), (-120.2, 39.6),
    (-122.6, 38.4), (-121.4, 38.4), (-120.2, 38.4), (-119.0, 38.4),
    (-122.6, 37.2), (-121.4, 37.2), (-120.2, 37.2), (-119.0, 37.2),
]


def synthetic_region():
    """Eleven districts as irregular WGS 84 polygons, fixed shape, no randomness."""
    polygons, names = [], []
    angles = np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False)
    for index, (lon0, lat0) in enumerate(DISTRICT_CENTRES):
        radii = 0.42 * (1.0 + 0.20 * np.sin(3.0 * angles + index))
        ring = [(lon0 + r * np.cos(a) / np.cos(np.radians(lat0)), lat0 + r * np.sin(a))
                for a, r in zip(angles, radii)]
        polygons.append(Polygon(ring))
        names.append("District %d" % (index + 1))
    return gpd.GeoDataFrame({"name": names}, geometry=polygons, crs="EPSG:4326")


# --- 1. Setup and custom helper functions ---

def add_north_arrow(ax, xy=(0.95, 0.9), size=0.03):
    """Adds a north arrow patch to the specified axes, anchored relative to the axis bounds."""
    arrow_center_x = ax.get_xlim()[0] + (ax.get_xlim()[1] - ax.get_xlim()[0]) * xy[0]
    arrow_center_y = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * xy[1]

    # ax.annotate draws the arrow and the 'N' label together, in data coordinates - which on
    # a GeoAxes are metres of the projection, not degrees.
    ax.annotate("N", xy=(arrow_center_x, arrow_center_y + size * 100),
                xytext=(arrow_center_x, arrow_center_y),
                arrowprops=dict(facecolor="black", shrink=0.0, width=5, headwidth=15),
                ha="center", va="center", fontsize=14, fontweight="bold",
                clip_on=False, transform=ax.transData)


# The basemap: water and land, both in WGS 84, so the GeoAxes has to reproject them.
BASEMAP = gpd.GeoDataFrame(
    {"layer": ["water", "land"]},
    geometry=[box(-125.0, 33.0, -115.0, 42.0), box(-123.5, 36.0, -117.0, 40.5)],
    crs="EPSG:4326",
)

# Define a custom color ramp (sequential scheme for density visualization)
colors = ["#fef0d9", "#fdcc8a", "#fc8d59", "#e34a33", "#b30000"]
custom_cmap = LinearSegmentedColormap.from_list("DensityMap", colors, N=256)

# --- 2. Data acquisition and preparation ---

districts = synthetic_region()

# Synthesize a 'Population_Density' metric (simulating real-world data)
rng = np.random.default_rng(42)
districts["Population_Density"] = rng.integers(80, 4_200, size=len(districts))

# The metric column needs an area, and an area needs a projection: degrees squared is not one.
districts_metric = districts.to_crs("EPSG:3857")
districts["Area_km2"] = districts_metric.geometry.area / 1e6

# --- 3. Figure and axes: the projection is chosen here ---

# ccrs.epsg(3857) is Web Mercator, the projection contextily's tiles arrive in.
MERCATOR = ccrs.epsg(3857)
fig, ax = plt.subplots(1, 1, figsize=(12, 12), subplot_kw={"projection": MERCATOR})

# 3a. The basemap first, handed over in WGS 84: Cartopy projects it onto the axes for us.
water, land = BASEMAP.geometry.iloc[0], BASEMAP.geometry.iloc[1]
ax.add_geometries([water], crs=WGS84, facecolor="#dcecf7", edgecolor="none", zorder=0)
ax.add_geometries([land], crs=WGS84, facecolor="#f2efe9", edgecolor="none", zorder=0)

# 3b. The choropleth. One colour per district, from the custom ramp; `crs=WGS84` is what tells
#     the GeoAxes the numbers are degrees and must be transformed.
norm = Normalize(vmin=districts["Population_Density"].min(),
                 vmax=districts["Population_Density"].max())
facecolors = [custom_cmap(norm(value)) for value in districts["Population_Density"]]
ax.add_geometries(list(districts.geometry), crs=WGS84, facecolor=facecolors,
                  edgecolor="dimgray", linewidth=0.8, zorder=2)

# The legend the chapter gets from `legend=True` is built explicitly: a ScalarMappable and a
# colour bar, because the axes is fed colour values rather than a data column.
mappable = ScalarMappable(norm=norm, cmap=custom_cmap)
mappable.set_array(districts["Population_Density"].values)
fig.colorbar(mappable, ax=ax, orientation="horizontal", shrink=0.6, pad=0.05,
             label="Population Density Index (Synthetic)")

# 3c. Cartographic elements. A scale bar whose length is real distance: on an EPSG:3857
#     GeoAxes the data units are metres, so 50 km is 50 000 of them.
SCALE_BAR_M = 50_000
scalebar = AnchoredSizeBar(ax.transData,
                           SCALE_BAR_M,
                           "50 km",
                           "lower left",
                           pad=0.5,
                           color="black",
                           frameon=False,
                           size_vertical=2,
                           fontproperties=fm.FontProperties(size=10))
ax.add_artist(scalebar)

# 3d. Final map aesthetics. The view is the districts plus a margin, in the projection's
#     metres; `set_extent` is where a GeoAxes differs from a plain axes.
west, south, east, north = districts_metric.total_bounds
pad = 0.10 * max(east - west, north - south)
ax.set_extent([west - pad, east + pad, south - pad, north + pad], crs=MERCATOR)
add_north_arrow(ax)

ax.set_title("Professional GeoAI Visualization: Population Density (Web Mercator Projection)",
             fontsize=16)
ax.set_axis_off()
plt.tight_layout()

# --- 4. Save the figure ---

figure_path = OUTPUT / "custom_geo_visualization_hires.png"
fig.savefig(figure_path, dpi=300, bbox_inches="tight")

# One known district centre, in both coordinate systems: the proof that the axes projects.
lon, lat = DISTRICT_CENTRES[4]
proj_x, proj_y = ax.projection.transform_point(lon, lat, WGS84)

print("--- Data ---")
print(f"Districts: {len(districts)}")
print(f"Source CRS: {districts.crs.to_string()} -> axes {ax.projection.__class__.__name__}")
print(f"Projected area: {districts_metric.geometry.area.sum() / 1e6:,.0f} sq km")
print(f"Density index: {districts['Population_Density'].min()}-"
      f"{districts['Population_Density'].max()}")

print("\n--- GeoAxes ---")
print(f"Type: {type(ax).__name__}")
print(f"Projection: {ax.projection.__class__.__name__} (EPSG:3857)")
print(f"Extent (degrees): "
      f"{tuple(round(float(v), 2) for v in ax.get_extent(crs=WGS84))}")
x0, x1, y0, y1 = ax.get_extent(crs=MERCATOR)
print(f"Extent (metres): ({x0:,.0f}, {x1:,.0f}) easting, ({y0:,.0f}, {y1:,.0f}) northing")
print(f"District 5 at ({lon}, {lat}) -> ({proj_x:,.1f}, {proj_y:,.1f}) m")
print(f"Scale bar: {SCALE_BAR_M:,} m of the projection")
print(f"Colormap stops: {custom_cmap.N}")

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")

plt.close(fig)
