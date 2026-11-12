"""Chapter 3, exercise 5 — dissolve micro-zones into macro-regions.

The task: assign each micro-zone to the region it falls in, then dissolve that
join by region_id while summing population and averaging income. The dissolve is
where the geometry arithmetic happens: the boundaries between zones of the same
region disappear, and each output row carries the aggregated attributes.

Readable results: two zones per region, so R1 and R2 both come out as 5 000 m²,
though each pair meets only at a single corner and therefore dissolves into a
MultiPolygon of two squares rather than one part, with populations 1 500 and 3 000. Note what the mean of
average_income does — it averages zone averages, which is only the regional mean
if every zone holds the same population, and here R2's zones hold 2 000 and 1 000
people. R2's plain mean is 65 000 while its population-weighted mean is 56 666.67;
the listing prints both so the difference is visible.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

# --- Conceptual Setup (Assumes metric CRS) ---
CRS_METRIC = "EPSG:32617"

macro_regions_gdf = gpd.GeoDataFrame({
    'region_id': ['R1', 'R2'],
    'geometry': [
        Polygon([(0, 0), (0, 100), (100, 100), (100, 0)]),
        Polygon([(200, 200), (200, 300), (300, 300), (300, 200)])
    ]
}, crs=CRS_METRIC)

micro_zones_gdf = gpd.GeoDataFrame({
    'micro_zone_id': [1, 2, 3, 4],
    'total_population': [1000, 500, 2000, 1000],
    'average_income': [50000, 60000, 40000, 90000],
    'geometry': [
        Polygon([(0, 0), (0, 50), (50, 50), (50, 0)]),  # R1 part 1
        Polygon([(50, 50), (50, 100), (100, 100), (100, 50)]),  # R1 part 2
        Polygon([(200, 200), (200, 250), (250, 250), (250, 200)]),  # R2 part 1
        Polygon([(250, 250), (250, 300), (300, 300), (300, 250)])  # R2 part 2
    ]
}, crs=CRS_METRIC)
# --- End Setup ---

# 1. Initial Spatial Join: Assign region_id to micro-zones
joined_micro_zones = gpd.sjoin(
    micro_zones_gdf,
    macro_regions_gdf[['region_id', 'geometry']],
    how='left',
    predicate='intersects'
)

# 2. & 3. Dissolve and Attribute Aggregation
# Define the aggregation dictionary for the dissolve operation
agg_funcs = {
    'total_population': 'sum',
    'average_income': 'mean'
}

# Perform the dissolve (implicit union) based on 'region_id'
unified_regions_gdf = joined_micro_zones.dissolve(
    by='region_id',
    aggfunc=agg_funcs
).reset_index()

print("Micro-zones assigned to regions:")
print(joined_micro_zones[['micro_zone_id', 'region_id', 'total_population']].to_string(index=False))

print("\nUnified regions:")
print(unified_regions_gdf[['region_id', 'total_population', 'average_income']].to_string(index=False))
print(f"\nRegion areas (m2): {unified_regions_gdf.geometry.area.round(1).tolist()}")
print(f"Regions produced: {len(unified_regions_gdf)} from {len(micro_zones_gdf)} micro-zones")

# The mean of averages against the population-weighted mean, for R1 and R2.
joined_micro_zones['income_x_pop'] = joined_micro_zones['average_income'] * joined_micro_zones['total_population']
weighted = joined_micro_zones.groupby('region_id').apply(
    lambda g: g['income_x_pop'].sum() / g['total_population'].sum(), include_groups=False
)
print(f"Population-weighted mean income: {weighted.round(2).to_dict()}")
