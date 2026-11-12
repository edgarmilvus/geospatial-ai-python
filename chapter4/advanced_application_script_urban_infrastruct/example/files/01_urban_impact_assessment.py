import geopandas as gpd
from shapely.geometry import Polygon, Point
from pyproj import Geod
import pandas as pd
import warnings

# Suppress common UserWarning related to GeoDataFrame operations
warnings.filterwarnings("ignore", category=UserWarning)

# --- 1. Setup Data and CRS Definitions ---
# WGS84 (EPSG:4326) is the standard geographic (lat/lon) CRS for global data.
WGS84 = "EPSG:4326"
# EPSG:3857 (Web Mercator) is a common projected CRS, suitable for planar buffering/distance checks.
PLANAR_CRS = "EPSG:3857" 

# Define the Industrial Zone (IZ) geometry in WGS84 coordinates
iz_coords = [
    (-118.2, 34.0), (-118.15, 34.05), (-118.1, 34.0), (-118.15, 33.95), (-118.2, 34.0)
]
iz_geometry = [Polygon(iz_coords)]
industrial_zone_gdf = gpd.GeoDataFrame(
    {'name': ['Industrial Zone A'], 'geometry': iz_geometry},
    crs=WGS84
)

# Define Residential Zones (RZ) as point centroids in WGS84
res_data = {
    'name': ['Res Zone 1 (Near)', 'Res Zone 2 (Far)', 'Res Zone 3 (Critical)'],
    'latitude': [34.01, 33.8, 33.98],
    'longitude': [-118.18, -118.3, -118.15]
}
res_gdf = gpd.GeoDataFrame(
    res_data,
    geometry=gpd.points_from_xy(res_data['longitude'], res_data['latitude']),
    crs=WGS84
)

print("--- Initializing Geospatial Data Structures (WGS84) ---")

# --- 2. Geodesic Calculations (Area and Centroid) ---

# A. Calculate Centroid (WGS84)
iz_centroid_wgs84 = industrial_zone_gdf.geometry.centroid.iloc[0]
print(f"IZ Centroid (WGS84): Lat={iz_centroid_wgs84.y:.4f}, Lon={iz_centroid_wgs84.x:.4f}")

# B. Calculate Geodesic Area (True Area using WGS84 Ellipsoid)
# Instantiate the pyproj Geod object for highly accurate calculations
geod = Geod(ellps='WGS84')
iz_polygon = industrial_zone_gdf.geometry.iloc[0]

# pyproj.Geod calculates area (sq meters) and perimeter (meters) based on the ellipsoid
area_sq_m, perimeter_m = geod.geometry_area_perimeter(iz_polygon)
area_sq_km = abs(area_sq_m) / 1_000_000
print(f"IZ Calculated Geodesic Area: {area_sq_km:.2f} sq km")
print(f"IZ Perimeter (Geodesic): {perimeter_m:.2f} meters")

# --- 3. Planar Proximity Setup (CRS Transformation) ---

# CRITICAL STEP: Project data to a planar CRS for accurate, uniform distance/buffer operations
iz_planar = industrial_zone_gdf.to_crs(PLANAR_CRS)
res_planar = res_gdf.to_crs(PLANAR_CRS)

# Define the critical buffer distance (500 meters)
BUFFER_DISTANCE_M = 500

# Create the 500m buffer polygon around the Industrial Zone
proximity_buffer = iz_planar.geometry.buffer(BUFFER_DISTANCE_M).iloc[0]

# --- 4. Distance Measurement and Impact Assessment ---

impacted_zones = []
iz_boundary_planar = iz_planar.geometry.iloc[0].boundary # Boundary for planar distance check

# Iterate through residential zones using the projected data
for index, row in res_planar.iterrows():
    res_name = res_gdf.loc[index, 'name'] # Get name from original (easier lookup)
    res_point_planar = row['geometry']
    
    # Planar Check: Does the point fall within the 500m planar buffer?
    is_impacted = proximity_buffer.contains(res_point_planar)
    
    # Calculate shortest Planar Distance (boundary to centroid)
    planar_dist = iz_boundary_planar.distance(res_point_planar)
    
    # Calculate Geodesic Distance (Centroid to Centroid, using WGS84 for accuracy)
    res_point_wgs84 = res_gdf.geometry.iloc[index]
    
    # pyproj.Geod.inv calculates the forward azimuth, back azimuth, and distance (meters).
    # (Older texts call it `inverse`; pyproj has always spelled the method `inv`.)
    # Note: pyproj requires (lon, lat) order
    _, _, geodesic_dist_m = geod.inv(
        iz_centroid_wgs84.x, iz_centroid_wgs84.y, 
        res_point_wgs84.x, res_point_wgs84.y
    )
    
    status = "IMPACTED" if is_impacted else "SAFE"
    
    impacted_zones.append({
        'Zone': res_name,
        'Status': status,
        'Planar_Boundary_Distance_m': f"{planar_dist:.2f}",
        'Geodesic_Centroid_Distance_km': f"{geodesic_dist_m / 1000:.2f}"
    })

# --- 5. Final Reporting ---

print("\n--- Proximity Analysis Results (500m Planar Buffer) ---")
results_df = pd.DataFrame(impacted_zones)
print(results_df.to_string(index=False))

print("\n--- Summary of Geometric Calculations ---")
print("Note: Planar distance is used for local operations (buffering), while Geodesic distance is the true Earth distance.")
print(f"Zone 1 Status: {results_df.iloc[0]['Status']} (Planar Distance: {results_df.iloc[0]['Planar_Boundary_Distance_m']} m)")
