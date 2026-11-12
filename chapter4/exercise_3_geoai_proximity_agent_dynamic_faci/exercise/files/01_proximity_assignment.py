import geopandas as gpd
from shapely.geometry import Point, LineString
from pyproj import CRS

# Define the CRS (UTM Zone 10N for meter-based calculation)
TARGET_CRS = CRS.from_epsg(26910)

# Incident location (example in meters, assuming projection)
incident_x, incident_y = 500000, 4500000
incident = Point(incident_x, incident_y)

# Existing POIs (X, Y in meters)
poi_data = [
    (500100, 4500100),
    (500500, 4499000),
    (499500, 4500050),
    (501000, 4501000),
    (498000, 4490000)
]

# 1. Data Setup
poi_points = [Point(x, y) for x, y in poi_data]
poi_gs = gpd.GeoSeries(poi_points, crs=TARGET_CRS)

# 2. Proximity Search (Vectorized distance calculation)
distances = poi_gs.distance(incident)
min_distance = distances.min()
closest_poi_index = distances.idxmin()
closest_poi = poi_gs.iloc[closest_poi_index]

# 3. Centroid Calculation (of the pair)
# Create a line segment between the incident and the closest POI
connecting_line = LineString([incident, closest_poi])
center_of_zone = connecting_line.centroid
center_x, center_y = center_of_zone.coords[0]

# 4. Minimum Bounding Radius Determination
# The distance is the diameter, so the radius is half the distance.
critical_radius = min_distance / 2

# 5. Output
print("--- GeoAI Proximity Assignment Analysis ---")
print(f"Incident Location (X, Y): ({incident_x}, {incident_y})")
print(f"Closest POI Found (Index {closest_poi_index}): ({closest_poi.x:.0f}, {closest_poi.y:.0f}) m")
print(f"Distance to Closest POI: {min_distance:.2f} meters")
print("-" * 40)
print(f"Center of Critical Proximity Zone (Centroid): ({center_x:.2f}, {center_y:.2f}) m")
print(f"Minimum Required Proximity Radius: {critical_radius:.2f} meters")
