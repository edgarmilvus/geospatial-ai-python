import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import pathlib
import warnings

# --- One substitution, and why ---
#
# The book ends with `plt.show()`, which in a script with no window either blocks or
# draws nothing. The figure is written into this project's own output/ folder instead,
# and the numbers behind it are printed, so the example can be checked without eyes.
#
# The coordinates below (0 to 40) are abstract units, not degrees, so the planar area
# in "square degrees" is topology rather than ground truth: geopandas warns about the
# geographic CRS and the warning is not a bug here.
warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- 1. Define Synthetic Geospatial Data (The Boundaries) ---
# We use shapely to manually define simple geometric shapes (polygons)
# that represent our three abstract geographic regions.
regions_data = {
    'RegionID': ['A01', 'B02', 'C03'],
    'RegionName': ['North Sector', 'Central Zone', 'South District'],
    'geometry': [
        Polygon([(0, 0), (0, 10), (10, 10), (10, 0)]),      # Region A01: Square
        Polygon([(15, 5), (15, 15), (25, 15), (25, 5)]),    # Region B02: Square
        Polygon([(30, 0), (30, 20), (40, 20), (40, 0)])     # Region C03: Rectangle
    ]
}
# Convert the dictionary into a GeoDataFrame (GDF).
# CRS (Coordinate Reference System) is set to a common standard (WGS 84).
geo_df = gpd.GeoDataFrame(regions_data, crs="EPSG:4326")

# --- 2. Define Synthetic Statistical Data (The Metrics) ---
# This data contains the quantitative metric we want to visualize.
# The 'RegionID' column is the essential link for merging.
stat_data = {
    'RegionID': ['A01', 'B02', 'C03'],
    'PopulationDensity': [150, 450, 250], # The main variable for coloring
    'VoterTurnout': [0.65, 0.78, 0.71]    # An additional variable
}
stat_df = pd.DataFrame(stat_data)

# --- 3. Merge Geospatial and Statistical Data ---
# The core operation: combining the boundaries (geo_df) with the metrics (stat_df).
# We merge based on the common key 'RegionID'.
merged_df = geo_df.merge(stat_df, on='RegionID', how='left')

print("--- Merged GeoDataFrame ---")
print(merged_df[['RegionID', 'RegionName', 'PopulationDensity', 'VoterTurnout']]
      .to_string(index=False))
print(f"Rows: {len(merged_df)}; CRS: {merged_df.crs.to_string()}")
print(f"Missing densities after the left join: "
      f"{int(merged_df['PopulationDensity'].isna().sum())}")
print(f"Planar areas (square degrees): "
      f"{[int(a) for a in merged_df.geometry.area]}")

# --- 4. Generate the Choropleth Map ---
# Prepare the Matplotlib figure and axis object for plotting.
fig, ax = plt.subplots(1, 1, figsize=(10, 10))

# The .plot() method of the GeoDataFrame handles the visualization.
# The 'column' parameter is the key instruction for choropleth generation.
merged_df.plot(
    column='PopulationDensity', # Use this column to determine color intensity
    ax=ax,                      # Plot onto the defined axis
    legend=True,                # Display the color bar legend
    cmap='plasma',              # Select the color scheme (Color Map)
    linewidth=1.5,              # Thickness of the border lines
    edgecolor='black'           # Color of the border lines
)

# --- 5. Final Visualization Enhancements ---
ax.set_title('Basic Synthetic Choropleth Map: Population Density', fontsize=16)
ax.set_axis_off() # Crucial for map visualization: removes unnecessary coordinate ticks

# --- 6. Save the map and report what it encodes ---
#
# The colour of each polygon is the value of the row divided into the column's own
# range: 150 is the bottom of the ramp, 450 the top, 250 lands two fifths of the way up.
ramp = ax.collections[0]
vmin, vmax = ramp.norm.vmin, ramp.norm.vmax
print("\n--- Ramp ---")
print(f"Colour range: {vmin:.0f} to {vmax:.0f} (the column's own min and max)")
for region_id, density in zip(merged_df['RegionID'], merged_df['PopulationDensity']):
    print(f"  {region_id}: density {density:>3.0f} -> "
          f"{(density - vmin) / (vmax - vmin):.2f} of the ramp")

figure_path = OUTPUT / "basic_choropleth_density.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")
print(f"Colour bar drawn: {len(fig.axes) > 1}")
