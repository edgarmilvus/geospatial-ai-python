import sys
# Set recursion limit higher for complex geometric operations, though not strictly
# necessary for this basic example, it is good practice in GeoAI scripting.
sys.setrecursionlimit(2000)

# 1. Import necessary components from shapely
from shapely.geometry import Polygon, Point
from typing import List, Tuple

# Define the coordinates (vertices) of a simple, L-shaped land parcel
# The coordinates are defined in (X, Y) pairs, representing corners
# The order of definition matters: it defines the boundary path.
# We use a simple planar coordinate system (e.g., meters)
parcel_coords: List[Tuple[float, float]] = [
    (0.0, 0.0),    # Corner A (Start)
    (10.0, 0.0),   # Corner B (10 units East)
    (10.0, 5.0),   # Corner C (5 units North)
    (5.0, 5.0),    # Corner D (5 units West, creating the inner corner)
    (5.0, 10.0),   # Corner E (5 units North)
    (0.0, 10.0),   # Corner F (5 units West)
    (0.0, 0.0)     # Closing the loop (Back to A)
]

# 2. Create the Polygon object
# Shapely automatically constructs the geometric object from the list of vertices.
# The list must define the outer boundary (exterior ring).
land_parcel: Polygon = Polygon(parcel_coords)

# 3. Calculate fundamental geometric properties

# 3a. Area: The space enclosed by the boundary.
# The .area attribute returns the calculated area based on the coordinate system units squared.
calculated_area: float = land_parcel.area

# 3b. Perimeter (Length): The total length of the boundary line (fencing requirement).
# For Polygon objects, the .length attribute calculates the perimeter.
calculated_perimeter: float = land_parcel.length

# 3c. Centroid: The geometric center point, often used as a representative location.
# The .centroid attribute returns a new shapely Point object.
calculated_centroid: Point = land_parcel.centroid

# 4. Output the results
print("=" * 50)
print("--- Geospatial Feature Analysis: Irregular Parcel ---")
print("=" * 50)
print(f"1. Polygon Definition (WKT): {land_parcel.wkt}")
print("-" * 35)
print(f"2. Calculated Area (units²): {calculated_area:,.2f}")
print(f"3. Calculated Perimeter (units): {calculated_perimeter:,.2f}")
print(f"4. Centroid Coordinates (Shapely Point): {calculated_centroid.wkt}")
print(f"   - X Coordinate (Center Easting): {calculated_centroid.x:,.3f}")
print(f"   - Y Coordinate (Center Northing): {calculated_centroid.y:,.3f}")
print("=" * 50)
