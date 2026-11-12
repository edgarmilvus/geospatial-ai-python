import shapely.geometry as sg
from geopy.distance import distance, geodesic
import math

# Coordinates (Lat, Lon)
station_a = (78.22, 15.64) # Svalbard
station_b = (64.14, -21.94) # Reykjavik

# 1. Define Points (for planar calculation)
# Note: Shapely treats the first coordinate as X (Longitude) and the second as Y (Latitude)
# when calculating planar distance, which is standard for Euclidean geometry.
point_a_planar = sg.Point(station_a[1], station_a[0])
point_b_planar = sg.Point(station_b[1], station_b[0])

# 2. Planar Calculation (in degrees)
planar_distance_degrees = point_a_planar.distance(point_b_planar)

# --- Conversion for Error Quantification ---
# To compare distances, we must convert the planar distance (degrees) to kilometers.
# We use the approximation: 1 degree of latitude ~ 111.32 km.
# 1 degree of longitude ~ 111.32 km * cos(latitude).
# We use the average latitude for a rough conversion factor.
avg_lat_rad = math.radians((station_a[0] + station_b[0]) / 2)
degree_to_km_factor = 111.32 * math.cos(avg_lat_rad)
planar_distance_km_approx = planar_distance_degrees * degree_to_km_factor

# 3. Geodesic Calculation (in kilometers)
# Using geopy's geodesic function (WGS84 ellipsoid by default)
true_geodesic_distance_km = geodesic(station_a, station_b).km

# 4. Error Quantification
# Error = |Planar - Geodesic| / Geodesic * 100
error_percentage = (abs(planar_distance_km_approx - true_geodesic_distance_km) / 
                    true_geodesic_distance_km) * 100

print("--- Distance Analysis (High Latitude) ---")
print(f"Station A (Lat, Lon): {station_a}")
print(f"Station B (Lat, Lon): {station_b}")
print("-" * 40)
print(f"1. Planar Distance (Degrees): {planar_distance_degrees:.4f}°")
print(f"   (Approximate Planar Distance in KM using average latitude conversion: {planar_distance_km_approx:.2f} km)")
print(f"2. True Geodesic Distance (KM): {true_geodesic_distance_km:.2f} km")
print("-" * 40)
print(f"Percentage Error (Planar vs. Geodesic): {error_percentage:.2f}%")
