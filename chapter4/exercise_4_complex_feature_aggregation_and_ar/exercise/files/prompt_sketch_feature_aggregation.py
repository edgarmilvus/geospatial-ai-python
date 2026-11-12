from shapely.geometry import Polygon
from shapely import union_all

# 1. Define the individual patches
patch_1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]) # Area 100
patch_2 = Polygon([(5, 5), (15, 5), (15, 15), (5, 15)]) # Area 100, overlaps patch_1
patch_3 = Polygon([(200, 200), (210, 200), (210, 210), (200, 210)]) # Area 10, isolated

# Define the minimum required area
MIN_AREA_THRESHOLD = 150.0

# Your task is to perform the union, calculate the total area of the resulting MultiPolygon,
# and apply the area threshold filter logic.
