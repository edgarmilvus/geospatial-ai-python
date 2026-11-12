import numpy as np
import pandas as pd
import xarray as xr
import rioxarray # Used for geospatial context handling

# --- 1. Configuration and Data Simulation ---

# Define the analysis period and spatial dimensions
START_DATE = '2019-01-01'
END_DATE = '2023-12-31'
TIME_STEPS = (pd.to_datetime(END_DATE) - pd.to_datetime(START_DATE)).days // 30
Y_DIM, X_DIM = 50, 50
Z_THRESHOLD = 2.5 # Statistical threshold for anomaly detection (2.5 standard deviations)
MIN_PERSISTENCE = 3 # Minimum consecutive months below threshold to confirm deforestation
BASELINE_STEPS = 24 # The first two years describe the expected, undisturbed trajectory

# A fixed seed makes the simulated cube, and every number printed below, reproducible.
RNG = np.random.default_rng(15)

def simulate_sentinel_stack(time_steps, y_dim, x_dim, rng):
    """
    Simulates a multi-temporal stack of Sentinel-2 bands (NIR and Red).
    Data is wrapped in an xarray Dataset for labeled processing.
    """
    time_index = pd.date_range(start=START_DATE, periods=time_steps, freq='MS')
    
    # 1a. Generate initial healthy forest data (high NIR, low Red)
    # NIR (Band 8): Mean reflectance around 0.45 (4500 scaled)
    nir_base = rng.normal(loc=4500, scale=150, size=(time_steps, y_dim, x_dim))
    # Red (Band 4): Mean reflectance around 0.10 (1000 scaled)
    red_base = rng.normal(loc=1000, scale=80, size=(time_steps, y_dim, x_dim))
    
    # 1b. Inject a deforestation event (Simulated change at T=30, affecting a 10x10 area)
    deforestation_start_time = 30
    affected_slice = (slice(10, 20), slice(10, 20))
    
    # After the event, NIR drops significantly (to ~0.15), Red rises slightly (to ~0.12)
    nir_base[deforestation_start_time:, affected_slice[0], affected_slice[1]] -= 3000
    red_base[deforestation_start_time:, affected_slice[0], affected_slice[1]] += 200
    
    # Ensure values remain realistic (0-10000 scale)
    nir_base = np.clip(nir_base, 500, 10000).astype(np.int16)
    red_base = np.clip(red_base, 500, 10000).astype(np.int16)

    # 1c. Combine into a labeled xarray Dataset
    data_vars = {
        'B8_NIR': (('time', 'y', 'x'), nir_base),
        'B4_RED': (('time', 'y', 'x'), red_base)
    }
    coords = {
        'time': time_index,
        'y': np.arange(y_dim),
        'x': np.arange(x_dim)
    }
    
    stack = xr.Dataset(data_vars=data_vars, coords=coords)
    
    # Add dummy geospatial metadata (crucial for real-world GeoAI)
    stack = stack.rio.write_crs("EPSG:4326")
    return stack

# --- 2. Feature Engineering: NDVI Calculation ---

def calculate_ndvi(ds):
    """Calculates NDVI using vectorized xarray operations."""
    # Assuming standard 16-bit scaling (0-10000)
    nir = ds['B8_NIR'].astype(np.float32)
    red = ds['B4_RED'].astype(np.float32)
    
    # Vectorized calculation across all time steps and spatial dimensions
    ndvi = (nir - red) / (nir + red)
    ndvi = ndvi.where((nir + red) != 0, 0.0) # Handle division by zero
    
    return ndvi.rename("NDVI")

# --- 3. Time Series Anomaly Detection Pipeline ---

