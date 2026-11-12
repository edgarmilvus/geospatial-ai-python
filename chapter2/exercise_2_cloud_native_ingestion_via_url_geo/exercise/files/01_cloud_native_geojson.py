"""Chapter 2, exercise 2 — the cloud-native read, without the cloud.

The task: load a wildfire-perimeter GeoJSON feed straight from its URL and
report its shape and CRS. A sandbox has no network, so the listing keeps the
call and moves the source: it writes the feed to output/ and reads that file
with the very same gpd.read_file(). A URL is one string away — the driver does
the HTTP work itself, no requests, no manual download.
"""
import pathlib

import geopandas as gpd
from shapely.geometry import Polygon

# The feed a production pipeline would point at. Not fetched here: see below.
REMOTE_SOURCE = "https://example.org/feeds/wildfire_perimeters.geojson"

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_SOURCE = OUTPUT_DIR / "wildfire_perimeters.geojson"


def read_any_source(source):
    """One call for a local path, a URL, or an archive: gpd.read_file."""
    return gpd.read_file(source)


# --- Setup: the hourly feed, as the mapping service would publish it ---
# Two fire perimeters with a reported intensity, in WGS 84 lon/lat.
feed = gpd.GeoDataFrame(
    {
        'id': [1, 2],
        'intensity': [5.5, 7.1],
    },
    geometry=[
        Polygon([(10.0, 20.0), (10.0, 20.4), (10.3, 20.4), (10.3, 20.0)]),
        Polygon([(30.0, 40.0), (30.0, 40.2), (30.2, 40.2), (30.2, 40.0)]),
    ],
    crs='EPSG:4326',
)
feed.to_file(LOCAL_SOURCE, driver='GeoJSON')


# 1. Define the Source
wildfire_url = REMOTE_SOURCE
print(f"1. Source configured: {wildfire_url}")
print(f"   Offline run reads the same feed from: {LOCAL_SOURCE.name}")

# 2. Remote Read — the same function, one argument
# In a connected environment this line is: gpd.read_file(wildfire_url)
fire_perimeters_gdf = read_any_source(LOCAL_SOURCE)

# 3. Data Type Confirmation (Shape)
data_shape = fire_perimeters_gdf.shape
print(f"\n3. GeoDataFrame Shape (Rows, Columns): {data_shape}")

# 4. CRS Check
crs_result = fire_perimeters_gdf.crs
print("\n4. CRS Check:")
print(f"   CRS: {crs_result}")
if crs_result and crs_result.to_epsg() == 4326:
    print("   Confirmed: CRS is WGS 84 (EPSG:4326), standard for GeoJSON.")

# 5. What the payload actually carries
print("\n5. Feed Contents:")
print(fire_perimeters_gdf[['id', 'intensity']].to_string(index=False))
