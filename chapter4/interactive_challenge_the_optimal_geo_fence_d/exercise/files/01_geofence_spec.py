from shapely.geometry import Polygon, Point
from shapely import union_all

# 1. Define the features (simplified meter coordinates for a projected space)
main_building = Polygon([
    (100, 100), (300, 100), (350, 200),
    (300, 300), (100, 300), (50, 200)
])

utility_point_1 = Point(400, 150)
utility_point_2 = Point(50, 450)

# Buffer distances in meters
BUILDING_BUFFER_DISTANCE = 50.0
UTILITY_BUFFER_DISTANCE = 20.0

# Your task is to calculate the buffers, perform the unary union operation on the
# resulting geometries, and calculate the final area and perimeter of the resulting Geo-Fence.
