"""Chapter 2, exercise 5 — read a layer with no CRS and repair it.

The task: read boundary_points.geojson, show that its CRS is undefined, assign
WGS 84 with set_crs(), and confirm the frame is usable afterwards.

One honest note this listing makes in code: the GeoJSON driver fills in
EPSG:4326 on read, because RFC 7946 fixes GeoJSON to WGS 84. A file that really
loses its CRS is a Shapefile without its .prj sidecar, so the missing state is
reproduced here explicitly and then repaired — which is exactly the situation a
CSV of coordinates or a stripped Shapefile puts you in.
"""
import pathlib

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
POINTS_FILE = OUTPUT_DIR / "boundary_points.geojson"

# --- Setup: the boundary points, as a downstream tool would hand them over ---
data = {
    'id': [1, 2, 3],
    'lat': [34.05, 34.10, 34.15],
    'lon': [-118.25, -118.30, -118.35]
}
survey_gdf = gpd.GeoDataFrame(
    pd.DataFrame(data),
    geometry=gpd.points_from_xy(data['lon'], data['lat']),
    crs='EPSG:4326',
)
survey_gdf.to_file(POINTS_FILE, driver='GeoJSON')

# 1. Initial Load
raw_points_gdf = gpd.read_file(POINTS_FILE)
print(f"1. Loaded {len(raw_points_gdf)} points from {POINTS_FILE.name}")
print(f"   CRS as the driver reports it: {raw_points_gdf.crs.to_string()}")

# A GeoJSON read cannot come back empty-handed; this line reproduces the failure
# state of a layer whose CRS metadata was lost (a Shapefile without its .prj).
raw_points_gdf.crs = None

# 2. CRS Diagnostic
print(f"\n2. Initial CRS: {raw_points_gdf.crs}")
if raw_points_gdf.crs is None:
    print("   Diagnostic: CRS is undefined. Manual assignment is required.")

# 3. CRS Assignment
# Assigning WGS 84 (EPSG:4326) using the dedicated set_crs method. It states
# "these coordinates are in this system"; to_crs() would instead reproject them.
print("\n3. Assigning CRS: EPSG:4326...")
raw_points_gdf.set_crs('EPSG:4326', inplace=True)

# 4. Final Verification
print(f"4. Final Assigned CRS: {raw_points_gdf.crs}")
if raw_points_gdf.crs is not None:
    print("   Verification: CRS successfully assigned and data is ready.")

# 5. Proof that the assignment unlocks the next step: reprojection to metres.
projected = raw_points_gdf.to_crs('EPSG:3857')
print("\n5. After assignment, reprojection works:")
print(f"   lon/lat: {raw_points_gdf.geometry.iloc[0].x:.5f}, "
      f"{raw_points_gdf.geometry.iloc[0].y:.5f}")
print(f"   web mercator x/y (m): {projected.geometry.iloc[0].x:.2f}, "
      f"{projected.geometry.iloc[0].y:.2f}")
