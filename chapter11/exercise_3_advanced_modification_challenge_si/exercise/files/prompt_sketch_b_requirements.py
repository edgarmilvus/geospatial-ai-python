# Required Imports
import rasterio
from rasterio.warp import calculate_default_transform, transform_bounds
# Assume IMAGE_PATH is defined

def downsample_and_retransform(image_path: str, factor: int = 4):
    """
    Reads the raster, downsamples it by a factor, and calculates the corresponding
    new affine transformation matrix.
    """
    # Your code here
    pass

# downsample_and_retransform(IMAGE_PATH)
