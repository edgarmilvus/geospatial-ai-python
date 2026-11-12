"""Chapter 3, exercise 2 — burned hectares by ecosystem.

A 10 x 10 km fire perimeter meets three protected zones in a metric CRS. The
answer the task wants is one row per ecosystem with the burned area in
hectares: the intersection of the zone with the fire, converted at 10 000 m²
per hectare, grouped and summed.

The numbers are checkable: zone 201 is 3 x 3 km and entirely inside the fire
(900 ha), zone 202 contributes the 5 x 5 km of it that the fire reaches
(2 500 ha), and zone 203 is 20 km away and contributes nothing.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

# --- Conceptual Setup (Assumes data is in a metric CRS) ---
CRS_METRIC = "EPSG:32617"
HA_PER_SQM = 10000

# Mock data setup: a 10 km square fire, three protected zones
fire_perimeter_gdf = gpd.GeoDataFrame({
    'fire_name': ['BigBurn'],
    'geometry': [Polygon([(0, 0), (0, 10000), (10000, 10000), (10000, 0)])]
}, crs=CRS_METRIC)

protected_zones_gdf = gpd.GeoDataFrame({
    'zone_id': [201, 202, 203],
    'ecosystem_type': ['Old Growth Forest', 'Wetland Habitat', 'Shrubland'],
    'protection_level': ['High', 'Medium', 'Low'],
    'geometry': [
        Polygon([(1000, 1000), (1000, 4000), (4000, 4000), (4000, 1000)]),  # Fully burned (900 ha)
        Polygon([(5000, 5000), (5000, 12000), (12000, 12000), (12000, 5000)]),  # Partially burned (2 500 ha)
        Polygon([(20000, 20000), (20000, 20100), (20100, 20100), (20100, 20000)]),  # Not burned
    ]
}, crs=CRS_METRIC)
# --- End Setup ---

print(f"Fire perimeter: {fire_perimeter_gdf.geometry.area.iloc[0] / HA_PER_SQM:,.0f} ha")
print(f"Protected zones: {len(protected_zones_gdf)}")

# 1. Overlay Operation (Intersection)
# This results in geometries that represent the overlap (burned area)
burned_areas_gdf = gpd.overlay(
    protected_zones_gdf,
    fire_perimeter_gdf,
    how='intersection',
    keep_geom_type=True
)
print(f"Zones touched by the fire: {sorted(burned_areas_gdf['zone_id'].tolist())}")

# 2. Damage Calculation - Calculate burned area in hectares
burned_areas_gdf['burned_area_hectares'] = burned_areas_gdf.geometry.area / HA_PER_SQM

# 3. Summary Report - Group and Aggregate
ecosystem_damage_summary = burned_areas_gdf.groupby('ecosystem_type').agg(
    total_burned_hectares=('burned_area_hectares', 'sum')
).reset_index()

# Ensure the final result is a standard Pandas DataFrame
ecosystem_damage_summary = pd.DataFrame(ecosystem_damage_summary)

print("\nEcosystem damage summary:")
print(ecosystem_damage_summary.to_string(index=False))
print(f"\nTotal burned across protected zones: "
      f"{ecosystem_damage_summary['total_burned_hectares'].sum():,.1f} ha")
print(f"Zones left untouched: "
      f"{sorted(set(protected_zones_gdf['zone_id']) - set(burned_areas_gdf['zone_id']))}")
