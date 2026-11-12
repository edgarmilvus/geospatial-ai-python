import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import matplotlib.pyplot as plt
import mapclassify
import pathlib
import warnings
from shapely.geometry import Polygon

# --- Two corrections to the book's solution, and why ---
#
# 1. The break point of each class is printed, and the classification is handed to
#    `.plot()` as a UserDefined scheme, so the legend shows the breaks that were computed
#    here. (Geopandas 1.0 no longer accepts a classifier object as `scheme`.)
# 2. `plt.show()`. A script has no window, so the figure goes to the project's output/
#    folder and the breaks are printed.
#
# The exercise asks for k=7 over four counties. Mapclassify allows it and simply leaves
# classes empty - which is the point of the counts printed below.
#
# The coordinates are abstract plane units, not degrees, so the areas below are topology:
# geopandas warns about the geographic CRS and the warning is not a bug here.
warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# 1. Data Preparation and Calculation (Simulated Data)
# Create dummy geometries (4 counties, one small urban, three large rural)
data = {
    'FIPS': ['01001', '01002', '01003', '01004'],
    'Population': [5000000, 10000, 15000, 8000], # Highly skewed population
    'LandArea_sqmi': [5, 500, 600, 700], # Highly skewed area
    'geometry': [
        Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
        Polygon([(2, 0), (2, 2), (4, 2), (4, 0)]),
        Polygon([(5, 0), (5, 3), (8, 3), (8, 0)]),
        Polygon([(9, 0), (9, 4), (13, 4), (13, 0)])
    ]
}
counties_gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

# Calculate Density
counties_gdf['Density'] = counties_gdf['Population'] / counties_gdf['LandArea_sqmi']

# Handle potential division by zero (not strictly needed here but good practice)
counties_gdf['Density'] = counties_gdf['Density'].fillna(0)

# Seven classes, as the exercise requires. Four counties cannot fill seven classes, so
# some of them come back empty; the counts below show how many.
K_CLASSES = 7

equal_interval = mapclassify.EqualInterval(counties_gdf['Density'], k=K_CLASSES)
quantiles = mapclassify.Quantiles(counties_gdf['Density'], k=K_CLASSES)

fig, axes = plt.subplots(1, 2, figsize=(15, 7))

# 2. Visualization A: Equal Interval Classification
counties_gdf.plot(
    column='Density',
    ax=axes[0],
    legend=True,
    scheme='UserDefined',
    classification_kwds={'bins': equal_interval.bins},
    cmap='YlOrRd',
    edgecolor='black',
    linewidth=0.5
)
axes[0].set_title(f'Map A: Population Density (Equal Interval, k={K_CLASSES})')
axes[0].set_axis_off()

# Critical Analysis Comment for Equal Interval:
# The Equal Interval map visually emphasizes only the most densely populated, typically small, urban areas, often rendering the vast majority of the map in the lightest color bin.
# This happens because the high density of the single urban county (5,000,000/5 = 1,000,000) creates class breaks so wide that the low densities of the rural counties (20, 25, 11.4) all fall into the lowest class.

# 3. Visualization B: Quantile Classification
counties_gdf.plot(
    column='Density',
    ax=axes[1],
    legend=True,
    scheme='UserDefined',
    classification_kwds={'bins': quantiles.bins},
    cmap='YlOrRd',
    edgecolor='black',
    linewidth=0.5
)
axes[1].set_title(f'Map B: Population Density (Quantiles, k={K_CLASSES})')
axes[1].set_axis_off()

# Critical Analysis Comment for Quantile:
# The Quantile method ensures that each color bin represents an equal number of geographic units (counties). With 4 units and k=7 the algorithm can only put one county in every other bin, so three bins come back empty and each of the four densities gets its own colour anyway - even though the top bin spans 99.998% of the total density range.

fig.tight_layout()

# 4. Report what each scheme did with the same four numbers
print("--- Density per county ---")
for fips, density in zip(counties_gdf['FIPS'], counties_gdf['Density']):
    print(f"  {fips}: {density:,.2f} people per square mile")
print(f"Range: {counties_gdf['Density'].min():,.2f} to {counties_gdf['Density'].max():,.2f}")

print("\n--- Equal Interval (width = range / k) ---")
print("Breaks: " + ", ".join(f"{value:,.2f}" for value in equal_interval.bins))
print("Counties per class: " + ", ".join(str(int(c)) for c in equal_interval.counts))
print(f"Class of each county: {[int(c) for c in equal_interval.yb]}")

print("\n--- Quantiles (equal count per class) ---")
print("Breaks: " + ", ".join(f"{value:,.2f}" for value in quantiles.bins))
print("Counties per class: " + ", ".join(str(int(c)) for c in quantiles.counts))
print(f"Class of each county: {[int(c) for c in quantiles.yb]}")

figure_path = OUTPUT / "density_classification_bias.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")
