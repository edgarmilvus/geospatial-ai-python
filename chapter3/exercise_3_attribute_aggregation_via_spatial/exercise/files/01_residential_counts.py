"""Chapter 3, exercise 3 — residential buildings per neighborhood.

Two neighborhood polygons and ten building detections, one of them outside both.
The solution joins the points to the polygons (predicate='within'), filters to
Residential, and counts per neighborhood — a sjoin, a boolean filter and one
groupby, with no intermediate joins on the full attribute table.

Expected by hand: Central holds three detections, two of them Residential;
North holds six, five of them Residential; one detection lies 10 km outside.
"""
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd

# --- Conceptual Setup ---
CRS_METRIC = "EPSG:32617"

neighborhoods_gdf = gpd.GeoDataFrame({
    'hood_name': ['Central', 'North'],
    'geometry': [
        Polygon([(0, 0), (0, 1000), (1000, 1000), (1000, 0)]),
        Polygon([(1500, 1500), (1500, 2500), (2500, 2500), (2500, 1500)])
    ]
}, crs=CRS_METRIC)

building_detections_gdf = gpd.GeoDataFrame({
    'detection_id': range(10),
    'building_type': ['Residential', 'Commercial', 'Residential', 'Industrial',
                      'Residential', 'Residential', 'Commercial', 'Residential', 'Residential', 'Residential'],
    'geometry': [
        Point(100, 100), Point(500, 500), Point(900, 900),  # Central (2 Residential)
        Point(100, 10000),  # Outside both neighborhoods
        Point(1600, 1600), Point(1800, 1800), Point(2000, 2000),  # North (2 Residential)
        Point(2200, 2200), Point(2400, 2400), Point(2450, 2450)  # North (3 Residential)
    ]
}, crs=CRS_METRIC)
# --- End Setup ---

# 1. Execute the spatial join (sjoin)
# Use 'inner' join to only keep points that fall within a neighborhood.
# The predicate is read left to right: a *detection* is within a *neighborhood*.
# Joining the polygons on the left with 'within' asks whether a polygon is
# inside a point, which is never true, and returns zero rows.
joined_detections = gpd.sjoin(
    building_detections_gdf[['detection_id', 'building_type', 'geometry']],
    neighborhoods_gdf[['hood_name', 'geometry']],
    how='inner',
    predicate='within'
)

# 2. & 3. Filtering and Aggregation (Memory-Optimized)
# Immediately filter the joined DataFrame based on the attribute column
# and then aggregate using Pandas groupby().
residential_counts_df = joined_detections[
    joined_detections['building_type'] == 'Residential'
].groupby('hood_name').agg(
    residential_building_count=('detection_id', 'count')
).reset_index()

# Note: The resulting DataFrame is a standard Pandas DataFrame
print(f"Detections loaded: {len(building_detections_gdf)}")
print(f"Detections inside a neighborhood: {len(joined_detections)}")
print(f"Detections outside every neighborhood: "
      f"{len(building_detections_gdf) - len(joined_detections)}")

print("\nResidential buildings per neighborhood:")
print(residential_counts_df.to_string(index=False))
print(f"\nResidential detections counted: "
      f"{int(residential_counts_df['residential_building_count'].sum())} of "
      f"{int((building_detections_gdf['building_type'] == 'Residential').sum())} in the layer")
