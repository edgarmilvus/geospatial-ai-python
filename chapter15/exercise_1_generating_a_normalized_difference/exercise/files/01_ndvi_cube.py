import numpy as np
import xarray as xr
import pandas as pd

# --- Simulation of Data Acquisition ---
# Define parameters for the simulated data cube (5 time steps, 100x100 pixels)
T, Y, X = 5, 100, 100
dates = pd.to_datetime(pd.date_range('2020-01-01', periods=T, freq='6MS'))
bands = ['red', 'nir']

# Simulate realistic band values (scaled 0-10000). The seed keeps the summary
# statistics below identical on every run.
RNG = np.random.default_rng(15)
red_data = RNG.integers(500, 2000, size=(T, Y, X))
nir_data = RNG.integers(2500, 4500, size=(T, Y, X))

raw_data_stack = xr.DataArray(
    data=np.stack([red_data, nir_data]),
    coords={
        'band': bands,
        'time': dates,
        'y': np.arange(Y),
        'x': np.arange(X)
    },
    dims=('band', 'time', 'y', 'x'),
    name='Sentinel_Bands'
).transpose('time', 'y', 'x', 'band') # Reorder to (T, Y, X, B)

def calculate_ndvi_stack(data_cube):
    """
    Calculates NDVI across the multi-temporal stack using vectorized operations.
    """
    # 1. Access the NIR and Red bands from the data_cube.
    nir = data_cube.sel(band='nir').astype(float)
    red = data_cube.sel(band='red').astype(float)
    
    # 2. Perform the vectorized calculation (NIR - Red) / (NIR + Red).
    numerator = nir - red
    denominator = nir + red
    
    # Calculate NDVI, handling division by zero by setting result to NaN
    ndvi = xr.where(denominator != 0, numerator / denominator, np.nan)
    
    # 3. Ensure the final structure is (time, y, x) and name the index it holds
    return ndvi.drop_vars('band', errors='ignore').rename('NDVI')

def verify_and_summarize(ndvi_stack):
    """
    Calculates and prints the global min, max, and mean NDVI.
    """
    # Use xarray reduction methods
    min_ndvi = ndvi_stack.min().item()
    max_ndvi = ndvi_stack.max().item()
    mean_ndvi = ndvi_stack.mean().item()
    
    print(f"--- NDVI Time Series Summary ---")
    print(f"Minimum NDVI: {min_ndvi:.4f}")
    print(f"Maximum NDVI: {max_ndvi:.4f}")
    print(f"Mean NDVI: {mean_ndvi:.4f}")
    
# Main execution flow:
ndvi_time_series = calculate_ndvi_stack(raw_data_stack)
verify_and_summarize(ndvi_time_series)
print(f"\nFinal NDVI Stack Dimensions: {ndvi_time_series.dims}")
