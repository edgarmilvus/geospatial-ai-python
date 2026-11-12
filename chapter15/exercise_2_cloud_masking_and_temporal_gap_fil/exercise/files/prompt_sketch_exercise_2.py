# Required Python libraries: xarray, numpy, pandas (for time indexing)

def apply_cloud_mask(ndvi_stack, qa_band):
    """
    Generates a boolean mask from the QA band and applies it to the NDVI stack.
    """
    # 1. Define the criteria for contamination (e.g., QA values > X).
    # 2. Create the boolean mask (contaminated = True).
    # 3. Use the boolean mask to set contaminated values in ndvi_stack to np.nan.
    # CRITICAL: Ensure the mask dimensions align perfectly with the NDVI stack.
    # Return the masked NDVI stack.
    pass

def interpolate_gaps(masked_ndvi_stack):
    """
    Performs linear interpolation along the time axis.
    """
    # Use xarray's .interpolate_na() method, specifying the dimension 'time'.
    # Return the gap-filled NDVI stack.
    pass

# Example of required boolean logic structure:
# contamination_mask = (qa_band & CLOUD_FLAG_BIT) > 0
# masked_ndvi = ndvi_stack.where(~contamination_mask) # Use the NOT operator (~)
