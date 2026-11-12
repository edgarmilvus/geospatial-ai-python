"""Chapter 2, exercise 3 — read only the columns the model needs.

The task: from a road network with many attributes, load the geometry plus
segment_id and road_class, and nothing else. The lever is read_file(columns=...):
the filter runs inside the I/O layer (pyogrio/GDAL), so the dropped columns are
never converted into Python objects at all.

The listing writes a small global_roads.shp with the same shape of problem —
seven attribute columns where two are wanted — reads it both ways, and compares.
"""
import pathlib

import geopandas as gpd
from shapely.geometry import LineString

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ROADS_FILE = OUTPUT_DIR / "global_roads.shp"

# --- Setup: a road file with far more columns than the model needs ---
# Field names stay within 10 characters: the dBase table inside a Shapefile
# truncates anything longer, and this exercise is about bandwidth, not names.
all_cols = ['segment_id', 'road_class', 'length_km', 'surface',
            'admin_code', 'legacy', 'traffic']
dummy_data = {col: [f"{col}_val_{i}" for i in range(3)] for col in all_cols}
dummy_data['segment_id'] = [101, 102, 103]
dummy_data['road_class'] = ['Highway', 'Local', 'Highway']
dummy_data['geometry'] = [
    LineString([(0, 0), (1, 1)]),
    LineString([(1, 1), (2, 2)]),
    LineString([(2, 2), (3, 3)])
]
gpd.GeoDataFrame(dummy_data, geometry='geometry', crs='EPSG:4326') \
    .to_file(ROADS_FILE, driver="ESRI Shapefile")

# 1. Identify Required Columns
required_attributes = ['segment_id', 'road_class']

# 2. Optimized Read
# The key is using the 'columns' parameter in read_file
# Note: The geometry column ('geometry') is automatically included
# unless specifically excluded, but listing it explicitly is safe practice.
# We will rely on the default inclusion of geometry.
optimized_roads_gdf = gpd.read_file(ROADS_FILE, columns=required_attributes)

# For comparison only: the same file read whole.
full_roads_gdf = gpd.read_file(ROADS_FILE)

# 3. Verification
print("Columns loaded in optimized GeoDataFrame:")
print(optimized_roads_gdf.columns.tolist())
print(f"\nRows read: {len(optimized_roads_gdf)}")
print(f"Columns read: {len(optimized_roads_gdf.columns)} of {len(full_roads_gdf.columns)}")
print(f"Columns skipped: {sorted(set(full_roads_gdf.columns) - set(optimized_roads_gdf.columns))}")
print(f"Still a GeoDataFrame: {type(optimized_roads_gdf).__name__}, "
      f"geometry column '{optimized_roads_gdf.geometry.name}'")
print("\nThe two columns that were asked for:")
print(optimized_roads_gdf.to_string(index=False))

# 4. Memory Comparison (Conceptual)
# This method is superior to loading the entire dataset and then dropping
# unwanted columns because the filtering occurs during the I/O operation
# (handled by the underlying GDAL/Fiona driver). This means only the
# required data ever enters Python's memory space, drastically reducing
# both memory usage and the initial load time, which is crucial for
# massive datasets.
