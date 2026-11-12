"""Chapter 3, exercise 1 — the pipeline that clips a corridor out of farmland.

A 10 km gas pipeline runs west to east; three parcels sit along it in a metric
CRS (EPSG:32617, metres). The solution has to end at five numbers per parcel:
the overlap geometry, its area, the parcel's original area, and the percentage
of the parcel the corridor consumes.

The three parcels are chosen so the percentages are checkable by hand: one sits
entirely inside the 500 m corridor (100 %), one is cut in half lengthwise
(25 %), and one is 20 km away and must not appear at all.
"""
import geopandas as gpd
from shapely.geometry import LineString, Polygon

# --- Conceptual Setup (Assumes data is already in a metric CRS like UTM) ---
CRS_METRIC = "EPSG:32617"

# Mock data setup: a 10 km pipeline along y = 0
pipeline_gdf = gpd.GeoDataFrame({
    'pipe_id': [1],
    'geometry': [LineString([(0, 0), (10000, 0)])]
}, crs=CRS_METRIC)

# Parcel 101: 3 km x 1 km, centred on the pipeline -> wholly inside the corridor.
# Parcel 102: 1 km x 2 km, centred on the pipeline -> the corridor takes half its
#             height, so 1 km x 1 km of 4 km² = 25 %.
# Parcel 103: 100 m x 100 m, 20 km away -> no overlap at all.
parcels_data = {
    'parcel_id': [101, 102, 103],
    'crop_type': ['Wheat', 'Corn', 'Soy'],
    'total_area_sqm': [3000000.0, 4000000.0, 10000.0],
    'geometry': [
        Polygon([(0, -500), (0, 500), (3000, 500), (3000, -500)]),
        Polygon([(5000, -1000), (5000, 1000), (6000, 1000), (6000, -1000)]),
        Polygon([(20000, 20000), (20000, 20100), (20100, 20100), (20100, 20000)]),
    ]
}
parcels_gdf = gpd.GeoDataFrame(parcels_data, crs=CRS_METRIC)
# --- End Setup ---

# 1. Buffer Generation (500 meters)
impact_zone_geometry = pipeline_gdf.geometry.buffer(500).union_all()
impact_zone_gdf = gpd.GeoDataFrame(
    {'zone_id': [1]},
    geometry=[impact_zone_geometry],
    crs=CRS_METRIC
)
print(f"1. Corridor: {impact_zone_geometry.area:,.0f} m2 around a "
      f"{pipeline_gdf.geometry.length.iloc[0]:,.0f} m pipeline")

# Prepare original area data for later merging
original_areas = parcels_gdf[['parcel_id', 'total_area_sqm']].copy()

# 2. & 3. Identification of Affected Parcels and Calculate Overlap Area
affected_parcels_gdf = gpd.overlay(
    parcels_gdf,
    impact_zone_gdf,
    how='intersection'
)
print(f"3. Parcels clipped by the corridor: {sorted(affected_parcels_gdf['parcel_id'].tolist())}")

# Calculate the area of the resulting overlap geometries
affected_parcels_gdf['impacted_area_sqm'] = affected_parcels_gdf.geometry.area

# 4. & 5. Join original area and calculate impact percentage
# Merge the original total area back using parcel_id
final_impact_analysis_gdf = affected_parcels_gdf.merge(
    original_areas,
    on='parcel_id',
    suffixes=('_overlap', '_original')
)

# Calculate Impact Percentage
final_impact_analysis_gdf['impact_percent'] = (
    final_impact_analysis_gdf['impacted_area_sqm'] /
    final_impact_analysis_gdf['total_area_sqm_original']
) * 100

# The final report the task asks for.
print("\nFinal impact analysis:")
print(final_impact_analysis_gdf[
    ['parcel_id', 'crop_type', 'impacted_area_sqm',
     'total_area_sqm_original', 'impact_percent']
].to_string(index=False))

unaffected = sorted(set(parcels_gdf['parcel_id']) - set(final_impact_analysis_gdf['parcel_id']))
print(f"\nParcels untouched by the corridor: {unaffected}")
