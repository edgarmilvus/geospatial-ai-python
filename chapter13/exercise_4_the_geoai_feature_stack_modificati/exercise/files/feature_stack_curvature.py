import numpy as np
import rasterio
from pathlib import Path
from scipy.ndimage import correlate
from rasterio.transform import from_origin

# --- Curvature without richDEM ---
# The book asks richDEM for profile_curvature. richDEM has no installable wheel on
# current Python, so the estimator is written out: the second derivatives come from
# the 3x3 stencil of Zevenbergen & Thorne, are projected onto the direction of
# steepest descent, and are divided by (1 + |grad|^2)^1.5. Positive means convex
# ground (flow spreads and accelerates), negative means a hollow (flow converges).

SIZE = 100
CELL_SIZE = 5.0
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "advanced_feature_stack.tif"

HORN_X = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
HORN_Y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
K_XX = np.array([[0, 0, 0], [1, -2, 1], [0, 0, 0]], dtype=np.float64)
K_YY = np.array([[0, 1, 0], [0, -2, 0], [0, 1, 0]], dtype=np.float64)
K_XY = np.array([[1, 0, -1], [0, 0, 0], [-1, 0, 1]], dtype=np.float64)


def synthetic_dem(size=SIZE, cell=CELL_SIZE):
    """A hill in the north-west, a hollow in the south-east, and a slight tilt.

    Two features, because the exercise is about telling a convex ridge from a
    concave drainage channel, and one shape cannot show both signs.
    """
    axis = np.arange(size) * cell
    X, Y = np.meshgrid(axis, axis)
    hill = 50.0 * np.exp(-((X - 150.0) ** 2 + (Y - 150.0) ** 2) / (2 * 80.0 ** 2))
    hollow = -40.0 * np.exp(-((X - 350.0) ** 2 + (Y - 350.0) ** 2) / (2 * 60.0 ** 2))
    Z = 200.0 + hill + hollow + 0.01 * X
    return Z.astype(np.float32)


def horn_gradient(dem, cell_size):
    dz_dx = correlate(dem.astype(np.float64), HORN_X, mode="nearest") / (8.0 * cell_size)
    dz_dy = correlate(dem.astype(np.float64), HORN_Y, mode="nearest") / (8.0 * cell_size)
    return dz_dx, dz_dy


def slope_degrees(dem, cell_size):
    dz_dx, dz_dy = horn_gradient(dem, cell_size)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def aspect_degrees(dem, cell_size):
    dz_dx, dz_dy = horn_gradient(dem, cell_size)
    aspect = np.degrees(np.arctan2(-dz_dx, dz_dy)) % 360.0
    aspect[np.hypot(dz_dx, dz_dy) < 1e-12] = 0.0
    return aspect


def profile_curvature(dem, cell_size):
    dem64 = dem.astype(np.float64)
    dz_dx, dz_dy = horn_gradient(dem, cell_size)
    d2x = correlate(dem64, K_XX, mode="nearest") / (cell_size ** 2)
    d2y = correlate(dem64, K_YY, mode="nearest") / (cell_size ** 2)
    d2xy = correlate(dem64, K_XY, mode="nearest") / (4.0 * cell_size ** 2)
    gradient_sq = dz_dx ** 2 + dz_dy ** 2
    along = (d2x * dz_dx ** 2 + 2.0 * d2xy * dz_dx * dz_dy
             + d2y * dz_dy ** 2) / np.maximum(gradient_sq, 1e-12)
    curvature = -along / (1.0 + gradient_sq) ** 1.5
    curvature[gradient_sq < 1e-12] = 0.0
    return curvature


def z_score_normalize(data_array):
    """Calculates Z-score normalization: (x - mu) / sigma."""
    valid_data = data_array[~np.isnan(data_array)]
    if valid_data.size == 0:
        return data_array

    mu = np.mean(valid_data)
    sigma = np.std(valid_data)

    if sigma == 0:
        return np.zeros_like(data_array)

    normalized_array = (data_array - mu) / sigma
    return normalized_array


def create_advanced_feature_stack(dem_data, cell_size=CELL_SIZE):

    # 1. Feature Calculation
    elevation = dem_data.astype(np.float64)
    slope = slope_degrees(dem_data, cell_size)
    aspect = aspect_degrees(dem_data, cell_size)
    curvature = profile_curvature(dem_data, cell_size)

    # 2. Data Normalization/Scaling (Z-score)
    # Normalize Elevation, Slope, and Curvature. Aspect (cyclical) is left raw.
    norm_elevation = z_score_normalize(elevation)
    norm_slope = z_score_normalize(slope)
    norm_curvature = z_score_normalize(curvature)

    # 3. Feature Stacking
    feature_list = [
        norm_elevation,
        norm_slope,
        aspect,  # Raw Aspect (for later cyclical transformation)
        norm_curvature,
    ]

    # Stack arrays along axis 0: (Channels, Rows, Cols)
    feature_stack = np.stack(feature_list, axis=0).astype(np.float32)

    # 4. Metadata Tracking
    print("--- GeoAI Feature Stack Summary ---")
    print(f"Stack Shape: {feature_stack.shape}")
    print("Feature Index Mapping:")
    print("[0]: Normalized Elevation")
    print("[1]: Normalized Slope")
    print("[2]: Raw Aspect (Degrees)")
    print("[3]: Normalized Profile Curvature")
    print(f"Aspect range kept raw: {aspect.min():.1f} to {aspect.max():.1f} degrees")
    print(f"Curvature before scaling: {curvature.min():.5f} to {curvature.max():.5f} 1/m")
    return feature_stack, feature_list


dem_data = synthetic_dem()
feature_stack, feature_list = create_advanced_feature_stack(dem_data)

# The stack is written as a four-band raster: channel 0 is band 1, and so on.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
profile = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'nodata': -9999.0,
    'width': SIZE,
    'height': SIZE,
    'count': feature_stack.shape[0],
    'crs': 'EPSG:32610',
    'transform': from_origin(500000.0, 4500000.0, CELL_SIZE, CELL_SIZE),
}
with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
    for index in range(feature_stack.shape[0]):
        dst.write(feature_stack[index], index + 1)
print(f"\nWrote {profile['count']}-band stack to: "
      f"{OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
