import pyproj
import math
import numpy as np

# 1. Input Coordinates (Lon, Lat) near San Francisco
roi_wgs84 = np.array([
    (-122.41, 37.77),  # Top Left (Lon, Lat)
    (-122.40, 37.77),  # Top Right
    (-122.40, 37.76),  # Bottom Right
    (-122.41, 37.76)   # Bottom Left
])

def get_utm_epsg(lon, lat):
    """Calculates the WGS 84 UTM EPSG code for a given location."""
    # Determine UTM Zone Number (2. UTM Zone Determination)
    zone_number = math.floor((lon + 180) / 6) + 1
    # Determine North (326xx) or South (327xx)
    if lat >= 0:
        return int(f"326{zone_number:02d}")
    else:
        return int(f"327{zone_number:02d}")

def transform_roi_to_utm(roi_points):
    """Transforms WGS 84 points to the local UTM projection using pyproj."""
    
    # Determine the target EPSG code (UTM Zone 10N = 32610 for San Francisco)
    lon_ref, lat_ref = roi_points[0]
    target_epsg = get_utm_epsg(lon_ref, lat_ref)
    
    # 3. Point Transformation: Create the optimized pyproj Transformer
    transformer = pyproj.Transformer.from_crs(
        crs_from=4326, 
        crs_to=target_epsg, 
        always_xy=True # Ensures input is (longitude, latitude)
    )
    
    # Separate coordinates for efficient bulk transformation
    lons = roi_points[:, 0]
    lats = roi_points[:, 1]
    
    # Perform transformation: returns (Easting, Northing) in meters
    easting, northing = transformer.transform(lons, lats)
    
    # Combine and round to three decimal places (required precision)
    transformed_points = np.column_stack((easting, northing)).round(3).tolist()
    
    # 4. Output Format
    output_dict = {
        "target_epsg": target_epsg,
        "transformed_coordinates": transformed_points
    }
    return output_dict

# Execute the transformation
utm_data = transform_roi_to_utm(roi_wgs84)

print(f"Target UTM EPSG: {utm_data['target_epsg']}")
print("Transformed Coordinates (Easting, Northing in meters):")
for i, (E, N) in enumerate(utm_data['transformed_coordinates']):
    print(f"  Point {i+1}: ({E}, {N})")

# 5. Verification Check: Calculate distance between Point 1 (TL) and Point 2 (TR)
tl_easting, tl_northing = utm_data['transformed_coordinates'][0]
tr_easting, tr_northing = utm_data['transformed_coordinates'][1]

dx = tr_easting - tl_easting
dy = tr_northing - tl_northing
distance_meters = math.hypot(dx, dy)

print(f"\nVerification: Distance between Top Left and Top Right points:")
print(f"  Calculated Distance: {distance_meters:.3f} meters")
