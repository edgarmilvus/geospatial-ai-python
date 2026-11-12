import numpy as np
import rasterio
from pathlib import Path
import matplotlib
matplotlib.use("Agg")             # no display in a headless run; save, never show
import matplotlib.pyplot as plt
from scipy.ndimage import correlate
from sklearn.preprocessing import StandardScaler

# --- Terrain derivatives without richDEM ---
# The book computes these three layers with richDEM. richDEM has no installable
# wheel on current Python, so the same algorithms are written here instead:
#   * slope and aspect come from Horn's 3x3 kernel, which is the estimator
#     richDEM's attrib='slope_degrees' / attrib='aspect' use;
#   * profile curvature comes from the 3x3 second-derivative stencil of
#     Zevenbergen & Thorne, again the estimator richDEM applies.
# Nothing else changes: the three layers are still standardized and stacked, and
# the code now shows the arithmetic the library was hiding.

# --- Configuration and Setup ---
# Define paths for input and output files
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
DEM_FILE = OUTPUT_DIR / "simulated_dem.tif"
FEATURE_STACK_FILE = OUTPUT_DIR / "terrain_feature_stack.tif"
HILLSHADE_FILE = OUTPUT_DIR / "hillshade.tif"

# Ensure output directory exists before writing files
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Simulate a Digital Elevation Model (DEM)
# In a production environment, this step loads an existing GeoTIFF.
SIZE = 128
RESOLUTION = 10.0  # Resolution in meters/pixel

# Horn's 3x3 kernels. The gradient is divided by 8 cells, the second derivatives
# by the cell size squared.
HORN_X = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
HORN_Y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)
K_XX = np.array([[0, 0, 0], [1, -2, 1], [0, 0, 0]], dtype=np.float64)
K_YY = np.array([[0, 1, 0], [0, -2, 0], [0, 1, 0]], dtype=np.float64)
K_XY = np.array([[1, 0, -1], [0, 0, 0], [-1, 0, 1]], dtype=np.float64)


def synthetic_dem(size=SIZE, resolution=RESOLUTION):
    """A rolling surface in metres: two sine waves over a slight regional tilt."""
    # The coordinates are metres, not array indices: with x in index units the
    # derivative would be per pixel and the cell size would have nowhere to go.
    x = np.arange(size) * resolution
    y = np.arange(size) * resolution
    X, Y = np.meshgrid(x, y)
    Z = 100.0 + 50.0 * np.sin(X / 300.0) * np.cos(Y / 250.0) + 0.02 * X
    return Z.astype(np.float32)


def horn_gradient(dem, cell_size):
    """dZ/dx (east positive) and dZ/dy (south positive) from Horn's 3x3 kernel."""
    dz_dx = correlate(dem.astype(np.float64), HORN_X, mode="nearest") / (8.0 * cell_size)
    dz_dy = correlate(dem.astype(np.float64), HORN_Y, mode="nearest") / (8.0 * cell_size)
    return dz_dx, dz_dy


def slope_degrees(dem, cell_size):
    """Slope: the magnitude of the gradient, as an angle from the horizontal."""
    dz_dx, dz_dy = horn_gradient(dem, cell_size)
    return np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))


def aspect_degrees(dem, cell_size):
    """Aspect: the compass direction of steepest descent, 0 = north, clockwise."""
    dz_dx, dz_dy = horn_gradient(dem, cell_size)
    # Screen rows grow southward, so the northward gradient is -dZ/dy.
    aspect = np.degrees(np.arctan2(-dz_dx, dz_dy)) % 360.0
    flat = np.hypot(dz_dx, dz_dy) < 1e-12
    aspect[flat] = 0.0        # a flat cell faces nowhere; 0 keeps the layer numeric
    return aspect


def profile_curvature(dem, cell_size):
    """Curvature along the flow line: positive on convex ground, negative in hollows."""
    dem64 = dem.astype(np.float64)
    dz_dx, dz_dy = horn_gradient(dem, cell_size)
    d2x = correlate(dem64, K_XX, mode="nearest") / (cell_size ** 2)
    d2y = correlate(dem64, K_YY, mode="nearest") / (cell_size ** 2)
    d2xy = correlate(dem64, K_XY, mode="nearest") / (4.0 * cell_size ** 2)

    gradient_sq = dz_dx ** 2 + dz_dy ** 2
    # Second derivative along the gradient direction (the fall line).
    along = (d2x * dz_dx ** 2 + 2.0 * d2xy * dz_dx * dz_dy
             + d2y * dz_dy ** 2) / np.maximum(gradient_sq, 1e-12)
    curvature = -along / (1.0 + gradient_sq) ** 1.5
    curvature[gradient_sq < 1e-12] = 0.0
    return curvature


