import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
from scipy.spatial import cKDTree
import time
import folium
from folium.plugins import HeatMap
import pathlib
import warnings

# --- Four corrections to the book's solution, and why ---
#
# 1. The Epanechnikov surface is calculated, not simulated. The book times the Gaussian
#    kernel and then sets `time_epanechnikov = time_gaussian * 0.95` because "scipy doesn't
#    easily expose kernel choice". A finite-support kernel needs no library: with a
#    `cKDTree` holding the points, a cell's density is the sum of the Epanechnikov weights
#    of the neighbours inside the bandwidth, and every cell outside that radius is exactly
#    zero. That difference in support is the exercise.
# 2. The layers use the same radius. The book gives one layer radius 8 and the other 6.4; a
#    reader comparing them would be comparing the radii, not the kernels. Both use 8, so the
#    only difference on the map is the density the two kernels produced.
# 3. `plt.show()` is not involved, but the map was never saved. It is written into the
#    project's output/ folder.
# 4. The data is seeded and the CartoDB warning is silenced for the build.
warnings.filterwarnings('ignore', message='CartoDB tiles now require an API key')

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

N_POINTS = 3000
GRID_RESOLUTION = 120
# Fixed bandwidth for both trials: 0.008 degrees of latitude, about 890 metres.
FIXED_BANDWIDTH = 0.008
CENTER_LAT, CENTER_LON = 34.0522, -118.2437

np.random.seed(42)


def write_noisy_feed(n=N_POINTS, path=None):
    """Three clusters of pings, plus the five per cent of rows a real feed carries."""
    lat = np.concatenate([
        np.random.normal(CENTER_LAT + 0.004, 0.004, int(n * 0.5)),
        np.random.normal(CENTER_LAT - 0.008, 0.006, int(n * 0.3)),
        np.random.normal(CENTER_LAT, 0.03, int(n * 0.2)),
    ])
    lon = np.concatenate([
        np.random.normal(CENTER_LON - 0.007, 0.005, int(n * 0.5)),
        np.random.normal(CENTER_LON + 0.012, 0.007, int(n * 0.3)),
        np.random.normal(CENTER_LON, 0.03, int(n * 0.2)),
    ])
    frame = pd.DataFrame({'latitude': lat, 'longitude': lon})
    noise = pd.DataFrame({
        'latitude': [0.0, np.nan, '34.05', 91.0, np.nan] * 30,
        'longitude': [-118.24, -118.24, '-118.24', -118.24, 0.0] * 30,
    })
    frame = pd.concat([frame, noise], ignore_index=True)
    path = path or (OUTPUT / 'noisy_trips.csv')
    frame.to_csv(path, index=False)
    return path


# Requirement 1 of the exercise is "load and clean the data as in exercise 1", so the feed
# is written to disk and read back through the same three gates, rather than generated in
# memory: the cleaning is part of what the kernels are given.
csv_path = write_noisy_feed()
df = pd.read_csv(csv_path)
raw_rows = len(df)

df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df.dropna(subset=['latitude', 'longitude'], inplace=True)
df = df[(df['latitude'] != 0.0) & (df['longitude'] != 0.0)]
df = df[(df['latitude'].between(-90, 90)) & (df['longitude'].between(-180, 180))]


def grid_for(frame, resolution):
    lon_grid = np.linspace(frame['longitude'].min(), frame['longitude'].max(), resolution)
    lat_grid = np.linspace(frame['latitude'].min(), frame['latitude'].max(), resolution)
    X, Y = np.meshgrid(lon_grid, lat_grid)
    return lon_grid, lat_grid, X, Y


def gaussian_surface(coords, X, Y, bandwidth, spread):
    """Density from scipy's Gaussian KDE, the book's kernel, and the time it takes."""
    start = time.perf_counter()
    kde = gaussian_kde(coords, bw_method=bandwidth / spread)
    Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)
    elapsed = time.perf_counter() - start
    return Z, elapsed


def epanechnikov_surface(coords, X, Y, bandwidth):
    """Density from the Epanechnikov kernel, which is zero beyond the bandwidth.

    In two dimensions the Epanechnikov kernel is K(u) = 2/pi * (1 - |u|^2) for |u| <= 1 and
    zero elsewhere, so f(x) = 1/(n h^2) * sum_i K((x - x_i) / h). A k-d tree returns only
    the neighbours inside h, which is why the support can be finite in practice.
    """
    start = time.perf_counter()
    points = np.column_stack([coords[0], coords[1]])
    tree = cKDTree(points)
    cells = np.column_stack([X.ravel(), Y.ravel()])
    neighbours = tree.query_ball_point(cells, r=bandwidth)
    Z = np.zeros(len(cells))
    n = len(points)
    for index, found in enumerate(neighbours):
        if not found:
            continue
        offsets = points[found] - cells[index]
        squared = (offsets ** 2).sum(axis=1) / bandwidth ** 2
        inside = squared < 1.0
        Z[index] = (2.0 / np.pi) * np.sum(1.0 - squared[inside]) / (n * bandwidth ** 2)
    elapsed = time.perf_counter() - start
    return Z.reshape(X.shape), elapsed, len(neighbours)


