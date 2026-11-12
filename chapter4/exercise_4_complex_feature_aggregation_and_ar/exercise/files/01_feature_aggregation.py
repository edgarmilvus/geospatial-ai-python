from shapely.geometry import Polygon
from shapely import union_all

# 1. Define the individual patches
patch_1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]) # Area 100
patch_2 = Polygon([(5, 5), (15, 5), (15, 15), (5, 15)]) # Area 100, overlaps patch_1
patch_3 = Polygon([(200, 200), (210, 200), (210, 210), (200, 210)]) # Area 100, isolated

# Define the minimum required area
MIN_AREA_THRESHOLD = 150.0

patches = [patch_1, patch_2, patch_3]
original_patch_count = len(patches)

# 2. Aggregation (Union)
# The union of overlapping/close polygons and one isolated polygon results in a MultiPolygon
unified_feature = union_all(patches)

# The area of the union of patch 1 and 2 is 100 + 100 - (5*5 overlap) = 175
# Total Area = 175 (merged) + 100 (isolated) = 275

# 3. Area Thresholding
total_aggregated_area = unified_feature.area

print("--- Feature Aggregation and Filtering ---")
print(f"Total Area of Aggregated Feature: {total_aggregated_area:.2f} sq units")
print(f"Minimum Required Area Threshold: {MIN_AREA_THRESHOLD:.2f} sq units")
print("-" * 40)

# 4. Conditional Output
if total_aggregated_area >= MIN_AREA_THRESHOLD:
    print("STATUS: INCLUDED in Final Analysis Layer.")
    print(f"The aggregated feature meets the threshold.")
    print(f"Final Feature Type: {unified_feature.geom_type}")
else:
    print("STATUS: EXCLUDED from Final Analysis Layer.")
    print(f"The feature started as {original_patch_count} patches but the resulting total area ({total_aggregated_area:.2f}) is below the threshold.")
