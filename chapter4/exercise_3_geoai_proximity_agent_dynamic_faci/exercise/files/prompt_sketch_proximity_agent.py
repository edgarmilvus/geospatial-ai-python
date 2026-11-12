import geopandas as gpd
from shapely.geometry import Point
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

# Your task is to create the GeoSeries, find the nearest POI, calculate the
# centroid of the segment connecting the two points, and determine the minimum required
# proximity radius (in meters).
