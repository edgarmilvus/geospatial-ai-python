import geopandas as gpd
from shapely.geometry import Polygon

# 1. Initial Setup: Define a parcel near the North Pole (Greenland/Arctic)
# Coordinates are in meters, suitable for EPSG:3413 (Polar Stereographic)
# Example area: 10,000 m x 10,000 m = 100,000,000 sq meters (100 sq km)
polar_polygon = Polygon([
    (500000, 500000), 
    (510000, 500000), 
    (510000, 510000), 
    (500000, 510000)
])

# Create GeoDataFrame with the accurate polar CRS (EPSG:3413)
gdf_polar = gpd.GeoDataFrame({'id': [1], 'geometry': [polar_polygon]}, crs='EPSG:3413')

# Calculate the initial, accurate area (True Area)
true_area = gdf_polar.geometry.area.iloc[0]
print(f"1. True Area (in EPSG:3413 - meters): {true_area:,.2f} sq meters")

# 2. Simulated Incorrect Transformation: Transform to Web Mercator (EPSG:3857)
gdf_web_mercator = gdf_polar.to_crs(epsg=3857)

# 3. Distorted Area Calculation
distorted_area = gdf_web_mercator.geometry.area.iloc[0]
print(f"2. Distorted Area (in EPSG:3857 - meters): {distorted_area:,.2f} sq meters")

def calculate_area_distortion(true_area, distorted_area):
    """Calculates the absolute percentage difference in area."""
    # 4. Error Quantification Formula
    distortion = (abs(distorted_area - true_area) / true_area) * 100
    return distortion

# Calculate and print the distortion
percentage_distortion = calculate_area_distortion(true_area, distorted_area)

# 5. Output Analysis
print("\n--- Distortion Analysis ---")
print(f"Projection Mismatch: EPSG:3413 (Accurate Polar) vs. EPSG:3857 (Distorted Web Mercator)")
print(f"Absolute Area Distortion: {abs(distorted_area - true_area):,.2f} sq meters")
print(f"Percentage Distortion: {percentage_distortion:.2f}%")
