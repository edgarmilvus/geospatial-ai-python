# Assume this is the input profile after clipping
input_profile = {
    'driver': 'GTiff',
    'dtype': 'uint16',
    'nodata': 0.0,
    'width': 1024.0,  # Note: Changed to float for demonstration of type conversion
    'height': 1024.0, # Note: Changed to float for demonstration of type conversion
    'count': 4,
    'crs': 'EPSG:32617',
    'transform': (10.0, 0.0, 500000.0, 0.0, -10.0, 100000.0),
    'is_tiled': False,
    'interleave': 'band',
}

# 1. Define Target Keys
TARGET_KEYS = ['crs', 'transform', 'width', 'height', 'dtype', 'count']

# 2, 3, 4. Dictionary Comprehension with Filtering and Type Conversion
clean_profile = {
    k: int(v) if k in ('width', 'height') else v
    for k, v in input_profile.items()
    if k in TARGET_KEYS
}

# Demonstration of result
import pprint
pprint.pprint(clean_profile)
