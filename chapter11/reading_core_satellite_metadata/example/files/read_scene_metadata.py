"""Basic example — write a small GeoTIFF, open it, read its three pillars.

The scene is 100 columns by 80 rows over a one-degree box, single band, uint16,
constant value 500. It is written under the project's `output/` folder, read back
through the same context manager the chapter teaches, and removed at the end of
the run so the run leaves the tree as it found it.
"""
import pathlib

import rasterio
import numpy as np
from rasterio.transform import from_bounds
from rasterio.crs import CRS

# --- 1. SETUP: Defining parameters and creating a temporary GeoTIFF ---

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# Define the file path for the temporary dataset
OUTPUT_FILENAME = "basic_rasterio_scene.tif"
WIDTH, HEIGHT = 100, 80  # Define dimensions (100 columns, 80 rows)
NUM_BANDS = 1

# Define the Coordinate Reference System (CRS) explicitly as WGS 84 (Lat/Lon)
# This is fundamental metadata linking pixel indices to Earth coordinates.
TARGET_CRS = CRS.from_epsg(4326)

# Define the Affine Transform using bounds. This matrix maps (row, col) to (x, y).
# We simulate a 100x80 scene covering 1 degree square (100 units wide, 80 units high)
# The resulting transform will define the resolution (e.g., 0.01 degree/pixel).
AFFINE_TRANSFORM = from_bounds(
    west=0.0, south=0.0, east=1.0, north=0.8,
    width=WIDTH, height=HEIGHT
)

# Define the profile (the metadata schema for the GeoTIFF header)
profile = {
    'driver': 'GTiff',      # Specify the file format driver
    'dtype': rasterio.uint16, # Specify the data type for pixel values
    'count': NUM_BANDS,      # Number of bands (e.g., 1 for grayscale)
    'height': HEIGHT,        # Number of rows
    'width': WIDTH,          # Number of columns
    'crs': TARGET_CRS,       # The Coordinate Reference System
    'transform': AFFINE_TRANSFORM, # The geometric transformation matrix
    'nodata': 0,             # Value representing missing data
}


def create_scene(path):
    """Write the dummy GeoTIFF and return its path."""
    with rasterio.open(path, 'w', **profile) as dst:
        # Create a simple NumPy array representing fake pixel data
        # We fill it with a constant value (500) within the allowed uint16 range
        dummy_data = np.full((HEIGHT, WIDTH), 500, dtype=rasterio.uint16)

        # Write the data to the dataset. The index '1' specifies the first band.
        dst.write(dummy_data, 1)
    return pathlib.Path(path)


def inspect_scene(path):
    """Open the scene with Rasterio and return its metadata and first band."""
    # Open the file in read mode ('r' is the default if not specified)
    # The 'src' variable is the DatasetReader object, the primary interface.
    with rasterio.open(path) as src:
        # A. Accessing Core Metadata Attributes
        print(f"File Name: {src.name}")
        print("-" * 30)
        print(f"1. Coordinate System (CRS):\n{src.crs.to_string()}")
        print("-" * 30)
        print(f"2. Affine Transform (Geo-T):")
        # Print the transform matrix, which links (row, col) to (x, y)
        print(src.transform)
        print("-" * 30)
        print(f"3. Dimensions & Structure:")
        print(f"   Width (Columns): {src.width}")
        print(f"   Height (Rows): {src.height}")
        print(f"   Number of Bands: {src.count}")
        print(f"   Pixel Data Type: {src.dtypes[0]}")

        # B. Reading Pixel Data
        # Read the entire first band (index 1) into a NumPy array
        # Note: Rasterio uses 1-based indexing for bands.
        print("\n4. Reading Band Data (Index 1)...")
        band_data = src.read(1)

        # C. Verification and Inspection
        print(f"   Data shape read (H, W): {band_data.shape}")
        print(f"   Data type read: {band_data.dtype}")
        print(f"   Minimum pixel value: {np.min(band_data)}")
        print(f"   Maximum pixel value: {np.max(band_data)}")

        metadata = {
            "crs": src.crs.to_string(),
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0],
            "transform": tuple(src.transform)[:6],
            "bounds": tuple(float(value) for value in src.bounds),
            "nodata": src.nodata,
        }
    return metadata, band_data


def main(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / OUTPUT_FILENAME

    print(f"--- 1. Creating dummy file: {path.name} ---")
    try:
        create_scene(path)
        print("Dummy GeoTIFF created successfully.")

        # --- 2. READING: Accessing metadata and pixel data ---
        print("\n--- 2. Reading metadata and data using Rasterio ---")
        metadata, band_data = inspect_scene(path)
        return metadata, band_data
    finally:
        # --- 3. CLEANUP ---
        if path.exists():
            path.unlink()
            print(f"\n--- 3. Cleanup: Removed {path.name} ---")


if __name__ == "__main__":
    main()
