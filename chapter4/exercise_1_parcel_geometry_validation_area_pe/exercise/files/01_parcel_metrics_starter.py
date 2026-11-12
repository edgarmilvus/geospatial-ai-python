# Starter points for the land parcel (Example: a complex shape)
parcel_coords = [
    (10, 20),
    (35, 5),
    (50, 30),
    (40, 60),
    (20, 50),
    (10, 20) # Closing the loop
]

# Required libraries: shapely
import shapely.geometry as sg

# Placeholder for the custom exception class
class InvalidGeoFeatureError(Exception):
    """Custom exception raised for invalid Shapely geometries."""
    pass

# Your task is to implement the construction, validation, and calculation logic here,
# utilizing the methods available on the shapely.Polygon object.
