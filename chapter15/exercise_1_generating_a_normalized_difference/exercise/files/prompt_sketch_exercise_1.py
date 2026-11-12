# Required Python libraries often include: xarray, dask, stackstac, rioxarray, numpy
# Assume 'aoi_bbox' is a list defining the bounding box [min_lon, min_lat, max_lon, max_lat]
# Assume 'start_date' and 'end_date' are defined.

def calculate_ndvi_stack(data_cube):
    """
    Calculates NDVI across the multi-temporal stack.
    Input data_cube is expected to have bands dimension including 'red' and 'nir'.
    """
    # 1. Access the NIR and Red bands from the data_cube.
    # 2. Perform the vectorized calculation (NIR - Red) / (NIR + Red).
    # 3. Handle potential division by zero errors by masking or using numpy methods.
    # 4. Return the resulting xarray.DataArray (should only have time, y, x dimensions).
    pass

def verify_and_summarize(ndvi_stack):
    """
    Calculates and prints the global min, max, and mean NDVI.
    """
    # Use xarray reduction methods (e.g., .min().compute())
    # Print the summary statistics clearly.
    pass

# Main execution flow structure:
# raw_data_stack = stackstac.stack(...) # Query and stack the raw data
# ndvi_time_series = calculate_ndvi_stack(raw_data_stack)
# verify_and_summarize(ndvi_time_series)
