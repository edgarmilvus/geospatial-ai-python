import geopandas as gpd
from shapely.geometry import Polygon

# 2. Target CRS Selection: EPSG:5070 (NAD83 / Conus Albers)
TARGET_CRS = 5070 
# Justification: EPSG:5070 is an Equal Area projection optimized for the 
# contiguous United States. It minimizes area distortion across the continent, 
# making it ideal for accurate area calculations, unlike 4326 (angular) or 
# 3857 (high distortion).

# 1. Mock Data Creation (Central US coordinates)
# Polygon A (Web Mercator 3857) - coordinates in meters
poly_A = Polygon([
    (-10800000, 4500000), 
    (-10700000, 4500000), 
    (-10700000, 4400000), 
    (-10800000, 4400000)
])
gdf_A = gpd.GeoDataFrame({'id': [1], 'geometry': [poly_A]}, crs='EPSG:3857')

# Polygon B (WGS 84 4326) - coordinates in degrees
poly_B = Polygon([
    (-97.0, 38.0), 
    (-96.0, 38.0), 
    (-96.0, 37.0), 
    (-97.0, 37.0)
])
gdf_B = gpd.GeoDataFrame({'id': [2], 'geometry': [poly_B]}, crs='EPSG:4326')

def unify_crs(gdf_list, target_epsg):
    """Transforms a list of GeoDataFrames to a common target CRS."""
    unified_gdfs = []
    target_crs_str = f"EPSG:{target_epsg}"
    print(f"--- Unifying CRSs to {target_crs_str} ---")
    
    for i, gdf in enumerate(gdf_list):
        original_crs = gdf.crs.to_string()
        
        # 3. Transformation and Unification using GeoPandas to_crs()
        transformed_gdf = gdf.to_crs(target_epsg)
        
        print(f"DataFrame {i+1}: Transformed from {original_crs} to {transformed_gdf.crs.to_string()}")
        unified_gdfs.append(transformed_gdf)
        
    return unified_gdfs

# Execute unification
unified_A, unified_B = unify_crs([gdf_A, gdf_B], TARGET_CRS)

# 4. Verification: Check CRS identity and attempt a spatial operation
print("\n--- Verification ---")
crs_match = unified_A.crs == unified_B.crs
print(f"CRS Match Confirmed: {crs_match}")

if crs_match:
    try:
        # Attempt a spatial intersection 
        intersection = gpd.overlay(unified_A, unified_B, how='intersection')
        print(f"Spatial operation (Intersection) successful. Resulting features: {len(intersection)}")
    except Exception as e:
        print(f"Spatial operation failed despite CRS match: {e}")
