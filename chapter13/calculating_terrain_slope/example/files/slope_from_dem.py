import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_origin

# --- 1. Configuration and Synthetic DEM Generation ---

# Define the dimensions of our synthetic terrain (100x100 pixels)
ROWS, COLS = 100, 100

# Spatial resolution: The real-world distance represented by one pixel side (in meters)
CELL_SIZE = 10.0

# The project's output folder, resolved from this file's own position so the
# script runs from any working directory.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "slope_degrees.tif"


def synthetic_dem(rows=ROWS, cols=COLS, peak_height=25.0):
    """A gentle ramp with a smooth Gaussian hill added near the centre."""
    # Create a base elevation array (Z) representing a gentle, uniform ramp
    # This simulates elevation rising from 0m to 50m across the width and height.
    # The rise is 50 m over 99 cells of 10 m, so the ramp's true grade is
    # (50 / 99) / 10 = 0.0505 m per metre on each axis: 4.09 degrees, not 45.
    x_coords = np.linspace(0, 50, cols)
    y_coords = np.linspace(0, 50, rows)

    # Use np.outer to create a 2D plane where Z = X + Y
    zm = np.outer(np.ones(rows), x_coords) + np.outer(y_coords, np.ones(cols))

    # Introduce a small, complex feature (a Gaussian peak) near the center
    # This ensures the calculated slope is not perfectly uniform.
    center_row, center_col = rows // 2, cols // 2
    peak_size = 20  # Size of the peak area (20x20 window)

    # Create indices for the peak area
    r_indices = np.arange(peak_size) - peak_size // 2
    c_indices = np.arange(peak_size) - peak_size // 2

    # Generate a 2D Gaussian function (for smooth, bell-shaped elevation)
    gaussian_peak = peak_height * np.exp(-(r_indices**2)[:, None] / 10.0
                                         - (c_indices**2)[None, :] / 10.0)

    # Add the peak to the center of the ramp
    zm[center_row - peak_size // 2: center_row + peak_size // 2,
       center_col - peak_size // 2: center_col + peak_size // 2] += gaussian_peak
    return zm.astype(np.float32)


def slope_degrees(dem, cell_size=CELL_SIZE):
    """Slope in degrees from a DEM, via the gradient in metres per metre."""
    # --- 2. Calculate Partial Derivatives (The Gradient) ---

    # The gradient function calculates the rate of change (delta Z / delta distance).
    # By passing CELL_SIZE (10.0), we ensure the output is in meters/meter (rise/run),
    # rather than meters/pixel index.
    # The output order is typically (dZ/dY, dZ/dX)
    dy_dz, dx_dz = np.gradient(dem, cell_size)

    # --- 3. Calculate Total Slope Magnitude (Tangent) ---

    # The total steepness (slope tangent) is the magnitude of the vector defined by
    # the partial derivatives (Pythagorean theorem: S = sqrt(dx^2 + dy^2)).
    slope_tangent = np.sqrt(dx_dz**2 + dy_dz**2)

    # --- 4. Convert to Standard Units (Degrees) ---

    # Use arctan (inverse tangent) to convert the tangent value (rise/run) into
    # the angle in radians, then to degrees (standard geospatial output format).
    return np.degrees(np.arctan(slope_tangent))


def main():
    DEM = synthetic_dem()

    # --- 5. Prepare Geospatial Metadata (Rasterio context) ---

    # Define the Affine transformation (required by Rasterio to locate the data)
    # This maps the pixel coordinates to real-world coordinates.
    transform = from_origin(500000.0, 4500000.0, CELL_SIZE, CELL_SIZE)

    # A 10 m cell is a linear unit, so the CRS must be projected: UTM zone 10N.
    # (The book's EPSG:4326 placeholder would declare a 10 *degree* cell.)
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.float32,
        'nodata': -9999,
        'width': COLS,
        'height': ROWS,
        'count': 1,  # Single band output
        'crs': 'EPSG:32610',  # UTM zone 10N: metres, matching CELL_SIZE
        'transform': transform
    }

    slope = slope_degrees(DEM)

    # --- 6. Report Key Statistics ---

    print("--- Digital Elevation Model (DEM) Analysis ---")
    print(f"Input Grid Shape: {DEM.shape}")
    print(f"Resolution (Meters/Pixel): {CELL_SIZE}")
    print("-" * 45)
    print(f"Maximum Elevation: {np.max(DEM):.2f} m")
    print(f"Minimum Elevation: {np.min(DEM):.2f} m")
    print("-" * 45)
    print(f"Maximum Calculated Slope: {np.max(slope):.2f}° (Found at the peak)")
    print(f"Average Calculated Slope: {np.mean(slope):.2f}°")
    print(f"Slope on the flat ramp: {slope[5, 5]:.2f}°")
    print("-" * 45)

    # --- 7. Write the slope as a one-band GeoTIFF ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
        dst.write(slope.astype('float32'), 1)
    print(f"Slope written to: {OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
    print(f"Product: 1 band | float32 | nodata {profile['nodata']} | "
          f"crs {profile['crs']} | cell {CELL_SIZE} m")


if __name__ == "__main__":
    main()
