import numpy as np

# Simulated 5x5 array data (example values)
# Values scaled 0-1000 for simplicity
red_band = np.array([
    [100, 150, 200, 120, 180],
    [110, 160, 210, 130, 190],
    [120, 170, 220, 140, 200],
    [130, 180, 230, 150, 210],
    [140, 190, 240, 160, 220]
], dtype=np.float32)

nir_band = np.array([
    [500, 600, 700, 550, 650],
    [510, 610, 710, 560, 660],
    [520, 620, 720, 570, 670],
    [530, 630, 730, 580, 680],
    [540, 640, 740, 590, 690]
], dtype=np.float32)

# 1. Calculate Numerator (Difference) and Denominator (Sum)
diff_bands = nir_band - red_band
sum_bands = nir_band + red_band

# 4. Denominator Check
print("--- Denominator Check ---")
print("Sum Bands (NIR + Red):\n", sum_bands)

# 2. Implement the NDVI formula (vectorized element-wise division)
# The result inherits the float32 dtype from the inputs.
ndvi_array = diff_bands / sum_bands

# 3. Output Verification
print("\n--- NDVI Verification ---")
print(f"NDVI Data Type: {ndvi_array.dtype}")
print(f"NDVI Shape: {ndvi_array.shape}")
print(f"NDVI Minimum Value: {ndvi_array.min():.4f}")
print(f"NDVI Maximum Value: {ndvi_array.max():.4f}")
print(f"Values inside [-1, 1]: {bool(np.all((ndvi_array >= -1.0) & (ndvi_array <= 1.0)))}")

# The number of pixels the whole calculation touched, without a single Python loop:
# nine short rows, and one division per cell applies to all of them at once.
print(f"Pixels computed: {ndvi_array.size} (no explicit loop)")

print("\n--- NDVI Array ---")
print(ndvi_array)
