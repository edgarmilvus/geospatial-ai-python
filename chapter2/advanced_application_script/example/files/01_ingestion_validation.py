"""Chapter 2, example 2 — an ingestion step that validates before it trusts.

The same read as example 1, arranged the way a pipeline needs it: write both
formats into a scratch folder, read each one back, count the features, and
compare the two coordinate reference systems before any spatial operation is
allowed to touch them. The historical districts are in EPSG:4326, the proposed
zones in EPSG:3857, so the check is meant to warn.

Everything is written under the project's output/ folder.
"""
import pathlib
import shutil

import geopandas as gpd
from shapely.geometry import Polygon

# --- 1. Setup: an isolated working folder ---

# A single folder, created per run and removed at the end, keeps the run
# reproducible and leaves the tree as it found it.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
WORK_DIR = OUTPUT_DIR / "ingest"
WORK_DIR.mkdir(parents=True, exist_ok=True)

SHP_FILE_PATH = WORK_DIR / "historical_districts.shp"
GEOJSON_FILE_PATH = WORK_DIR / "proposed_zones.geojson"

print(f"Working directory created at: output/{WORK_DIR.name}")

# --- 2. Synthetic Data Creation: Historical Districts (Shapefile) ---

# Define geometries for the Shapefile (using a standard CRS: EPSG:4326 WGS 84)
historical_geoms = [
    Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]),
    Polygon([(2, 2), (2, 3), (3, 3), (3, 2), (2, 2)])
]

# Create attribute data using a dictionary comprehension.
# Field names here stay within the Shapefile's ten-character DBF limit:
# "District_ID" would come back as "District_I" after a round trip.
historical_data = {
    'District': [101, 102],
    'Year_Est': [1950, 1985],
    'Status': ['Protected', 'Review']
}

# Construct the GeoDataFrame for the Shapefile
gdf_historical_out = gpd.GeoDataFrame(
    historical_data,
    geometry=historical_geoms,
    crs="EPSG:4326"
)

# Write the GeoDataFrame to a multi-file Shapefile format
# Shapefiles often require specific driver settings, though geopandas handles defaults well.
print(f"Writing Shapefile to: {SHP_FILE_PATH.name}")
gdf_historical_out.to_file(SHP_FILE_PATH, driver="ESRI Shapefile")


# --- 3. Synthetic Data Creation: Proposed Zones (GeoJSON) ---

# Define geometries for the GeoJSON (using a different, projected CRS: EPSG:3857 Web Mercator)
# One metre in EPSG:3857 is one unit, so a 1000 x 1000 square is 1 000 000 m².
proposed_geoms = [
    Polygon([(1000, 1000), (1000, 2000), (2000, 2000), (2000, 1000), (1000, 1000)]),
    Polygon([(5000, 5000), (5000, 6000), (6000, 6000), (6000, 5000), (5000, 5000)])
]

proposed_data = {
    'Zone_Name': ['A-1', 'B-2'],
    'Area_SqM': [1000000, 1000000]
}

# Construct the GeoDataFrame for the GeoJSON
gdf_proposed_out = gpd.GeoDataFrame(
    proposed_data,
    geometry=proposed_geoms,
    crs="EPSG:3857"
)

# Write the GeoDataFrame to the single-file GeoJSON format
print(f"Writing GeoJSON to: {GEOJSON_FILE_PATH.name}")
gdf_proposed_out.to_file(GEOJSON_FILE_PATH, driver="GeoJSON")


# --- 4. Data Ingestion and Validation Phase ---

print("\n--- Starting Ingestion Process ---")

# A. Ingesting the Shapefile
try:
    # Use gpd.read_file() to ingest the Shapefile. geopandas automatically locates
    # the associated auxiliary files (.dbf, .shx, .prj, etc.)
    gdf_historical_in = gpd.read_file(SHP_FILE_PATH)
    print(f"\nSuccessfully read Shapefile: {SHP_FILE_PATH.name}")
    print(f"  Feature Count: {len(gdf_historical_in)}")
    print(f"  CRS Detected: {gdf_historical_in.crs}")

except Exception as e:
    print(f"Error reading Shapefile: {e}")
    gdf_historical_in = None


# B. Ingesting the GeoJSON
try:
    # Use gpd.read_file() to ingest the GeoJSON. This uses the GeoJSON driver
    # which is optimized for single-file JSON parsing.
    gdf_proposed_in = gpd.read_file(GEOJSON_FILE_PATH)
    print(f"\nSuccessfully read GeoJSON: {GEOJSON_FILE_PATH.name}")
    print(f"  Feature Count: {len(gdf_proposed_in)}")
    print(f"  CRS Detected: {gdf_proposed_in.crs}")

except Exception as e:
    print(f"Error reading GeoJSON: {e}")
    gdf_proposed_in = None


# C. Final Validation Check: CRS Alignment
if gdf_historical_in is not None and gdf_proposed_in is not None:
    print("\n--- CRS Consistency Check ---")

    # Check if the CRSs are identical (they should not be, based on creation)
    if gdf_historical_in.crs != gdf_proposed_in.crs:
        print(f"WARNING: CRSs are mismatched.")
        print(f"  Historical CRS: {gdf_historical_in.crs.to_string()}")
        print(f"  Proposed CRS: {gdf_proposed_in.crs.to_string()}")
        print("  Reprojection is required before spatial operations (e.g., intersection).")
    else:
        print("CRSs are consistent. Data is ready for immediate spatial analysis.")

    # The areas are only comparable inside one CRS: degrees for the districts,
    # square metres for the zones.
    print(f"\nHistorical district areas (square degrees): "
          f"{gdf_historical_in.geometry.area.round(2).tolist()}")
    print(f"Proposed zone areas (square metres): "
          f"{gdf_proposed_in.geometry.area.tolist()}")

# --- 5. Cleanup ---

# Standard practice to remove temporary files and directories
try:
    shutil.rmtree(WORK_DIR)
    print(f"\nCleanup complete. Removed working directory: output/{WORK_DIR.name}")
except Exception as e:
    print(f"Error during cleanup: {e}")
