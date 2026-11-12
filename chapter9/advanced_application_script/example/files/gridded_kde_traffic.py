import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
import folium
from folium.plugins import HeatMap
import pathlib
import warnings

# --- Five corrections to the book's script, and why ---
#
# 1. The bandwidth. `gaussian_kde(coords, bw_method=0.0035)` does not mean "0.0035 degrees":
#    scipy's `bw_method` is a *factor* applied to the data's own standard deviation, so the
#    smoothing radius silently changed with the spread of the sample. The factor is now
#    computed from the bandwidth in degrees, `bw_method = bandwidth / mean(std)`, and both
#    numbers are printed so the unit is not a guess.
# 2. The weights. Folium 0.19 removed `max_val` from `HeatMap` (it warns and ignores it) and
#    leaflet-heat expects intensities in 0..1, so raw densities scaled by 10 000 paint every
#    cell of the city in the top colour. The weights are normalised so the cap the comment
#    describes - half the peak - is what saturates, and nothing exceeds 1.0.
# 3. The gradient keys were floats, and folium camelises every option key, so `0.2` raised
#    `AttributeError: 'float' object has no attribute 'split'` before the file could be
#    written. String keys are what the JavaScript wants anyway.
# 4. The map was saved as `advanced_traffic_kde_heatmap.html` in the current directory and
#    the path was printed absolute. It now goes to the project's output/ folder and is
#    reported relative to it.
# 5. The CartoDB tile names warn about an API key in folium 0.19. No tile is fetched while
#    the file is built, so the build stays quiet.
warnings.filterwarnings('ignore', message='CartoDB tiles now require an API key')

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- 1. CONFIGURATION AND DATA SIMULATION ---

# Define the number of simulated GPS points
N_POINTS = 5000
# Define the approximate center of the study area (e.g., a major metropolitan area)
CENTER_LAT, CENTER_LON = 34.0522, -118.2437
# Define the resolution of the calculation grid (e.g., 150x150 cells)
GRID_RESOLUTION = 150
# Define the KDE bandwidth in DEGREES (controls smoothness: smaller = sharper hotspots).
# 0.0035 degrees of latitude is about 390 metres.
KDE_BANDWIDTH = 0.0035
# Fraction of the peak density at which the colour scale saturates.
CAP_FRACTION = 0.5
# One degree of latitude, in metres, for the sentence that puts the bandwidth on the ground.
BANDWIDTH_METRES = KDE_BANDWIDTH * 111_320


def generate_traffic_data(n: int) -> pd.DataFrame:
    """
    Simulates raw GPS logs, clustering points around specific 'hotspots'
    to mimic real-world traffic congestion patterns.
    """
    np.random.seed(42)

    # Hotspot 1: High Density (50% of data)
    lat1 = np.random.normal(CENTER_LAT + 0.005, 0.002, int(n * 0.5))
    lon1 = np.random.normal(CENTER_LON - 0.008, 0.003, int(n * 0.5))

    # Hotspot 2: Medium Density (30% of data)
    lat2 = np.random.normal(CENTER_LAT - 0.01, 0.005, int(n * 0.3))
    lon2 = np.random.normal(CENTER_LON + 0.015, 0.006, int(n * 0.3))

    # Background Noise/Random Movement (20% of data)
    lat3 = np.random.normal(CENTER_LAT, 0.05, int(n * 0.2))
    lon3 = np.random.normal(CENTER_LON, 0.05, int(n * 0.2))

    lats = np.concatenate([lat1, lat2, lat3])
    lons = np.concatenate([lon1, lon2, lon3])

    frame = pd.DataFrame({'latitude': lats, 'longitude': lons})
    return frame


# --- 2. CORE KDE DENSITY CALCULATION ---