def main():
    frame = df.copy()
    coords = np.vstack([frame['longitude'].values, frame['latitude'].values])
    spread = float(np.mean(coords.std(axis=1)))
    lon_grid, lat_grid, X, Y = grid_for(frame, GRID_RESOLUTION)
    cell_area = (lon_grid[1] - lon_grid[0]) * (lat_grid[1] - lat_grid[0])

    print(f"--- {len(frame)} pings ({raw_rows} rows read, "
          f"{raw_rows - len(frame)} rejected), {GRID_RESOLUTION}x{GRID_RESOLUTION} grid ---")
    print(f"Fixed bandwidth: {FIXED_BANDWIDTH} degrees "
          f"({FIXED_BANDWIDTH * 111_320:.0f} m of latitude)")

    # 1 & 2. Gaussian kernel
    gaussian, time_gaussian = gaussian_surface(coords, X, Y, FIXED_BANDWIDTH, spread)

    # 3. Epanechnikov kernel
    epanechnikov, time_epanechnikov, touched = epanechnikov_surface(
        coords, X, Y, FIXED_BANDWIDTH)

    # 4. Comparative visualisation: both surfaces, normalised to their own peak so the
    # colours describe shape rather than units, on one map with two toggles.
    def heat_points(Z):
        peak = float(Z.max())
        return [[float(lat), float(lon), float(value / peak)]
                for lat, lon, value in zip(Y.ravel(), X.ravel(), Z.ravel())
                if value > 0.0]

    gaussian_points = heat_points(gaussian)
    epanechnikov_points = heat_points(epanechnikov)

    map_center = [float(frame['latitude'].mean()), float(frame['longitude'].mean())]
    m_comp = folium.Map(location=map_center, zoom_start=12, tiles='cartodbpositron')

    HeatMap(
        gaussian_points,
        name='Gaussian Kernel Density (Green/Yellow)',
        radius=8,
        blur=15,
        gradient={"0.4": "green", "0.8": "yellow"},
        min_opacity=0.3
    ).add_to(folium.FeatureGroup(name='Gaussian KDE').add_to(m_comp))

    HeatMap(
        epanechnikov_points,
        name='Alternative Kernel Density (Purple/Pink)',
        radius=8,
        blur=15,
        gradient={"0.4": "purple", "0.8": "pink"},
        min_opacity=0.3
    ).add_to(folium.FeatureGroup(name='Epanechnikov KDE').add_to(m_comp))

    folium.LayerControl().add_to(m_comp)
    output_file = OUTPUT / "kernel_comparison.html"
    m_comp.save(str(output_file))

    # 5. Performance and interpretation
    mass_gaussian = float(gaussian.sum() * cell_area)
    mass_epanechnikov = float(epanechnikov.sum() * cell_area)
    gaussian_peak = np.unravel_index(int(np.argmax(gaussian)), gaussian.shape)
    epanechnikov_peak = np.unravel_index(int(np.argmax(epanechnikov)), epanechnikov.shape)

    print("\n--- Kernel Performance Comparison ---")
    print(f"Gaussian Kernel Calculation Time: {time_gaussian:.4f} seconds")
    print(f"Alternative (Epanechnikov) Kernel Calculation Time: {time_epanechnikov:.4f} seconds")
    print(f"Ratio (Gaussian / Epanechnikov): {time_gaussian / time_epanechnikov:.1f}x")
    print("\n--- Surfaces ---")
    print(f"Gaussian:      peak {gaussian.max():.1f} at "
          f"{Y[gaussian_peak]:.4f} N, {X[gaussian_peak]:.4f} E; "
          f"zero cells {int((gaussian == 0).sum())}; mass {mass_gaussian:.3f}")
    print(f"Epanechnikov:  peak {epanechnikov.max():.1f} at "
          f"{Y[epanechnikov_peak]:.4f} N, {X[epanechnikov_peak]:.4f} E; "
          f"zero cells {int((epanechnikov == 0).sum())}; mass {mass_epanechnikov:.3f}")
    print(f"Cells with at least one neighbour inside the bandwidth: {touched} "
          f"of {GRID_RESOLUTION * GRID_RESOLUTION}")
    print(f"\n[SUCCESS] Interactive heatmap saved to: {output_file.relative_to(OUTPUT.parent)}")
    print(f"          Bytes: {output_file.stat().st_size}")

    print("\n--- Theoretical Interpretation ---")
    print("The Gaussian kernel assigns weight based on a normal distribution, meaning every "
          "point in the dataset contributes (albeit minimally) to the density estimate at "
          "every location. This 'infinite support' property leads to very smooth density "
          "surfaces but can be computationally expensive as all pairwise distances must be "
          "considered.")
    print("The Epanechnikov or Quartic kernels (finite support) assign zero weight to points "
          "outside the defined bandwidth (h). This property can lead to faster execution "
          "times, especially on large datasets, because the algorithm only needs to "
          "calculate distances for local neighbors, resulting in sharper, more localized "
          "hotspots.")

    return {
        'points': len(frame),
        'raw_rows': raw_rows,
        'spread': spread,
        'time_gaussian': time_gaussian,
        'time_epanechnikov': time_epanechnikov,
        'mass_gaussian': mass_gaussian,
        'mass_epanechnikov': mass_epanechnikov,
        'zero_cells': {'gaussian': int((gaussian == 0).sum()),
                       'epanechnikov': int((epanechnikov == 0).sum())},
        'peak': {'gaussian': [float(Y[gaussian_peak]), float(X[gaussian_peak])],
                 'epanechnikov': [float(Y[epanechnikov_peak]), float(X[epanechnikov_peak])]},
        'gaussian_points': len(gaussian_points),
        'epanechnikov_points': len(epanechnikov_points),
        'output': output_file,
    }


if __name__ == "__main__":
    main()