def hillshade(dem, cell_size, azimuth=315.0, altitude=45.0):
    """Grey relief image: 255 where the surface faces the sun, 0 where it turns away."""
    slope = np.radians(slope_degrees(dem, cell_size))
    aspect = np.radians(aspect_degrees(dem, cell_size))
    zenith = np.radians(90.0 - altitude)
    shade = (np.cos(zenith) * np.cos(slope)
             + np.sin(zenith) * np.sin(slope) * np.cos(np.radians(azimuth) - aspect))
    return np.clip(255.0 * shade, 0.0, 255.0)


def standardize_band(band, name):
    """Z-score a band: (x - mean) / standard deviation, NaN preserved."""
    scaler = StandardScaler()
    valid = ~np.isnan(band)
    out = np.full(band.shape, np.nan, dtype=np.float32)
    out[valid] = scaler.fit_transform(band[valid].reshape(-1, 1)).ravel()
    print(f"   -> Standardized {name}. Shape: {out.shape}")
    return out


print("1. Simulating DEM data...")
dem_array = synthetic_dem()

# Define metadata for Rasterio (essential for a georeferenced product)
profile = {
    'driver': 'GTiff',
    'dtype': rasterio.float32,
    'nodata': -9999.0,
    'width': SIZE,
    'height': SIZE,
    'count': 1,
    'crs': 'EPSG:32610',  # Example UTM zone
    'transform': rasterio.transform.from_origin(500000.0, 4500000.0,
                                                RESOLUTION, RESOLUTION)
}

# Write the simulated DEM to disk, then read it back: the derivatives must be
# computed from what a downstream reader would get, not from a private array.
with rasterio.open(DEM_FILE, 'w', **profile) as dst:
    dst.write(dem_array, 1)

print(f"2. Loading DEM back from {DEM_FILE.name} ...")
with rasterio.open(DEM_FILE) as src:
    dem_array = src.read(1)
    cell_size = src.res[0]

print("3. Calculating Slope, Aspect, and Profile Curvature...")

# Slope: Measure of steepness (critical for identifying runoff potential)
slope = slope_degrees(dem_array, cell_size)

# Aspect: Direction the slope faces (influences solar radiation and soil moisture)
aspect = aspect_degrees(dem_array, cell_size)

# Profile Curvature: Rate of change of slope along the flow path (identifies acceleration/deceleration)
p_curvature = profile_curvature(dem_array, cell_size)

# Collect the derivatives as standard NumPy arrays for ML preprocessing
derivatives = {
    'slope': slope.astype(np.float32),
    'aspect': aspect.astype(np.float32),
    'p_curvature': p_curvature.astype(np.float32)
}

# 4. Feature Standardization (Mandatory for GeoAI/ML input)
print("4. Standardizing features using StandardScaler...")
feature_list = []
for name, arr in derivatives.items():
    feature_list.append(standardize_band(arr, name))

# 5. Stack and Write the Multi-Band Feature Raster
print(f"5. Writing multi-band feature stack to {FEATURE_STACK_FILE.name}...")
profile.update({
    'count': len(feature_list),
    'dtype': rasterio.float32,
    'nodata': profile['nodata']
})
with rasterio.open(FEATURE_STACK_FILE, 'w', **profile) as dst:
    for i, feature_array in enumerate(feature_list):
        dst.write(feature_array, i + 1)

print("\nProcess Complete. The GeoAI feature stack is ready.")
print(f"Output Feature Stack: {FEATURE_STACK_FILE.name} | Bands: {profile['count']}")
print(f"Stack shape (channels, rows, cols): {np.stack(feature_list).shape}")

# The relief image is not a model feature: it is how a reader checks the stack.
shade = hillshade(dem_array, cell_size)
with rasterio.open(HILLSHADE_FILE, 'w', **{**profile, 'count': 1,
                                          'nodata': 0.0}) as dst:
    dst.write(shade.astype(np.float32), 1)
print(f"Relief check written to: {HILLSHADE_FILE.name}")

print("\n--- Terrain Summary ---")
print(f"Elevation: {dem_array.min():.1f} m to {dem_array.max():.1f} m")
print(f"Slope: {slope.min():.2f}° to {slope.max():.2f}° (mean {slope.mean():.2f}°)")
print(f"Aspect: {aspect.min():.1f}° to {aspect.max():.1f}°")
print(f"Profile curvature: {p_curvature.min():.5f} to {p_curvature.max():.5f} (1/m)")

# A picture of the relief, written next to the rasters.
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
axes[0].imshow(shade, cmap='gray')
axes[0].set_title('Hillshade (az 315, alt 45)')
axes[1].imshow(slope, cmap='magma')
axes[1].set_title('Slope (degrees)')
axes[2].imshow(p_curvature, cmap='RdBu_r', vmin=-np.abs(p_curvature).max(),
               vmax=np.abs(p_curvature).max())
axes[2].set_title('Profile curvature')
for ax in axes:
    ax.set_xticks([])
    ax.set_yticks([])
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "terrain_overview.png", dpi=110)
plt.close(fig)
print(f"Figure written to: terrain_overview.png")
