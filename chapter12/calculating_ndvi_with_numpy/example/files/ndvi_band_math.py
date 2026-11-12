import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_origin

# --- 1. Define the Spectral Bands (Mock Reflectance Data) ---
# In real-world scenarios, these arrays would be loaded from a raster file (like GeoTIFF)
# using libraries such as rasterio. Here, we simulate a 3x3 pixel area.

# Red Band (R): Reflectance values (0.0 to 1.0).
# Healthy vegetation absorbs Red light, so these values are typically low.
red_band_data = np.array([
    [0.10, 0.15, 0.10], # Healthy vegetation pixel examples
    [0.25, 0.12, 0.35], # Mixed/stressed vegetation or bare soil
    [0.11, 0.14, 0.13]  # Healthy vegetation pixel examples
], dtype=np.float32)

# Near-Infrared Band (NIR): Reflectance values (0.0 to 1.0).
# Healthy vegetation strongly reflects NIR light, so these values are high.
nir_band_data = np.array([
    [0.55, 0.60, 0.50],
    [0.30, 0.65, 0.45],
    [0.52, 0.58, 0.53]
], dtype=np.float32)

# The output folder this listing writes into. It is resolved from the file's own
# position, so the script runs from any working directory.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "ndvi_basic.tif"

# The index is written as a one-band float32 raster: the same grid, the same cell
# size and the same CRS the two input bands would have had.
CELL_SIZE = 10.0                      # metres per pixel
NODATA_VALUE = -9999.0
PROFILE = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'nodata': NODATA_VALUE,
    'width': 3,
    'height': 3,
    'count': 1,                       # a single derived index, not a band stack
    'crs': 'EPSG:32610',              # UTM zone 10N: metres, so the cell size is true
    'transform': from_origin(500000.0, 4500000.0, CELL_SIZE, CELL_SIZE)
}


def calculate_ndvi(red_band, nir_band):
    """Return (ndvi, numerator, denominator) for two aligned reflectance bands."""
    # --- 2. Perform Band Math: The NDVI Calculation ---

    # Step A: Calculate the Numerator (NIR - Red)
    # The subtraction is performed element-wise across the entire array.
    numerator = nir_band - red_band

    # Step B: Calculate the Denominator (NIR + Red)
    # The addition is performed element-wise across the entire array.
    denominator = nir_band + red_band

    # Step C: Calculate the final NDVI map (Numerator / Denominator)
    # NumPy handles the division element-wise.
    # NOTE: We intentionally ignore the division-by-zero handling here for simplicity;
    # the robust method is covered in the Common Pitfall section.
    ndvi_map = numerator / denominator
    return ndvi_map, numerator, denominator


def write_index(ndvi_map, path):
    """Write one float32 band to `path`, creating the output folder first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(PROFILE)
    profile['width'] = ndvi_map.shape[1]
    profile['height'] = ndvi_map.shape[0]
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(ndvi_map.astype('float32'), 1)
    return path


def main():
    print("--- Input Data Summary ---")
    print(f"Shape of Arrays: {red_band_data.shape}")
    print("-" * 30)

    ndvi_map, numerator, denominator = calculate_ndvi(red_band_data, nir_band_data)

    # --- 3. Output and Interpretation ---

    print("--- Intermediate Results (Numerator) ---")
    print(numerator)
    print("-" * 30)

    print("--- Intermediate Results (Denominator) ---")
    print(denominator)
    print("-" * 30)

    print("--- Final NDVI Map (Normalized Difference Vegetation Index) ---")
    print(ndvi_map)

    # Interpretation: Values closer to +1.0 indicate very dense, healthy vegetation.
    # Values near 0.0 or negative indicate bare soil, water, or non-vegetated areas.
    print(f"\nMax NDVI recorded: {np.max(ndvi_map):.4f}")
    print(f"Min NDVI recorded: {np.min(ndvi_map):.4f}")

    # --- 4. The index as a georeferenced product ---
    write_index(ndvi_map, OUTPUT_FILE)
    print("\n--- GeoTIFF written ---")
    print(f"File: {OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
    print(f"Bands: {PROFILE['count']} | dtype: {PROFILE['dtype']} | "
          f"nodata: {PROFILE['nodata']}")
    print(f"CRS: {PROFILE['crs']} | cell size: {CELL_SIZE} m | "
          f"grid: {ndvi_map.shape[1]} x {ndvi_map.shape[0]} px")
    print(f"Transform (a, b, c, d, e, f): {tuple(PROFILE['transform'])[:6]}")


if __name__ == "__main__":
    main()
