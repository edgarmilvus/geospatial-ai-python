# Required structure for Exercise 4.
# A sketch, not a program: the function is the interface to fill in.
import geopandas as gpd
from shapely.geometry import shape
import rasterio
from rasterio.features import shapes


def raster_to_vector(binary_mask_path: str, output_gpkg_path: str):
    """
    Converts a georeferenced binary raster mask into a GeoDataFrame
    with calculated building attributes.
    """
    with rasterio.open(binary_mask_path) as src:
        image = src.read(1)
        transform = src.transform
        crs = src.crs

        # 1. Use rasterio.features.shapes to generate geometry/value pairs.

        features = []
        for geom, val in shapes(image, transform=transform):
            if val == 1:  # Only process building pixels
                polygon = shape(geom)

                # 2. Calculate Area (polygon.area) and Centroid (polygon.centroid).
                # 3. Append dictionary of attributes and geometry to 'features'.
                pass

        # 4. Create and return the GeoDataFrame.
        pass