def detect_deforestation_date(ndvi_stack, z_threshold, min_persistence, baseline_steps):
    """
    Performs pixel-wise statistical change detection.
    
    Returns a 2D array (Y, X) containing the date index of the first confirmed
    deforestation event, or -1 if no event occurred.
    """
    
    # 3a. Calculate the statistical baseline per pixel, from the undisturbed
    # part of the record only. Including the changed years would pull the mean
    # towards the bare soil and shrink the anomaly it is meant to expose.
    baseline = ndvi_stack.isel(time=slice(0, baseline_steps))
    ndvi_mean = baseline.mean(dim='time')
    ndvi_std = baseline.std(dim='time')
    
    # 3b. Calculate the Z-score for every observation against that baseline
    # Z-score = (Observation - Mean) / Standard Deviation
    z_scores = (ndvi_stack - ndvi_mean) / ndvi_std
    
    # 3c. Identify potential anomaly candidates (significant negative deviation)
    # A negative Z-score indicates a drop below the historical mean.
    anomaly_mask = (z_scores < -z_threshold).isel(time=slice(baseline_steps, None))
    
    # Convert mask to a 3D numpy array for efficient sequential processing
    anomaly_np = anomaly_mask.values
    
    # Initialize the result array: Stores the time index of the confirmed DoD
    # Use -1 to denote 'No Change Detected'
    dod_index = np.full((ndvi_stack.sizes['y'], ndvi_stack.sizes['x']), -1, dtype=np.int32)
    
    # 3d. Sequential persistence check (The core change detection logic)
    T = anomaly_np.shape[0] # Months monitored after the baseline
    
    for y in range(dod_index.shape[0]):
        for x in range(dod_index.shape[1]):
            persistence_count = 0
            
            # Iterate through the monitored months for the current pixel (y, x)
            for t in range(T):
                if anomaly_np[t, y, x]:
                    # Anomaly detected, increment persistence counter
                    persistence_count += 1
                else:
                    # Anomaly broken, reset counter
                    persistence_count = 0
                
                # Check for confirmed event
                if persistence_count == min_persistence:
                    # Event confirmed. The DoD is the start of the persistent drop,
                    # expressed on the full stack's time axis.
                    dod_index[y, x] = baseline_steps + t - min_persistence + 1
                    break # Stop processing this pixel's time series
                    
    return dod_index

# --- 4. Execution and Quantification ---

# 4a. Load/Generate the data stack
print(f"Generating synthetic Sentinel-2 stack ({TIME_STEPS} monthly observations)...")
sentinel_ds = simulate_sentinel_stack(TIME_STEPS, Y_DIM, X_DIM, RNG)

# 4b. Calculate NDVI
ndvi_stack = calculate_ndvi(sentinel_ds)

# 4c. Run the change detection pipeline
print("Running time series anomaly detection...")
date_index_of_deforestation = detect_deforestation_date(
    ndvi_stack, Z_THRESHOLD, MIN_PERSISTENCE, BASELINE_STEPS
)

# 4d. Post-processing and Quantification

# Convert the resulting index array back to a meaningful xarray DataArray
dod_xr = xr.DataArray(
    date_index_of_deforestation, 
    coords={'y': sentinel_ds.y, 'x': sentinel_ds.x},
    dims=['y', 'x'],
    name="Date_Index_of_Deforestation"
)

# Calculate the total affected area (assuming 10m resolution, 100 sq meters per pixel)
AFFECTED_PIXELS = (dod_xr != -1).sum().item()
PIXEL_AREA_M2 = 100 
TOTAL_AREA_HECTARES = (AFFECTED_PIXELS * PIXEL_AREA_M2) / 10000

# Map the index back to actual dates for reporting
def get_date_from_index(index):
    """Converts the time index back to the actual date string."""
    if index == -1:
        return "N/A (No Change)"
    return sentinel_ds.time.values[index].astype(str)[:10]

# Find the earliest and latest detected events
detected_indices = date_index_of_deforestation[date_index_of_deforestation != -1]

if detected_indices.size > 0:
    EARLIEST_DOD_INDEX = detected_indices.min()
    LATEST_DOD_INDEX = detected_indices.max()
    
    earliest_dod = get_date_from_index(EARLIEST_DOD_INDEX)
    latest_dod = get_date_from_index(LATEST_DOD_INDEX)
else:
    earliest_dod = "N/A"
    latest_dod = "N/A"


# 4e. Output Summary
print("\n--- Deforestation Tracking Report ---")
print(f"Analysis Period: {START_DATE} to {END_DATE}")
print(f"Baseline Window: {BASELINE_STEPS} months, "
      f"{get_date_from_index(0)} to {get_date_from_index(BASELINE_STEPS - 1)}")
print(f"Anomaly Threshold: Z-score < -{Z_THRESHOLD}")
print(f"Persistence Requirement: {MIN_PERSISTENCE} consecutive months")
print("-" * 35)
print(f"Total Pixels Analyzed: {Y_DIM * X_DIM}")
print(f"Total Affected Pixels: {AFFECTED_PIXELS}")
print(f"Total Deforested Area: {TOTAL_AREA_HECTARES:.2f} Hectares")
print(f"Earliest Detected Event Date: {earliest_dod}")
print(f"Latest Detected Event Date: {latest_dod}")
