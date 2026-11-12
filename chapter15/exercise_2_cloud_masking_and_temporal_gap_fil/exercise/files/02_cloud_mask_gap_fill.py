import numpy as np
import xarray as xr
import pandas as pd

# Simulation setup (T=5, Y=100, X=100)
T, Y, X = 5, 100, 100
dates = pd.to_datetime(pd.date_range('2020-01-01', periods=T, freq='6MS'))

# A fixed seed keeps the time series, and the gaps the mask cuts into it, identical.
RNG = np.random.default_rng(15)

# Simulated NDVI and QA data
ndvi_stack = xr.DataArray(
    data=RNG.uniform(0.1, 0.8, size=(T, Y, X)),
    coords={'time': dates, 'y': np.arange(Y), 'x': np.arange(X)},
    dims=('time', 'y', 'x'),
    name='NDVI'
)

# A realistic QA band is mostly clean: here one observation in ten is contaminated.
qa_band_data = np.zeros((T, Y, X), dtype=np.int8)
qa_band_data[RNG.random((T, Y, X)) < 0.10] = 1

# Force contamination at two interior observations of one pixel, and nowhere else
# in its series, so the reader can watch interpolation fill a gap rather than only
# reading that masking happened.
qa_band_data[:, 50, 50] = 0
qa_band_data[1, 50, 50] = 1
qa_band_data[3, 50, 50] = 1

qa_band = xr.DataArray(
    data=qa_band_data,
    coords={'time': dates, 'y': np.arange(Y), 'x': np.arange(X)},
    dims=('time', 'y', 'x'),
    name='QA_Mask'
)
CLOUD_CONTAMINATION_FLAG = 1

def apply_cloud_mask(ndvi_stack, qa_band):
    """
    Generates a boolean mask from the QA band and applies it to the NDVI stack.
    """
    # 1. Define the criteria for contamination (True where contaminated).
    contamination_mask = qa_band == CLOUD_CONTAMINATION_FLAG
    
    # 2. Apply the mask: use .where(~mask) to keep values ONLY where the mask is False (clean).
    # Contaminated pixels are set to np.nan by default.
    masked_ndvi_stack = ndvi_stack.where(~contamination_mask) 
    
    return masked_ndvi_stack

def interpolate_gaps(masked_ndvi_stack):
    """
    Performs linear interpolation along the time axis.
    """
    # Use xarray's .interpolate_na() method, specifying the dimension 'time'.
    interpolated_ndvi_stack = masked_ndvi_stack.interpolate_na(dim='time', method='linear')
    return interpolated_ndvi_stack

# Main execution flow
masked_ndvi = apply_cloud_mask(ndvi_stack, qa_band)
interpolated_ndvi = interpolate_gaps(masked_ndvi)

# 4. Visualization Preparation for a single pixel (50, 50)
pixel_x, pixel_y = 50, 50
raw_ts = ndvi_stack.sel(x=pixel_x, y=pixel_y).values
masked_ts = masked_ndvi.sel(x=pixel_x, y=pixel_y).values
interpolated_ts = interpolated_ndvi.sel(x=pixel_x, y=pixel_y).values

print(f"Contaminated observations: {int(qa_band_data.sum())} of {T * Y * X} "
      f"({100 * qa_band_data.mean():.1f}%)")
print(f"--- Cloud Masking and Interpolation Summary (Pixel {pixel_x}, {pixel_y}) ---")
print("Raw Time Series:", np.round(raw_ts, 4))
print("Masked Time Series:", np.round(masked_ts, 4))
print("Interpolated Time Series:", np.round(interpolated_ts, 4))
