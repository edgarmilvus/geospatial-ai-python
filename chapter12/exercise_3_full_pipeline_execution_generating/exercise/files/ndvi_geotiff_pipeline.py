import rasterio
import numpy as np
from pathlib import Path
from rasterio.transform import from_bounds

# --- Setup: the four-band scene the pipeline reads ---
ROWS, COLS = 50, 50
RED_BAND_INDEX = 3
NIR_BAND_INDEX = 4
SEED = 3251                      # one seed: the same DN values on every machine

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
SCENE_FILE = OUTPUT_DIR / "scene_multiband.tif"
OUTPUT_FILE = OUTPUT_DIR / "ndvi_map.tif"
NODATA_VALUE = -9999.0

# The input profile carries the georeferencing the output must inherit: 1000 m
# across 50 cells is a 20 m cell, in UTM zone 17N where the unit is the metre.
INPUT_PROFILE = {
    'driver': 'GTiff', 'dtype': rasterio.uint16, 'count': 4,
    'width': COLS, 'height': ROWS, 'crs': 'EPSG:32617',
    'transform': from_bounds(300000, 4000000, 301000, 4001000, COLS, ROWS),
    'nodata': 0
}


def build_scene(path):
    """Write the four-band input the pipeline reads, with a patch of no signal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    red = rng.integers(1000, 2000, (ROWS, COLS), dtype=np.uint16)
    nir = rng.integers(4000, 6000, (ROWS, COLS), dtype=np.uint16)
    # Deep shadow: no signal in either band, so NIR + Red is zero there.
    red[10:14, 10:14] = 0
    nir[10:14, 10:14] = 0
    with rasterio.open(path, 'w', **INPUT_PROFILE) as dst:
        dst.write(rng.integers(500, 1500, (ROWS, COLS), dtype=np.uint16), 1)
        dst.write(rng.integers(800, 1800, (ROWS, COLS), dtype=np.uint16), 2)
        dst.write(red, RED_BAND_INDEX)
        dst.write(nir, NIR_BAND_INDEX)
    return path


build_scene(SCENE_FILE)

# --- Read the two bands and their profile ---
with rasterio.open(SCENE_FILE) as src:
    red_array = src.read(RED_BAND_INDEX).astype(np.float32)
    nir_array = src.read(NIR_BAND_INDEX).astype(np.float32)
    input_profile = src.profile.copy()

# 1. NDVI Calculation
diff_bands = nir_array - red_array
sum_bands = nir_array + red_array

# Calculate NDVI, then decide what to store where the sum is zero: the index of a
# pixel with no signal is not 0.0 (that is bare soil), it is nodata.
with np.errstate(divide='ignore', invalid='ignore'):
    ndvi_array = diff_bands / sum_bands
invalid = (sum_bands == 0) | ~np.isfinite(ndvi_array)
ndvi_array = np.where(invalid, NODATA_VALUE, np.clip(ndvi_array, -1.0, 1.0))
ndvi_array = ndvi_array.astype('float32')

# 2. Profile Modification
output_profile = input_profile.copy()
output_profile.update({
    'dtype': rasterio.float32,  # Output data type must be float
    'count': 1,                 # Output is a single band index map
    'nodata': NODATA_VALUE      # Define a clear nodata value for the output
})

print("--- Output Profile Changes ---")
print(f"New Dtype: {output_profile['dtype']}")
print(f"New Band Count: {output_profile['count']}")
print(f"New NoData Value: {output_profile['nodata']}")
print(f"CRS inherited: {output_profile['crs']}")
print(f"Transform inherited: {tuple(output_profile['transform'])[:6]}")

# 3. File Writing
try:
    with rasterio.open(OUTPUT_FILE, 'w', **output_profile) as dst:
        # Write the calculated NDVI array as the first band (index 1)
        # Ensure the array is float32 before writing
        dst.write(ndvi_array.astype(rasterio.float32), 1)

    print(f"\nSuccessfully wrote NDVI map to: "
          f"{OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")

except Exception as e:
    print(f"An error occurred during file writing: {e}")

# 4. What landed on disk
valid = ndvi_array != NODATA_VALUE
print("\n--- Index Summary ---")
print(f"Index pixels: {int(valid.sum())} of {ndvi_array.size} "
      f"({int(invalid.sum())} nodata)")
print(f"NDVI Min: {ndvi_array[valid].min():.4f}")
print(f"NDVI Max: {ndvi_array[valid].max():.4f}")
print(f"NDVI Mean: {ndvi_array[valid].mean():.4f}")
print(f"Nodata value in the array: {NODATA_VALUE}")
