import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_origin

# --- Setup: an aspect array that crosses the 0/360 boundary ---
# North-west (300 degrees) turning through north (0/360) to north-east (60): the
# range a single hillside really covers, and the one a linear model reads as a jump
# of 358 degrees between two neighbouring cells.
SIZE = 50
CELL_SIZE = 10.0
aspect_degrees_array = (np.linspace(300.0, 420.0, SIZE * SIZE).reshape(SIZE, SIZE) % 360.0)

# Two other features, already standardized, for the stacking demonstration.
axis = np.arange(SIZE)[:, None] * np.ones((1, SIZE))
elevation_normalized = (axis - axis.mean()) / axis.std()
slope_normalized = np.ones((SIZE, SIZE)) * (axis - axis.mean()) / axis.std()

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "aspect_cyclical.tif"


def transform_cyclical_aspect(aspect_degrees_array):
    """
    Transforms cyclical aspect data into continuous Sine and Cosine components.
    """
    # 2. Degree to Radian Conversion
    aspect_radians = np.radians(aspect_degrees_array)

    # 3. Feature Transformation
    aspect_sine = np.sin(aspect_radians)
    aspect_cosine = np.cos(aspect_radians)

    return aspect_sine, aspect_cosine


# Execute transformation (Requirement 1, 2, 3)
aspect_sine, aspect_cosine = transform_cyclical_aspect(aspect_degrees_array)

# 4. Feature Replacement Demonstration
# Original Stack (conceptually): [Elevation, Slope, Aspect_degrees]
new_stack = np.stack([
    elevation_normalized,
    slope_normalized,
    aspect_sine,
    aspect_cosine
], axis=0)

print("--- Cyclical Aspect Transformation Summary ---")
print(f"Original Aspect Range (Degrees): {np.min(aspect_degrees_array):.1f} "
      f"to {np.max(aspect_degrees_array):.1f}  (0-360, wrapping at north)")
print(f"Aspect Sine Range: {np.min(aspect_sine):.4f} to {np.max(aspect_sine):.4f}")
print(f"Aspect Cosine Range: {np.min(aspect_cosine):.4f} to {np.max(aspect_cosine):.4f}")
print(f"\nNew Feature Stack Shape (Channels, H, W): {new_stack.shape}")
print("The feature count increased from 3 to 4, replacing one cyclical feature "
      "with two continuous features.")

# The point of the transformation: the two sides of north are close in the pair,
# and would be 358 apart on the raw degree scale.
north_west = 359.0
north_east = 1.0
sin_w, cos_w = (float(v[0]) for v in transform_cyclical_aspect(np.array([north_west])))
sin_e, cos_e = (float(v[0]) for v in transform_cyclical_aspect(np.array([north_east])))
pair_distance = float(np.hypot(sin_w - sin_e, cos_w - cos_e))
print(f"\nDistance between {north_west:.0f}° and {north_east:.0f}°:")
print(f"  as degrees: {abs(north_west - north_east):.0f}")
print(f"  as (sin, cos) pairs: {pair_distance:.4f}")
print(f"Unit circle preserved: "
      f"{bool(np.allclose(aspect_sine**2 + aspect_cosine**2, 1.0))}")

# The two new channels are a product like any other: write them as a two-band raster.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
profile = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'nodata': -9999.0,
    'width': SIZE,
    'height': SIZE,
    'count': 2,
    'crs': 'EPSG:32610',
    'transform': from_origin(500000.0, 4500000.0, CELL_SIZE, CELL_SIZE),
}
with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
    dst.write(aspect_sine.astype('float32'), 1)
    dst.write(aspect_cosine.astype('float32'), 2)
print(f"\nWrote aspect sine/cosine to: "
      f"{OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
