import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_origin

NODATA_VALUE = -9999.0
EPSILON = 1e-6          # a sum below this is treated as "no signal"
SIZE = 256              # the book uses 1000x1000; 256 keeps the example instant
SEED = 2024             # one seed: the same noisy scene on every machine

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "ndvi_robust.tif"

# Simulated noisy data
rng = np.random.default_rng(SEED)
nir_noisy = rng.integers(50, 800, size=(SIZE, SIZE)).astype(np.float32)
red_noisy = rng.integers(30, 700, size=(SIZE, SIZE)).astype(np.float32)

# Force areas where the sum is zero (simulating deep shadow/water)
nir_noisy[100:110, 100:110] = 0.0
red_noisy[100:110, 100:110] = 0.0

# 1. Denominator Calculation
diff_bands = nir_noisy - red_noisy
sum_bands = nir_noisy + red_noisy

print("--- Robust NDVI Calculation (np.where) ---")

# 2. Conditional Masking using np.where()
# Condition: Check if the sum is extremely close to zero (or less)
zero_sum_mask = (sum_bands <= EPSILON)

# If zero_sum_mask is TRUE, assign NODATA_VALUE
# If zero_sum_mask is FALSE, perform the standard division
with np.errstate(divide='ignore', invalid='ignore'):
    ndvi_robust = np.where(
        zero_sum_mask,
        NODATA_VALUE,
        diff_bands / sum_bands
    )

# 4. Verification (Checking the forced zero area)
print(f"NDVI value at forced zero sum area [105, 105]: {ndvi_robust[105, 105]:.1f}")
print(f"Pixels assigned NODATA: {int(zero_sum_mask.sum())}")
print(f"NaN values left in the map: {int(np.isnan(ndvi_robust).sum())}")
print(f"Inf values left in the map: {int(np.isinf(ndvi_robust).sum())}")

print("\n--- Alternative Method (Warning Suppression + nan_to_num) ---")

# 3. Warning Suppression (Alternative Method)
with np.errstate(divide='ignore', invalid='ignore'):
    ndvi_alternative = diff_bands / sum_bands

# Replace NaN (0/0) and Inf (X/0) with the NODATA_VALUE
ndvi_alternative = np.nan_to_num(
    ndvi_alternative,
    nan=NODATA_VALUE,
    posinf=NODATA_VALUE,
    neginf=NODATA_VALUE
)

# Verification
print(f"Alternative NDVI value at forced zero sum area [105, 105]: "
      f"{ndvi_alternative[105, 105]:.1f}")
print(f"Both methods agree pixel for pixel: "
      f"{bool(np.array_equal(ndvi_robust, ndvi_alternative))}")

# 5. The masked index as a product: a nodata marker the next stage can honour.
valid = ndvi_robust != NODATA_VALUE
print("\n--- Index Summary ---")
print(f"Valid pixels: {int(valid.sum())} of {ndvi_robust.size}")
print(f"NDVI Min: {ndvi_robust[valid].min():.4f}")
print(f"NDVI Max: {ndvi_robust[valid].max():.4f}")
print(f"NDVI Mean: {ndvi_robust[valid].mean():.4f}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
profile = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'nodata': NODATA_VALUE,
    'width': SIZE,
    'height': SIZE,
    'count': 1,
    'crs': 'EPSG:32610',
    'transform': from_origin(500000.0, 4500000.0, 10.0, 10.0),
}
with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
    dst.write(ndvi_robust.astype('float32'), 1)
print(f"\nWrote masked NDVI to: {OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
