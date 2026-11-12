#!/usr/bin/env python3
# Chapter 14: Masking and Clipping - Extracting Region of Interest
# Subsection 2: Basic Code Example - Rasterio Masking

import numpy as np
import rasterio
from rasterio.mask import mask
from affine import Affine
import rasterio.io

# --- 1. CONFIGURATION AND SYNTHETIC RASTER SETUP ---

# Define the dimensions of our synthetic 10x10 pixel raster
RASTER_WIDTH, RASTER_HEIGHT = 10, 10
# Define the Coordinate Reference System (WGS 84, standard for global data)
RASTER_CRS = 'EPSG:4326'
# Define the NoData value, used to fill areas outside the mask
NODATA_VALUE = -9999

# Create an Affine transformation matrix (georeferencing information)
# Affine(a, b, c, d, e, f) maps pixel coordinates (col, row) to world coordinates (x, y)
# Here: 1.0 degree resolution, no rotation/skew, top-left corner at (0.0, 10.0)
RASTER_TRANSFORM = Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0)

# Create dummy data: a single band of sequential integer values (0 to 99)
# This allows us to easily verify which values were clipped
synthetic_data = np.arange(RASTER_WIDTH * RASTER_HEIGHT).reshape(RASTER_HEIGHT, RASTER_WIDTH).astype(rasterio.int16)

# Define the metadata dictionary required by rasterio
raster_meta = {
    'driver': 'GTiff',
    'dtype': rasterio.int16,
    'nodata': NODATA_VALUE,
    'width': RASTER_WIDTH,
    'height': RASTER_HEIGHT,
    'count': 1, # Number of bands
    'crs': RASTER_CRS,
    'transform': RASTER_TRANSFORM
}

# --- 2. DEFINING THE REGION OF INTEREST (ROI) GEOMETRY ---

# The mask function expects a list of GeoJSON-like feature dictionaries.
# We define a simple square polygon covering the area from X=3 to X=7 and Y=3 to Y=7.
# This corresponds to a 4x4 pixel area in our 10x10 synthetic raster.
roi_geometry = [
    {
        'type': 'Polygon',
        'coordinates': [[
            # Vertices must be defined in order and the loop must close
            (3.0, 3.0),
            (7.0, 3.0),
            (7.0, 7.0),
            (3.0, 7.0),
            (3.0, 3.0)
        ]]
    }
]

# --- 3. PERFORMING THE IN-MEMORY MASKING ---

# We use rasterio.io.MemoryFile to simulate opening a file from disk,
# allowing the code to be self-contained and run entirely in memory.
print("Starting clipping process...")
with rasterio.io.MemoryFile() as memfile:
    # Open the memory file using the defined metadata
    with memfile.open(**raster_meta) as src:
        # Write the synthetic data into the source dataset (band 1)
        src.write(synthetic_data, 1)

        # Execute the core masking operation
        clipped_data, clipped_transform = mask(
            dataset=src,        # The source raster dataset object
            shapes=roi_geometry, # The list of vector geometries (ROI)
            crop=True,          # CRITICAL: Crop the output array to the minimal bounding box of the ROI
            all_touched=False,  # Only include pixels whose center falls within the geometry
            nodata=NODATA_VALUE # Value used for areas outside the mask boundary
        )

# --- 4. OUTPUT AND VERIFICATION ---

print("\n--- Masking Results ---")
print(f"Original Data Shape (H, W): {synthetic_data.shape}")
print(f"Clipped Data Shape (Bands, H, W): {clipped_data.shape}")

# Calculate the expected top-left value:
# Our data runs 0-9, 10-19, 20-29, ..., 90-99.
# The ROI starts at X=3, Y=3. In array indices, this is row 7, col 3 (y is inverted in Affine).
# Let's inspect the actual content of the clipped array (Band 1)
print("\nContent of Clipped Data (Band 1):")
print(clipped_data[0])

# Verify the new georeferencing transform
print("\nNew Affine Transform (Top-Left Coordinates):")
print(clipped_transform)
