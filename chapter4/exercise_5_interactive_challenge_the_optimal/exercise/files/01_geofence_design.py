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

# 2. Building Buffer
building_fence = main_building.buffer(BUILDING_BUFFER_DISTANCE)

# 3. Point Buffers
point1_fence = utility_point_1.buffer(UTILITY_BUFFER_DISTANCE)
point2_fence = utility_point_2.buffer(UTILITY_BUFFER_DISTANCE)

# Collect all buffered geometries
all_fences = [building_fence, point1_fence, point2_fence]

# 4. Union Operation
# Combine all individual buffers into a single, unified Geo-Fence
unified_geo_fence = union_all(all_fences)

# 5. Perimeter and Area Calculation
fence_area = unified_geo_fence.area
fence_perimeter = unified_geo_fence.length

# Output
print("--- Optimal Geo-Fence Design Analysis ---")
print(f"Building Buffer Distance: {BUILDING_BUFFER_DISTANCE} m")
print(f"Utility Buffer Distance: {UTILITY_BUFFER_DISTANCE} m")
print(f"Resulting Geo-Fence Type: {unified_geo_fence.geom_type}")
print("-" * 40)
print(f"Total Monitored Area (sq meters): {fence_area:.2f}")
print(f"Total Geo-Fence Perimeter (meters): {fence_perimeter:.2f}")
