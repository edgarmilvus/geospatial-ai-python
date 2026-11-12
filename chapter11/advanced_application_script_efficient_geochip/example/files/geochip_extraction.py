"""Advanced example — extract a centred GeoChip with a windowed read.

The synthetic scene is 1024 x 1024 x 4 in UTM zone 17N at 10 m resolution, written
under the project's `output/` folder with a fixed generator, so the chip and its
mean are the same on every run. The read asks Rasterio for three bands and one
256-pixel window; the window's own affine transform is what keeps the chip on the
map.
"""
import pathlib

import rasterio
from rasterio.windows import Window
import numpy as np

# --- Configuration and Setup ---

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DUMMY_FILENAME = OUTPUT_DIR / "large_satellite_scene.tif"

# Define the dimensions of the simulated large scene
SCENE_WIDTH = 1024
SCENE_HEIGHT = 1024
NUM_BANDS = 4  # Standard multi-spectral: Blue, Green, Red, Near-Infrared (NIR)

# Define the target chip size for extraction
CHIP_SIZE = 256
TARGET_BANDS = [3, 2, 1]  # Extracting Red, Green, Blue bands (assuming standard order 1-based indexing)


def create_dummy_geotiff(filepath: pathlib.Path):
    """
    Creates a large, synthetic GeoTIFF file for demonstration purposes.
    This simulates a multi-band satellite image (e.g., Sentinel-2).
    """
    if filepath.exists():
        print(f"Skipping creation: {filepath.name} already exists.")
        return filepath

    print(f"Creating dummy file: {filepath.name}...")

    # Define a simple affine transform (required for georeferencing)
    # Origin (0,0) is at (500000, 4500000) UTM coordinates, 10m resolution
    transform = rasterio.transform.from_origin(500000, 4500000, 10, 10)

    # Define the profile for the new GeoTIFF
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'count': NUM_BANDS,
        'height': SCENE_HEIGHT,
        'width': SCENE_WIDTH,
        'crs': 'EPSG:32617',  # Example UTM zone
        'transform': transform,
        'nodata': 0
    }

    # Generate synthetic data (band-dependent noise, fixed by the seed)
    with rasterio.open(filepath, 'w', **profile) as dst:
        for i in range(1, NUM_BANDS + 1):
            # Create a band with values centered around 1000 (common for 16-bit imagery)
            rng = np.random.default_rng(100 + i)
            data = rng.integers(500, 1500, (SCENE_HEIGHT, SCENE_WIDTH),
                                dtype=rasterio.uint16)
            dst.write(data, i)

    print(f"Dummy file created successfully at {filepath.name}.")
    return filepath


def extract_geo_chip(source_path: pathlib.Path, chip_size: int, bands: list):
    """
    Opens a raster file, inspects metadata, defines a central window,
    and efficiently reads only the specified bands and subset.
    """
    print("\n--- Starting GeoChip Extraction Process ---")

    try:
        # 1. Open the raster dataset using Rasterio's context manager
        with rasterio.open(source_path) as src:

            # 2. Inspect and report essential metadata
            print(f"Source Dimensions: W={src.width}, H={src.height}")
            print(f"Coordinate Reference System (CRS): {src.crs}")
            print(f"Affine Transform (Top-Left Corner, Resolution): {src.transform}")
            print(f"Number of Bands: {src.count}")
            print(f"Data Type: {src.dtypes[0]}")

            # 3. Calculate the center coordinates for the chip extraction
            center_x = src.width // 2
            center_y = src.height // 2

            # Calculate the top-left corner of the desired window
            window_start_col = center_x - (chip_size // 2)
            window_start_row = center_y - (chip_size // 2)

            # 4. Define the extraction window using rasterio.windows.Window
            # This object specifies the row/column coordinates to read
            extraction_window = Window(
                col_off=window_start_col,
                row_off=window_start_row,
                width=chip_size,
                height=chip_size
            )
            print(f"\nDefined Extraction Window: {extraction_window}")

            # 5. Calculate the georeferencing transform specific to this window
            # This is crucial for correctly locating the extracted chip on Earth
            window_transform = src.window_transform(extraction_window)

            # 6. Efficiently read only the specified bands and the windowed subset
            # The 'window' argument ensures only the required pixels are loaded from disk
            geo_chip = src.read(
                indexes=bands,
                window=extraction_window,
                boundless=False, # Do not read outside the dataset bounds
                out_dtype=src.dtypes[0] # Ensure output dtype matches source
            )

            # 7. Perform a basic validation check (simulating cloud/error detection)
            mean_value = np.mean(geo_chip)
            print(f"\nExtraction successful. Chip Shape: {geo_chip.shape}")
            print(f"Mean Pixel Value (Validation): {mean_value:.2f}")

            # 8. Return the data and its associated georeferencing information
            return {
                "data": geo_chip,
                "crs": src.crs,
                "transform": window_transform,
                "window": extraction_window,
                "source_transform": src.transform,
                "source_shape": (src.height, src.width),
            }

    except rasterio.RasterioIOError as e:
        print(f"Error reading file: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# --- Execution ---
if __name__ == "__main__":

    # 1. Ensure the dummy file exists
    create_dummy_geotiff(DUMMY_FILENAME)

    # 2. Run the extraction process
    result = extract_geo_chip(
        source_path=DUMMY_FILENAME,
        chip_size=CHIP_SIZE,
        bands=TARGET_BANDS
    )

    if result:
        chip_data = result["data"]
        chip_transform = result["transform"]

        # Verify the final output dimensions
        print("\n--- Final Output Verification ---")
        # Expected shape: (Number of Bands, Height, Width) -> (3, 256, 256)
        print(f"Final Chip Data Shape (Bands, H, W): {chip_data.shape}")

        # Verify the new transform for the chip
        print(f"Chip's Affine Transform: {chip_transform}")

        # Assertions for programmatic verification
        assert chip_data.shape == (len(TARGET_BANDS), CHIP_SIZE, CHIP_SIZE)
        print("Verification successful: Chip shape matches expected dimensions.")
