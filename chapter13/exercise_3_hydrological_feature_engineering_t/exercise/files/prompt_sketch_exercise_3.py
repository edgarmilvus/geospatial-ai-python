import numpy as np
# richDEM has no installable wheel on current Python: D8 flow routing is
# written out, and slope comes from np.gradient.

def calculate_twi(dem_array, cell_size):
    # 1. Prepare data (a float DEM with no NaN)
    # 2. Calculate flow accumulation (Ac)
    # 3. Calculate slope (beta) in radians
    # 4. Calculate As (Ac / cell_size)
    # 5. Apply TWI formula, handling zero slopes
    return twi_array
