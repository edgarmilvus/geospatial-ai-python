import numpy as np
import rasterio
# Note: rasterio is imported primarily to establish context, 
# though we use numpy extensively for simulation in this simple example.

# --- 1. Simulation Parameters ---
# Define a small geographic area (e.g., 10x10 pixels)
HEIGHT, WIDTH = 10, 10
NUM_TIMESTEPS = 3 # T1, T2, T3 (representing three months/years)

# --- 2. Simulate Multi-Temporal Satellite Data Stack ---
# We need Red (R) and Near-Infrared (NIR) bands for NDVI calculation.
# Data is stored as (Time, Height, Width, Bands)
# Band index 0: Red (R), Band index 1: Near-Infrared (NIR)

# Initialize the data stack with zeros and ensure float type for calculations
data_stack = np.zeros((NUM_TIMESTEPS, HEIGHT, WIDTH, 2), dtype=np.float32)

# Seed the generator so the simulated scene, and every number printed below,
# is the same on every run of this listing.
RNG = np.random.default_rng(15)

# Simulate data progression (e.g., a deforestation event)

# T1 (Healthy Vegetation - High NIR, Low Red)
# High NIR (0.6 - 0.7), Low Red (0.05 - 0.15) -> High NDVI (~0.7)
data_stack[0, :, :, 1] = RNG.uniform(0.6, 0.7, (HEIGHT, WIDTH)) # NIR T1
data_stack[0, :, :, 0] = RNG.uniform(0.05, 0.15, (HEIGHT, WIDTH)) # Red T1

# T2 (Partial Stress/Early Deforestation)
# NIR drops (0.4 - 0.5), Red increases (0.15 - 0.25) -> Mid NDVI (~0.3)
data_stack[1, :, :, 1] = RNG.uniform(0.4, 0.5, (HEIGHT, WIDTH)) # NIR T2
data_stack[1, :, :, 0] = RNG.uniform(0.15, 0.25, (HEIGHT, WIDTH)) # Red T2

# T3 (Deforested/Bare Earth - Low NIR, High Red)
# Low NIR (0.1 - 0.2), High Red (0.25 - 0.35) -> Low NDVI (~ -0.2)
data_stack[2, :, :, 1] = RNG.uniform(0.1, 0.2, (HEIGHT, WIDTH)) # NIR T3
data_stack[2, :, :, 0] = RNG.uniform(0.25, 0.35, (HEIGHT, WIDTH)) # Red T3

# --- 3. Define the Core Calculation Function (NDVI) ---
def calculate_ndvi(red_band, nir_band):
    """Calculates the Normalized Difference Vegetation Index (NDVI).
    NDVI = (NIR - Red) / (NIR + Red)
    """
    # Use numpy for vectorized, element-wise array operations
    numerator = nir_band - red_band
    denominator = nir_band + red_band

    # CRITICAL: Handle division by zero safely using np.where
    # If denominator is zero, set NDVI to 0.0 (or NaN, depending on standard)
    ndvi = np.where(denominator > 0, numerator / denominator, 0.0)
    return ndvi

# --- 4. Process the Time Series Stack ---
# Initialize a list to hold the resulting 2D NDVI maps
ndvi_time_series = []

print(f"Starting time series analysis for {NUM_TIMESTEPS} steps...")

# Iterate through each temporal slice (axis 0 of the data_stack)
for t in range(NUM_TIMESTEPS):
    # Extract the specific time slice (e.g., T1 data: 10x10x2)
    current_data = data_stack[t]

    # Separate the bands using standard array slicing:
    # Index 0 is Red, Index 1 is NIR (the last dimension)
    red = current_data[:, :, 0]
    nir = current_data[:, :, 1]

    # Calculate NDVI for the current time step (10x10 array)
    ndvi_map = calculate_ndvi(red, nir)

    # Store the resulting 2D map
    ndvi_time_series.append(ndvi_map)

    # Print summary statistics to confirm the change detection logic
    print(f"Time Step T{t+1}:")
    print(f"  Mean NDVI: {ndvi_map.mean():.4f}")

# --- 5. Reconstruct the Results Stack ---
# Convert the list of 2D NDVI maps back into a 3D NumPy array (Time, Height, Width)
final_ndvi_stack = np.stack(ndvi_time_series, axis=0)

print("\nProcessing complete.")
print(f"Final NDVI stack shape: {final_ndvi_stack.shape}")
print(f"Change detected: T1 Mean NDVI ({final_ndvi_stack[0].mean():.4f}) -> T3 Mean NDVI ({final_ndvi_stack[2].mean():.4f})")
