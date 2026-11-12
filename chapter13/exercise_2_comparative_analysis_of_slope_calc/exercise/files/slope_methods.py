import numpy as np
import time
from scipy.ndimage import correlate

# --- The two estimators ---
# The book compares a NumPy finite difference against richDEM. richDEM has no
# installable wheel on current Python, so the second column is Horn's 3x3 kernel,
# which is the estimator richDEM's attrib='slope' applies: every cell of the window
# is weighted, the diagonals at half the weight of the edge neighbours, and the sum
# divided by 8 cell widths. Comparing the two is the exercise; the numbers now come
# from arithmetic the reader can check, not from a library that will not install.

SIZE = 500
CELL_SIZE = 10.0
SEED = 1123                      # one seed: the same DEM on every machine
REPEATS = 3                      # best of three timings, so a slow tick is not the story

# Horn's kernels: the same weights GDAL and richDEM use.
HORN_X = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
HORN_Y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)


def synthetic_dem(size=SIZE):
    """A 0.5 m per row ramp with 2 m of rugged noise on top."""
    rng = np.random.default_rng(SEED)
    return (np.indices((size, size))[0] * 0.5 + rng.random((size, size)) * 2.0)


def calculate_slope_numpy(dem_array, cell_size):
    """Calculates slope in degrees using NumPy's central difference approximation."""

    # Calculate gradients (dz/dx and dz/dy)
    dz_dy, dz_dx = np.gradient(dem_array, cell_size)

    # Calculate total slope (tan(theta) = sqrt(dz/dx)^2 + (dz/dy)^2)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))

    # Convert to degrees
    slope_deg = np.degrees(slope_rad)

    return slope_deg


def calculate_slope_horn(dem_array, cell_size):
    """Slope in degrees from Horn's 3x3 kernel, as richDEM computes it."""
    dz_dx = correlate(dem_array, HORN_X, mode="nearest") / (8.0 * cell_size)
    dz_dy = correlate(dem_array, HORN_Y, mode="nearest") / (8.0 * cell_size)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def fastest(call, repeats=REPEATS):
    """Run a function a few times and keep its best wall-clock time, in seconds."""
    best = float("inf")
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = call()
        best = min(best, time.perf_counter() - start)
    return result, best


def run_slope_comparison(dem_array, cell_size):

    # 1. NumPy Slope Implementation & Benchmarking
    slope_np, time_np = fastest(lambda: calculate_slope_numpy(dem_array, cell_size))

    # 2. Horn Slope Implementation & Benchmarking
    slope_horn, time_rd = fastest(lambda: calculate_slope_horn(dem_array, cell_size))

    # 3. Performance Benchmarking
    print(f"--- Performance Comparison (Grid Size: {dem_array.shape}) ---")
    print(f"NumPy Slope Time: {time_np:.4f} seconds")
    print(f"Horn Slope Time: {time_rd:.4f} seconds")
    if time_rd > 0:
        print(f"NumPy/Horn Time Ratio: {time_np / time_rd:.1f}x")

    # 4. Statistical Comparison
    diff = slope_np - slope_horn
    rmse = np.sqrt(np.mean(diff**2))

    print("\n--- Statistical Comparison (Slope in Degrees) ---")
    print(f"NumPy Mean Slope: {slope_np.mean():.2f}, Std Dev: {slope_np.std():.2f}")
    print(f"Horn Mean Slope: {slope_horn.mean():.2f}, Std Dev: {slope_horn.std():.2f}")
    print(f"Root Mean Square Error (RMSE) between methods: {rmse:.4f}")
    print(f"Maximum absolute difference: {np.abs(diff).max():.4f}")
    return slope_np, slope_horn, time_np, time_rd, rmse


dem_array = synthetic_dem()
slope_np, slope_horn, time_np, time_horn, rmse = run_slope_comparison(dem_array, CELL_SIZE)

print("\n--- Where the two disagree ---")
print(f"Cells: {dem_array.size}")
print(f"Cells differing by more than 1 degree: {int((np.abs(slope_np - slope_horn) > 1).sum())}")
print(f"Cells differing by more than 5 degrees: {int((np.abs(slope_np - slope_horn) > 5).sum())}")