def calculate_kde_density(df: pd.DataFrame, bandwidth: float, resolution: int) -> tuple:
    """
    Performs Kernel Density Estimation over a defined grid covering the data bounds.
    Returns a list of [latitude, longitude, intensity] plus the peak cell.
    """
    # 2a. Prepare Data for Scipy KDE
    # Scipy's KDE expects the input data array to be transposed (M x N, where M=dimensions, N=samples)
    coords = np.vstack([df['longitude'], df['latitude']])

    # 2b. Initialize Gaussian KDE estimator.
    # `bw_method` is a multiplier on the data's covariance, so a bandwidth in degrees has to
    # be divided by the sample's own spread before it means degrees.
    spread = float(np.mean(coords.std(axis=1)))
    bw_factor = bandwidth / spread
    kde = gaussian_kde(coords, bw_method=bw_factor)

    # 2c. Define the Grid and Bounding Box
    lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
    lat_min, lat_max = df['latitude'].min(), df['latitude'].max()

    # Create linearly spaced arrays for the latitude and longitude axes
    lon_grid = np.linspace(lon_min, lon_max, resolution)
    lat_grid = np.linspace(lat_min, lat_max, resolution)

    # Create a 2D mesh grid (X, Y) from the 1D arrays
    X, Y = np.meshgrid(lon_grid, lat_grid)

    # 2d. Prepare Grid Coordinates for Evaluation
    # Flatten and stack the grid points into the format required by kde()
    grid_coords = np.vstack([X.ravel(), Y.ravel()])

    # 2e. Calculate Density (Z)
    # Evaluate the KDE function at every point on the generated grid
    Z = kde(grid_coords)

    # 2f. Structure Output for Folium.
    # leaflet-heat reads an intensity in 0..1, so the densities are rescaled against a cap:
    # everything at or above CAP_FRACTION of the peak saturates, which is the "cap the
    # maximum colour intensity" the book asks for and `max_val` no longer does.
    cap = float(Z.max()) * CAP_FRACTION
    intensities = np.minimum(Z / cap, 1.0)

    heatmap_data = []
    for lat, lon, density, intensity in zip(Y.ravel(), X.ravel(), Z, intensities):
        if density > 0.0: # Filter out areas with zero density
            heatmap_data.append([float(lat), float(lon), float(intensity)])

    peak = int(np.argmax(Z))
    return heatmap_data, (float(Y.ravel()[peak]), float(X.ravel()[peak])), {
        'points': len(df),
        'spread': spread,
        'bw_factor': bw_factor,
        'peak_density': float(Z.max()),
        'cap': cap,
        'saturated': int((intensities >= 1.0).sum()),
        'cells': int(resolution * resolution),
    }


# --- 3. INTERACTIVE VISUALIZATION ---

def visualize_heatmap(heatmap_data: list, center_lat: float, center_lon: float, output_file: pathlib.Path):
    """
    Renders the weighted density points onto an interactive Folium map.
    """
    # Initialize Folium map centered on the study area
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="cartodbpositron")

    # Add the HeatMap layer using the calculated density points
    HeatMap(heatmap_data,
            radius=18,          # Visual size of the hotspot circles
            blur=15,            # Smoothness of the transition between colors
            min_opacity=0.3,    # Ensure background areas are not fully transparent
            gradient={"0.2": 'blue', "0.5": 'lime', "0.8": 'orange', "1.0": 'red'} # Custom gradient
           ).add_to(m)

    # Save the interactive HTML file into the project's output folder
    output_file.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_file))
    return m


# --- 4. EXECUTION ---

def main() -> dict:
    print("--- GeoAI Advanced Traffic Density Analysis (KDE Grid Method) ---")

    # Step A: Data Acquisition (Simulated)
    raw_gps_data = generate_traffic_data(N_POINTS)
    print(f"1. Generated {len(raw_gps_data)} raw GPS points.")

    # Step B: Density Estimation
    heatmap_points, peak, stats = calculate_kde_density(
        raw_gps_data,
        bandwidth=KDE_BANDWIDTH,
        resolution=GRID_RESOLUTION
    )
    print(f"2. KDE calculated over a {GRID_RESOLUTION}x{GRID_RESOLUTION} grid.")
    print(f"3. Prepared {len(heatmap_points)} weighted grid points for visualization.")
    print(f"   Bandwidth {KDE_BANDWIDTH} degrees = {BANDWIDTH_METRES:.0f} m of latitude, "
          f"applied as bw_method={stats['bw_factor']:.4f} (scipy multiplies by the data's "
          f"{stats['spread']:.4f} degree spread).")
    print(f"   Peak density {stats['peak_density']:.3f} at "
          f"{peak[0]:.4f} N, {peak[1]:.4f} E; cap {stats['cap']:.3f}; "
          f"{stats['saturated']} cells saturate the colour scale.")

    # Step C: Visualization
    output_file = OUTPUT / "advanced_traffic_kde_heatmap.html"
    visualize_heatmap(heatmap_points, CENTER_LAT, CENTER_LON, output_file)
    print(f"\n[SUCCESS] Interactive heatmap saved to: "
          f"{output_file.relative_to(OUTPUT.parent)}")
    print(f"       Bytes: {output_file.stat().st_size}")

    return {
        'points': len(raw_gps_data),
        'grid_points': len(heatmap_points),
        'peak': peak,
        'output': output_file,
        **stats,
    }


if __name__ == "__main__":
    main()
