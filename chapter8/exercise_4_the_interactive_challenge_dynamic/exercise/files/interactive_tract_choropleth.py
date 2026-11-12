import geopandas as gpd
import numpy as np
import folium
import mapclassify
import pathlib
import warnings
from folium.features import GeoJsonTooltip
from matplotlib import colormaps
from matplotlib.colors import Normalize, rgb2hex
from shapely.geometry import box

# --- Four corrections to the book's solution, and why ---
#
# 1. `plt.cm.get_cmap('RdYlGn', k)` no longer exists: matplotlib 3.9 removed the
#    `get_cmap` shim in favour of `matplotlib.colormaps[...]`. `matplotlib.colors` was
#    also used without being imported, so `rgb2hex` raised a NameError on the first
#    feature. Both are fixed here.
# 2. The class of a tract is `classifier.yb`, one entry per observation. The book indexes
#    that array with the class id (`classifier.yb[classifier.bins.searchsorted(x)]`),
#    which returns the class of *some other* tract - and raises IndexError for a value
#    above the last break.
# 3. The map used to be saved only in a commented-out line. It is written into the
#    project's output/ folder, and `tiles=None` keeps the base layer list at the two the
#    requirement asks for, instead of three with OpenStreetMap twice.
# 4. The data is seeded, so the classes and the colours are reproducible.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# The tracts are a schematic grid in the same coordinate range as a real extent, not
# surveyed parcels, so geopandas' centroid warning is not a bug here.
warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')
# Folium 0.19 warns that the CartoDB tile names now need a key. Nothing is fetched when
# the file is built - the reader's browser loads the tiles - so the build stays quiet.
warnings.filterwarnings('ignore', message='CartoDB tiles now require an API key')

np.random.seed(42)

# 1. Preparation for Interaction (Simulated Data)
N_tracts = 30
tract_data = {
    'Tract ID': [f'T{i:04d}' for i in range(N_tracts)],
    'Pop2020': np.random.randint(1000, 5000, N_tracts),
    # Simulate population change between -20% and +30%
    'PopChange_Percent': np.random.uniform(-20.0, 30.0, N_tracts),
}

# Create dummy geometries (must be in WGS 84 / EPSG:4326 for Folium)
tract_gdf = gpd.GeoDataFrame(
    tract_data,
    geometry=[box(i % 6, i // 6, (i % 6) + 0.9, (i // 6) + 0.9) for i in range(N_tracts)],
    crs="EPSG:4326"
)

# Apply Jenks Natural Breaks classification
k_classes = 6
classifier = mapclassify.NaturalBreaks(tract_gdf['PopChange_Percent'], k=k_classes)
tract_gdf['Jenks_Class'] = classifier.yb

# Convert GeoDataFrame to GeoJSON string for Folium
# Ensure necessary columns are strings/floats for tooltip display
tract_gdf['Pop2020'] = tract_gdf['Pop2020'].round(0).astype(int)
tract_gdf['PopChange_Percent'] = tract_gdf['PopChange_Percent'].round(2)
geojson_data = tract_gdf.to_json()

# 2. Folium Integration and Conversion
# Calculate centroid for map centering
center_x = tract_gdf.geometry.centroid.x.mean()
center_y = tract_gdf.geometry.centroid.y.mean()

m = folium.Map(location=[center_y, center_x], zoom_start=8, tiles=None)

# Define style function based on Jenks classification.
# The ramp is sampled at class position i/(k-1), so class 0 is red and class 5 green.
cmap = colormaps['RdYlGn']
colour_norm = Normalize(0, k_classes - 1)


def style_function(feature):
    class_index = feature['properties']['Jenks_Class']
    color = rgb2hex(cmap(colour_norm(class_index)))
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7
    }


# 3. Interactive Tooltip Implementation
folium.GeoJson(
    geojson_data,
    name='Population Change (Jenks Classified)',
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=['Tract ID', 'Pop2020', 'PopChange_Percent'],
        aliases=['Tract ID:', '2020 Population:', 'Pop Change (2010-2020 %):'],
        localize=True,
        sticky=False
    )
).add_to(m)

# 4. Layer Control and Basemaps
folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
folium.TileLayer('cartodbdarkmatter', name='CartoDB Dark Matter').add_to(m)
folium.LayerControl().add_to(m)

# 5. Save the map where the rest of this project's artefacts live
output_file = OUTPUT / "interactive_tract_choropleth.html"
m.save(str(output_file))

print(f"--- {N_tracts} census tracts in WGS 84 ---")
print(f"Map centre: {center_y:.4f} N, {center_x:.4f} E at zoom 8")
print(f"Population change: {tract_gdf['PopChange_Percent'].min():+.2f}% to "
      f"{tract_gdf['PopChange_Percent'].max():+.2f}%")
print("\nJenks breaks (%): " + ", ".join(f"{value:.2f}" for value in classifier.bins))
print("Tracts per class: " + ", ".join(str(int(count)) for count in classifier.counts))
print("\nColour per class (RdYlGn, red = decline, green = growth):")
for index in range(k_classes):
    counts = int((tract_gdf['Jenks_Class'] == index).sum())
    print(f"  class {index}: {rgb2hex(cmap(colour_norm(index)))}  {counts} tract(s)")

print("\n--- Figure ---")
print(f"Saved: {output_file.relative_to(OUTPUT.parent)}")
print(f"Bytes: {output_file.stat().st_size}")
print(f"Tooltip fields: Tract ID, Pop2020, PopChange_Percent")
