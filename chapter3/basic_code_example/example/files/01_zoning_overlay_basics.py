"""Chapter 3, example 1 — intersection, union, buffer, spatial join.

Two zoning layers: a Development Zone (0,0)-(10,8) and a Natural Reserve
(5,4)-(15,12). The listing walks the four operations the chapter introduces and
prints the number each one should produce, so the geometry can be checked by
hand: the overlap is 5 x 4 = 20 square units, and the union of the two 80-unit
rectangles is 140.

The plane here is unitless on purpose — the point is topology, not geodesy. The
advanced script does the same work in metres.
"""
import warnings

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

# The plane is unitless on purpose (see the module docstring): the numbers below
# are topology, not metres, so geopandas' geographic-area warning is not a bug here.
warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')

# --- SETUP: Defining Geometries and GeoDataFrames ---

# 1. Define input geometries using simple coordinates
# Zone A (Development): A rectangle covering coordinates (0,0) to (10,8)
coords_a = [(0, 0), (10, 0), (10, 8), (0, 8), (0, 0)]
poly_a = Polygon(coords_a)

# Zone B (Reserve): An overlapping rectangle covering (5,4) to (15,12)
coords_b = [(5, 4), (15, 4), (15, 12), (5, 12), (5, 4)]
poly_b = Polygon(coords_b)

# 2. Create GeoDataFrames (GDFs)
# GDF 1: Development Plan Attributes
data_a = {'Name': ['Development Zone'], 'Max_Height': [50], 'geometry': [poly_a]}
# CRITICAL: Spatial operations require a defined Coordinate Reference System (CRS) for accuracy.
gdf_development = gpd.GeoDataFrame(pd.DataFrame(data_a), geometry='geometry', crs="EPSG:4326")

# GDF 2: Protected Areas Attributes
data_b = {'Name': ['Natural Reserve'], 'Status': ['Protected'], 'geometry': [poly_b]}
gdf_reserve = gpd.GeoDataFrame(pd.DataFrame(data_b), geometry='geometry', crs="EPSG:4326")

print("--- Input GeoDataFrames ---")
print("Development GDF:\n", gdf_development[['Name', 'Max_Height']].to_string(index=False))
print("\nReserve GDF:\n", gdf_reserve[['Name', 'Status']].to_string(index=False))

# --- PART A: GEOMETRIC OVERLAY OPERATIONS (Creating new geometries) ---

# 3. Spatial Intersection (Finding the conflict area)
# gpd.overlay combines two GDFs based on geometric interaction.
# how='intersection' returns only the overlapping area.
gdf_conflict = gpd.overlay(
    gdf_development,
    gdf_reserve,
    how='intersection',
    # make_valid repairs any self-intersecting input before the overlay runs
    make_valid=True
)
print("\n--- 1. Spatial Intersection (Conflict Area) ---")
# The resulting geometry is the overlap of the two input polygons (5,4) to (10,8), area = 5*4 = 20
print(f"Area of Intersection (sq units): {gdf_conflict.geometry.area.iloc[0]:.2f}")
# Attributes from both sides arrive side by side: Name_1 is the left (development)
# frame, Name_2 the right (reserve) one.
print(gdf_conflict[['Name_1', 'Name_2', 'Max_Height', 'Status']].to_string(index=False))

# 4. Spatial Union (Combining all parts)
# how='union' returns the full extent of both, splitting geometries where they overlap.
gdf_union = gpd.overlay(
    gdf_development,
    gdf_reserve,
    how='union',
    make_valid=True
)
print("\n--- 2. Spatial Union (Combined Footprint) ---")
# The union results in three features: A-B, A intersect B, and B-A.
print(f"Total Features after Union: {len(gdf_union)}")
print(f"Total Union Area: {gdf_union.geometry.area.sum():.2f}")

# 5. Spatial Buffer (Creating a protective perimeter)
# This is a method applied directly to the geometry column, not an overlay operation.
gdf_buffer = gdf_reserve.copy()
# The buffer method calculates a polygon at a specified distance around the existing geometry.
gdf_buffer['geometry'] = gdf_buffer.buffer(distance=1.0)
gdf_buffer['Name'] = 'Reserve Buffer'
print("\n--- 3. Spatial Buffer (1.0 unit perimeter) ---")
print(f"Original Reserve Area: {gdf_reserve.geometry.area.iloc[0]:.2f}")
print(f"Buffered Area: {gdf_buffer.geometry.area.iloc[0]:.2f}")

# --- PART B: SPATIAL JOIN OPERATION (Transferring attributes) ---

# 6. Spatial Join (Identifying overlap between Development and Buffer)
# gpd.sjoin transfers attributes based on a spatial relationship (predicate).
gdf_joined_check = gpd.sjoin(
    gdf_development,
    gdf_buffer,
    how='left',
    predicate='intersects'  # Join if the geometries touch or overlap
)

print("\n--- 4. Spatial Join (Development overlapping Buffer) ---")
print("Joined Attributes (Development + Buffer Status):")
# Clean up column names for display, using the suffixes automatically added by sjoin
gdf_joined_check = gdf_joined_check[['Name_left', 'Max_Height', 'Name_right']]
gdf_joined_check.columns = ['Development', 'Height', 'Buffer_Status']
print(gdf_joined_check.to_string(index=False))
