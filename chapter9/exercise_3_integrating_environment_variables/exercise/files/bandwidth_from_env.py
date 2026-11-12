import os
import pandas as pd
import numpy as np
import pathlib
import sys
from scipy.stats import gaussian_kde

# --- Four corrections to the book's solution, and why ---
#
# 1. The default path. `./data/default_traffic.csv` does not exist in this project and the
#    listing did not create it, so the "graceful default" branch raised FileNotFoundError
#    and called `exit()` - a silent SystemExit(0). The file is generated if it is missing,
#    which is what makes the default branch runnable at all.
# 2. The bandwidth is used. The book computes `dynamic_h` and then says "for demonstration
#    we simply show the calculated value": the KDE never sees it. It is now the bandwidth of
#    a real `gaussian_kde`, converted to scipy's factor units, and the grid it is evaluated
#    on is reported.
# 3. `exit()` is replaced by a `SystemExit` with a message: `exit()` is a helper added by the
#    `site` module, not part of the language, and it exits with status 0 - the code for
#    success.
# 4. The output paths are relative to the project, not to whatever directory the script was
#    started from.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

def shown(path):
    """The path as the reader should see it: relative to the project when it can be."""
    try:
        return path.relative_to(OUTPUT.parent)
    except ValueError:
        return path


# --- 1. Environment Variable Setup (Mock) ---
GEOAI_DATA_PATH = os.environ.get('GEOAI_DATA_PATH')
USING_DEFAULT = GEOAI_DATA_PATH is None

if USING_DEFAULT:
    # Defaulting to the local path if environment variable is not set
    data_path = OUTPUT / 'default_traffic.csv'
    print(f"WARNING: GEOAI_DATA_PATH environment variable not set. "
          f"Using default path: {shown(data_path)}")
else:
    data_path = pathlib.Path(GEOAI_DATA_PATH)
    print(f"Using data path from environment variable: {GEOAI_DATA_PATH}")

if not data_path.is_absolute():
    data_path = OUTPUT.parent / data_path
# The default feed is generated once, deterministically, so the default branch is
# runnable. A path somebody named in the environment is expected to exist: inventing data
# for a name the deployment chose would hide a misconfigured mount.
if USING_DEFAULT and not data_path.exists():
    rng = np.random.RandomState(42)
    n = 8000
    generated = pd.DataFrame({
        'latitude': rng.normal(34.05, 0.02, n),
        'longitude': rng.normal(-118.24, 0.02, n),
        'start_time': pd.date_range('2023-01-01', periods=n, freq='min'),
    })
    data_path.parent.mkdir(parents=True, exist_ok=True)
    generated.to_csv(data_path, index=False)


# --- 2. Dynamic Bandwidth Heuristic ---
def calculate_dynamic_bandwidth(N, scaling_constant=1.0):
    """
    Calculates the optimal bandwidth (h) based on the sample size N,
    using a rule of thumb often derived from Silverman's rule for
    non-parametric density estimation (h ∝ N^(-1/5)).

    The -1/5 exponent is generally optimal for Gaussian-kernel density
    estimation under the assumption of multivariate normal data.
    """
    if N <= 1:
        return 0.01

    # Simple scaling rule: h = C * N^(-1/5)
    # We use a constant C that relates to the standard deviation of the data
    # (or a fixed spatial extent multiplier)
    C = scaling_constant * 0.1 # Scaling constant chosen based on the coordinate range (~0.1 degrees)
    h = C * (N ** (-1/5))
    return h


# --- 3. Refactored Data Loading and Cleansing ---
try:
    df = pd.read_csv(data_path)
except FileNotFoundError:
    raise SystemExit(f"Error: Data file not found at {shown(data_path)}. "
                     f"Set GEOAI_DATA_PATH to an existing feed.")

# Clean data (as per Exercise 1)
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df.dropna(subset=['latitude', 'longitude'], inplace=True)
df = df[(df['latitude'] != 0.0) & (df['longitude'] != 0.0)]
df = df[(df['latitude'].between(-90, 90)) & (df['longitude'].between(-180, 180))]

N_valid = len(df)

# --- 4. KDE Execution ---
# Calculate the dynamic bandwidth
dynamic_h = calculate_dynamic_bandwidth(N_valid)

GRID_RESOLUTION = 120
peak = None
if N_valid > 1:
    coords = np.vstack([df['longitude'], df['latitude']])
    # scipy's `bw_method` is a multiplier on the sample's covariance, so the bandwidth in
    # degrees becomes a factor: dividing by the spread keeps h in degrees.
    spread = float(np.mean(coords.std(axis=1)))
    kde = gaussian_kde(coords, bw_method=dynamic_h / spread)

    lon_grid = np.linspace(df['longitude'].min(), df['longitude'].max(), GRID_RESOLUTION)
    lat_grid = np.linspace(df['latitude'].min(), df['latitude'].max(), GRID_RESOLUTION)
    X, Y = np.meshgrid(lon_grid, lat_grid)
    Z = kde(np.vstack([X.ravel(), Y.ravel()]))
    hottest = int(np.argmax(Z))
    peak = (float(Y.ravel()[hottest]), float(X.ravel()[hottest]))
    print(f"\nKDE evaluated on a {GRID_RESOLUTION}x{GRID_RESOLUTION} grid; "
          f"peak density {Z.max():.2f} at {peak[0]:.4f} N, {peak[1]:.4f} E.")
else:
    print("Insufficient data for KDE calculation.")


# --- 5. Output Log ---
print("\n--- Configuration Summary ---")
print(f"Final used file path: {shown(data_path)}")
print(f"Total valid data points (N): {N_valid}")
print(f"Calculated Dynamic Bandwidth (h): {dynamic_h:.6f} degrees")
print(f"Bandwidth applied as bw_method: {dynamic_h / spread:.4f} "
      f"(sample spread {spread:.4f} degrees)")
