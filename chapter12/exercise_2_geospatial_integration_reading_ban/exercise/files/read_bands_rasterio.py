import rasterio
import numpy as np
from pathlib import Path
from rasterio.transform import from_bounds

# --- Setup: a four-band scene, so the exercise has a file to read ---
# The exercise describes a vendor GeoTIFF with at least four bands, where band 3 is
# Red and band 4 is NIR. Downloading one is not part of the lesson, so the listing
# writes a small four-band tile of its own and then reads it the way any other
# scene is read.
ROWS, COLS = 50, 50
SEED = 7117                      # one seed: the same DN values on every machine

# Define the expected band indices (1-based for rasterio)
RED_BAND_INDEX = 3
NIR_BAND_INDEX = 4

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
SCENE_FILE = OUTPUT_DIR / "image_001.tif"

SCENE_PROFILE = {
    'driver': 'GTiff',
    'dtype': rasterio.uint16,
    'count': 4,                  # 4 bands total
    'width': COLS,
    'height': ROWS,
    'crs': 'EPSG:4326',
    'transform': from_bounds(
        west=-10, south=40, east=-9, north=41, width=COLS, height=ROWS
    ),
    'nodata': 0
}


def build_scene(path):
    """Write a four-band tile: Blue, Green, Red, NIR, in that order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    with rasterio.open(path, 'w', **SCENE_PROFILE) as dst:
        # Bands 1 and 2 are written so the file really has four of them; only 3 and
        # 4 are read below.
        dst.write(rng.integers(500, 1500, (ROWS, COLS), dtype=np.uint16), 1)   # Blue
        dst.write(rng.integers(800, 1800, (ROWS, COLS), dtype=np.uint16), 2)   # Green
        dst.write(rng.integers(1000, 2000, (ROWS, COLS), dtype=np.uint16), 3)  # Red
        dst.write(rng.integers(4000, 6000, (ROWS, COLS), dtype=np.uint16), 4)  # NIR
    return path


build_scene(SCENE_FILE)

# 1. File Access and 2. Band Extraction
with rasterio.open(SCENE_FILE) as src:
    # Read the bands using their 1-based index and cast to float32 for math
    red_array = src.read(RED_BAND_INDEX).astype(np.float32)
    nir_array = src.read(NIR_BAND_INDEX).astype(np.float32)

    # Store the full profile
    profile = src.profile

# 3. Dimension Check
print("--- Array Dimensions Check ---")
print(f"Red Array Shape: {red_array.shape}")
print(f"NIR Array Shape: {nir_array.shape}")
print(f"Aligned for band math: {red_array.shape == nir_array.shape}")

# 4. Metadata Inspection
print("\n--- Geospatial Metadata Inspection ---")
print(f"Band Count: {profile['count']}")
print(f"Data Type: {profile['dtype']}")
print(f"Coordinate Reference System (CRS): {profile['crs']}")
print(f"Geospatial Transform Matrix (Affine):\n{profile['transform']}")

# The DN ranges are what a vendor file looks like: 16-bit integers, not reflectance.
print("\n--- Digital Number Ranges ---")
print(f"Red (band {RED_BAND_INDEX}): {red_array.min():.0f} to {red_array.max():.0f}")
print(f"NIR (band {NIR_BAND_INDEX}): {nir_array.min():.0f} to {nir_array.max():.0f}")
print(f"Scene kept at: {SCENE_FILE.relative_to(OUTPUT_DIR.parent)}")
