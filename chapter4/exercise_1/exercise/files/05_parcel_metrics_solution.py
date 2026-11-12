import shapely.geometry as sg
from shapely.geometry import Polygon

# Placeholder for the custom exception class
class InvalidGeoFeatureError(Exception):
    """Custom exception raised for invalid Shapely geometries."""
    pass

# Starter points for the land parcel (Example: a complex shape)
parcel_coords = [
    (10, 20),
    (35, 5),
    (50, 30),
    (40, 60),
    (20, 50),
    (10, 20) # Closing the loop
]

# 1. Feature Construction
try:
    land_parcel = Polygon(parcel_coords)

    # 2. Validation and Error Handling
    if not land_parcel.is_valid:
        # Note: For this specific input, the geometry is valid, but we include the check
        raise InvalidGeoFeatureError(
            f"Geometry is invalid. Error type: {land_parcel.geom_type}."
        )

    # 3. Metric Calculation
    parcel_area = land_parcel.area
    parcel_perimeter = land_parcel.length
    
    # Extracting centroid coordinates
    centroid_x, centroid_y = land_parcel.centroid.coords[0]

    # 4. Output Formatting
    print("--- Urban Planning Feature Analysis ---")
    print("Feature Validation: SUCCESS (Geometry is valid)")
    print(f"Total Parcel Area (sq units): {parcel_area:.2f}")
    print(f"Parcel Perimeter (units): {parcel_perimeter:.2f}")
    print(f"Geometric Centroid (X, Y): ({centroid_x:.4f}, {centroid_y:.4f})")

except InvalidGeoFeatureError as e:
    print(f"FATAL ERROR: Cannot process feature due to invalid geometry: {e}")
