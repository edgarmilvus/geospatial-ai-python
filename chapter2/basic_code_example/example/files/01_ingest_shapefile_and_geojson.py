"""Chapter 2, example 1 — one reader for two vector formats.

The problem: the same three European cities arrive twice, once as an ESRI
Shapefile (the legacy multi-file format) and once as GeoJSON (the modern
single-file format). Both must come back as a GeoDataFrame with its geometry
column and its CRS intact, through the same call.

The listing is self-contained: it writes the two files into the project's
output/ folder first, reads them back, inspects the result, and cleans up.
"""
import glob
import os
import pathlib
import warnings

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Suppress warnings that might arise during file creation/cleanup
warnings.filterwarnings('ignore')

# Everything this listing writes lands in the project's own output/ folder,
# so the script behaves the same whatever directory it is started from.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 1. SETUP: Creating Self-Contained Test Data ---
# In a real-world scenario, these files would already exist.
# We create them here to make the example runnable.

# Define the base data for three European cities
data_points = {
    'City': ['London', 'Paris', 'Berlin'],
    'Country': ['UK', 'France', 'Germany'],
    'Population_M': [9.6, 2.1, 3.8]
}
df = pd.DataFrame(data_points)

# Define coordinates (Longitude, Latitude)
coords = [
    (0.1278, 51.5074),  # London
    (2.3522, 48.8566),  # Paris
    (13.4050, 52.5200)  # Berlin
]

# Create Point geometries
geometry = [Point(lon, lat) for lon, lat in coords]

# Initialize the GeoDataFrame with a standard CRS (WGS 84)
initial_gdf = gpd.GeoDataFrame(
    df,
    geometry=geometry,
    crs="EPSG:4326"
)

# Define output filenames
SHP_FILE = OUTPUT_DIR / 'european_cities.shp'
GEOJSON_FILE = OUTPUT_DIR / 'european_cities.geojson'

# Write the data out to disk
print("--- Preparing Files for Ingestion ---")
initial_gdf.to_file(SHP_FILE)
initial_gdf.to_file(GEOJSON_FILE, driver='GeoJSON')
print(f"Successfully created: {SHP_FILE.name} (and sidecar files) and {GEOJSON_FILE.name}")
print("-" * 45)


# --- 2. CORE TASK: Reading the GeoDataFrame ---

print("\n[A] Ingesting the Shapefile (.shp)")
# Use the core reading function, pointing only to the main .shp file
gdf_from_shp = gpd.read_file(SHP_FILE)

print("\n[B] Ingesting the GeoJSON (.geojson)")
# The exact same function is used for GeoJSON
gdf_from_json = gpd.read_file(GEOJSON_FILE)


# --- 3. VERIFICATION AND INSPECTION ---

print("\n--- Verification of Shapefile Read ---")
print(f"1. Object Type: {type(gdf_from_shp)}")
print(f"2. CRS Detected: {gdf_from_shp.crs.to_string()}")
print("3. Data Head (Shapefile):")
print(gdf_from_shp.head())

print("\n--- Verification of GeoJSON Read ---")
print(f"1. Object Type: {type(gdf_from_json)}")
print(f"2. CRS Detected: {gdf_from_json.crs.to_string()}")
print("3. Data Head (GeoJSON):")
print(gdf_from_json.head())

# The two reads agree on every value except one column name: the dBase table
# behind a Shapefile stores field names in 10 characters, so Population_M is
# truncated to Population. This is the sidecar trap in numbers.
print("\n--- Column Names After the Round Trip ---")
print(f"Shapefile: {list(gdf_from_shp.columns)}")
print(f"GeoJSON:   {list(gdf_from_json.columns)}")


# --- 4. CLEANUP (Ensuring a clean state after execution) ---
print("\n--- Cleanup ---")
# Shapefiles generate multiple files (e.g., .dbf, .shx, .prj, .cpg)
# We use glob to find all related files starting with the base name
base_name = os.path.splitext(SHP_FILE)[0]
files_to_remove = glob.glob(f'{base_name}.*')
files_to_remove.append(GEOJSON_FILE)

for f in files_to_remove:
    if os.path.exists(f):
        os.remove(f)
        # print(f"Removed: {f}") # Uncomment for detailed cleanup tracking

print("Cleanup successful. Temporary geospatial files removed from the directory.")
