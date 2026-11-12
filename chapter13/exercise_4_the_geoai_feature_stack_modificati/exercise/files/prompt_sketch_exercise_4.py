import numpy as np
# richDEM has no installable wheel on current Python: slope, aspect and
# curvature come from Horn's 3x3 kernel and the 3x3 curvature stencil.

def z_score_normalize(data_array):
    # Calculates mean and standard deviation and returns normalized array
    return normalized_array

def create_advanced_feature_stack(dem_array):
    # 1. Calculate all four derivatives with numpy/scipy
    # 2. Normalize Elevation, Slope, and Curvature
    # 3. Stack the four resulting 2D arrays into a (4, H, W) array
    return feature_stack
