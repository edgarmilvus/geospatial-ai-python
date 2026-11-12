# Assume this is the input profile after clipping
input_profile = {
    'driver': 'GTiff',
    'dtype': 'uint16',
    'nodata': 0.0,
    'width': 1024, # Could be float in some contexts
    'height': 1024, # Could be float in some contexts
    'count': 4,
    'crs': 'EPSG:32617',
    'transform': (10.0, 0.0, 500000.0, 0.0, -10.0, 100000.0), # Example tuple
    'is_tiled': False,
    'interleave': 'band',
    # ... many other non-essential keys
}

# The challenge is to use Dictionary Comprehension to generate clean_profile
# Expected result structure:
clean_profile = {
    # Only the six target keys should be present
    'crs': 'EPSG:32617',
    'transform': (10.0, 0.0, 500000.0, 0.0, -10.0, 100000.0),
    'width': 1024, # Must be int
    'height': 1024, # Must be int
    'dtype': 'uint16',
    'count': 4
}
