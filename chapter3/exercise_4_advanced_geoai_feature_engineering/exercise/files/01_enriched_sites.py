"""Chapter 3, exercise 4 — three features, one enriched point layer.

Part A: a 100 m buffer around the sensitive area, joined back to mark which
extraction sites are near it. Part B: the concession each site falls inside.
Part C: the area of overlap between a 50 m buffer around each site and the
sensitive area.

The hard part is Part C: the overlay returns a frame indexed by site, so the
result is aggregated first and then merged back into the original frame — never
the other way round, which would lose sites with no overlap.

Readable results: site 1 sits inside Park A's buffer, inside concession C1, and
its 50 m buffer is wholly inside the park (pi * 50² = 7 853.98 m²). Site 3 is in
concession C2 and nowhere near the park.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

# --- Conceptual Setup (Assumes metric CRS) ---
CRS_METRIC = "EPSG:32617"

extraction_sites_gdf = gpd.GeoDataFrame({
    'site_id': [1, 2, 3, 4],
    'extraction_type': ['Legal', 'Illegal', 'Legal', 'Illegal'],
    'geometry': [Point(100, 100), Point(5000, 5000), Point(10000, 10000), Point(1000, 1000)]
}, crs=CRS_METRIC).set_index('site_id')

sensitive_areas_gdf = gpd.GeoDataFrame({
    'area_name': ['Park A'],
    'protection_level': ['High'],
    'geometry': [Polygon([(0, 0), (0, 200), (200, 200), (200, 0)])]  # Near Site 1
}, crs=CRS_METRIC)

concession_boundaries_gdf = gpd.GeoDataFrame({
    'concession_id': ['C1', 'C2'],
    'geometry': [
        Polygon([(50, 50), (50, 150), (150, 150), (150, 50)]),  # Contains Site 1
        Polygon([(9000, 9000), (9000, 11000), (11000, 11000), (11000, 9000)])  # Contains Site 3
    ]
}, crs=CRS_METRIC)
# --- End Setup ---

# Initialize the final GDF based on the original sites (using site_id as index)
enriched_sites_gdf = extraction_sites_gdf.copy()


# --- Feature 1: Binary Proximity Flag (100m Buffer + Join) ---
sensitive_buffer_100m = sensitive_areas_gdf.buffer(100)
sensitive_buffer_gdf = gpd.GeoDataFrame(geometry=sensitive_buffer_100m, crs=CRS_METRIC).assign(is_buffered=True)

# Spatially join sites to the buffer (left join to keep all sites)
proximity_join = gpd.sjoin(
    enriched_sites_gdf,
    sensitive_buffer_gdf,
    how='left',
    predicate='intersects'
)

# Aggregate the join result back to the original index (site_id) and convert to Boolean.
# Sites with no match hold NaN, and .eq(True) turns both NaN and False into False.
proximity_flag = proximity_join.groupby(
    enriched_sites_gdf.index
)['is_buffered'].first()
enriched_sites_gdf['is_near_sensitive_area'] = proximity_flag.eq(True)


# --- Feature 2: Concession ID Assignment (Join) ---
concession_join = gpd.sjoin(
    enriched_sites_gdf.drop(columns=['is_near_sensitive_area']),
    concession_boundaries_gdf[['concession_id', 'geometry']],
    how='left',
    predicate='within'
)

# Aggregate the join result and fill NaNs
concession_map = concession_join.groupby(
    enriched_sites_gdf.index
)['concession_id'].first().fillna('NONE')

enriched_sites_gdf['concession_id'] = concession_map


# --- Feature 3: Quantified Impact Area (Buffer + Intersection + Aggregation) ---
# 1. Create 50m buffer around each extraction site. Copying the frame keeps the
#    site_id index and swaps only the geometry column.
site_buffers_gdf = enriched_sites_gdf.copy()
site_buffers_gdf['geometry'] = site_buffers_gdf.geometry.buffer(50)
site_buffers_gdf = site_buffers_gdf[['geometry']]

# 2. Perform intersection overlay
impact_overlap_gdf = gpd.overlay(
    site_buffers_gdf.reset_index(),
    sensitive_areas_gdf,
    how='intersection'
)

# 3. Calculate overlap area
impact_overlap_gdf['overlap_sqm'] = impact_overlap_gdf.geometry.area

# 4. Aggregate maximum overlap area per site_id
max_overlap_summary = impact_overlap_gdf.groupby('site_id')['overlap_sqm'].max()

# 5. Merge results back and fill NaNs with 0.0
enriched_sites_gdf['max_sensitive_overlap_sqm'] = enriched_sites_gdf.index.map(
    max_overlap_summary
).fillna(0.0)

# Final cleanup: Reset index to restore original structure
enriched_sites_gdf = enriched_sites_gdf.reset_index()

print("Enriched extraction sites:")
print(enriched_sites_gdf[
    ['site_id', 'extraction_type', 'is_near_sensitive_area',
     'concession_id', 'max_sensitive_overlap_sqm']
].to_string(index=False))
print(f"\nSites near the sensitive area: "
      f"{int(enriched_sites_gdf['is_near_sensitive_area'].sum())} of {len(enriched_sites_gdf)}")
print(f"Sites inside a concession: "
      f"{int((enriched_sites_gdf['concession_id'] != 'NONE').sum())} of {len(enriched_sites_gdf)}")
print(f"Sites with any sensitive-area overlap: "
      f"{int((enriched_sites_gdf['max_sensitive_overlap_sqm'] > 0).sum())}")
