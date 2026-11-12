import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_origin

# --- Setup: Create simulated NDVI data (100x100 array) ---
# Generate data covering most of the NDVI range, then force two blocks so that the
# first and the last class are certainly represented.
np.random.seed(42)
final_ndvi_map = np.random.uniform(low=-0.2, high=0.8, size=(100, 100)).astype(np.float32)

# Force some extremes to ensure all classes are represented
final_ndvi_map[0:10, 0:10] = -0.5   # Class 0
final_ndvi_map[90:100, 90:100] = 0.7  # Class 3
# ---------------------------------------------------------

CLASS_NAMES = {
    0: "Water/Cloud/No Data",
    1: "Bare Soil/Urban",
    2: "Sparse Vegetation",
    3: "Dense Vegetation",
}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "vegetation_classes.tif"

# 1. Define Conditions and Choices
# The four ranges tile the whole real line, so every pixel lands in exactly one
# class. They are written for the map they are applied to: a function that closed
# over one array would then classify that array whatever it was handed.
def classify_ndvi(ndvi_map):
    """Threshold a continuous index map into the four class codes, as int8."""
    conditions = [
        (ndvi_map < 0.0),                             # Class 0: Water/Cloud/No Data
        (ndvi_map >= 0.0) & (ndvi_map < 0.2),         # Class 1: Bare Soil/Urban
        (ndvi_map >= 0.2) & (ndvi_map < 0.5),         # Class 2: Sparse Vegetation
        (ndvi_map >= 0.5)                             # Class 3: Dense Vegetation
    ]

    # The corresponding class codes
    choices = [0, 1, 2, 3]

    # 2. Apply Classification using np.select()
    # np.select evaluates conditions sequentially and assigns the corresponding choice.
    return np.select(conditions, choices, default=0).astype(np.int8)


vegetation_class_map = classify_ndvi(final_ndvi_map)

print("--- Classification Summary ---")
print(f"Resulting classification map shape: {vegetation_class_map.shape}")
print(f"Class map data type: {vegetation_class_map.dtype}")

# 3. Statistical Summary
unique_classes, counts = np.unique(vegetation_class_map, return_counts=True)
class_summary = dict(zip(unique_classes, counts))
total_pixels = final_ndvi_map.size

print("\nPixel Count per Class:")
for code, count in class_summary.items():
    percentage = (count / total_pixels) * 100
    print(f"Class {code} ({CLASS_NAMES[code]}: Count: {count:,}, "
          f"Percentage: {percentage:.2f}%)")

# 4. Interpretation Prompt
dominant = max(class_summary, key=class_summary.get)
interpretation = (
    f"Interpretation: Class {dominant} ({CLASS_NAMES[dominant]}) dominates the scene, "
    f"covering {class_summary[dominant] / total_pixels * 100:.2f}% of the total area. "
    f"Classes 2 and 3 together hold "
    f"{(class_summary.get(2, 0) + class_summary.get(3, 0)) / total_pixels * 100:.2f}%, "
    "so the scene is split between actively growing vegetation and bare or built "
    "surfaces rather than covered by one land cover."
)
print(f"\n{interpretation}")

# 5. The classes as a product: one byte per pixel, 255 for "not classified".
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
profile = {
    'driver': 'GTiff',
    'dtype': 'uint8',
    'nodata': 255,
    'width': vegetation_class_map.shape[1],
    'height': vegetation_class_map.shape[0],
    'count': 1,
    'crs': 'EPSG:32610',
    'transform': from_origin(500000.0, 4500000.0, 10.0, 10.0),
}
with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
    dst.write(vegetation_class_map.astype('uint8'), 1)
print(f"\nWrote class map to: {OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
