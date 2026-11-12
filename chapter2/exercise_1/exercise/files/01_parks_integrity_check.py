"""Chapter 2, exercise 1 — ingest a Shapefile and check what came back.

The task: read city_parks.shp, confirm the object is a GeoDataFrame, name its
active geometry column, report the CRS (or its absence), and preview five rows.

No file is provided, so the listing writes a realistic one first: three Berlin
parks in EPSG:25833 (ETRS89 / UTM zone 33N), where one unit is one metre, and
each park's geometry has exactly the area its attribute table claims.
"""
import pathlib

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

# One projected CRS for the whole exercise: metres, so area_sqm is checkable.
CRS_METRIC = "EPSG:25833"

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PARK_FILE = OUTPUT_DIR / "city_parks.shp"


def rectangle(x, y, width, height):
    """A park parcel as a closed rectangle, in metres."""
    return Polygon([(x, y), (x, y + height), (x + width, y + height),
                    (x + width, y), (x, y)])


# --- Setup: create city_parks.shp so the read below is a real file read ---
# Three parks on a grid north of Berlin: 40x25, 100x50 and 50x50 metres.
data = {
    'name': ['Park A', 'Park B', 'Park C'],
    'area_sqm': [1000, 5000, 2500],
}
parks_gdf_dummy = gpd.GeoDataFrame(
    pd.DataFrame(data),
    geometry=[
        rectangle(390000, 5820000, 40, 25),
        rectangle(390200, 5820000, 100, 50),
        rectangle(390500, 5820000, 50, 50),
    ],
    crs=CRS_METRIC,
)
parks_gdf_dummy.to_file(PARK_FILE, driver="ESRI Shapefile")


# 1. Load the Data
parks_gdf = gpd.read_file(PARK_FILE)

print(f"1. Data Loaded: {type(parks_gdf)}")

# 2. Verify Geometry and Identify Column Name
is_gdf = isinstance(parks_gdf, gpd.GeoDataFrame)
geom_col_name = parks_gdf.geometry.name

print(f"\n2. Is GeoDataFrame? {is_gdf}")
print(f"   Active Geometry Column: '{geom_col_name}'")

# 3. Inspect CRS
crs_info = parks_gdf.crs
print("\n3. Coordinate Reference System (CRS) Inspection:")
if crs_info:
    print(f"   CRS is defined.")
    if crs_info.to_epsg():
        print(f"   EPSG Code: {crs_info.to_epsg()}")
    else:
        print(f"   WKT String: {crs_info.to_wkt(pretty=True)[:100]}...")
else:
    print("   WARNING: CRS is missing or undefined.")

# 4. Attribute Preview
print("\n4. First Five Rows (Attribute and Geometry Preview):")
print(parks_gdf.head(5))

# The integrity check that matters after ingestion: does the attribute table
# agree with the geometry it travels with?
print("\n5. Geometry Area vs Attribute Area (integrity check):")
print(f"   geometry area (m2): {parks_gdf.geometry.area.round(1).tolist()}")
print(f"   attribute area_sqm: {parks_gdf['area_sqm'].tolist()}")
print(f"   agree: {bool((parks_gdf.geometry.area.round(1) == parks_gdf['area_sqm']).all())}")
