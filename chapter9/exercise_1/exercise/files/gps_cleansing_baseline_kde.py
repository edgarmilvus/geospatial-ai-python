import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pathlib
import warnings

# --- Three corrections to the book's solution, and why ---
#
# 1. The CSV. The book writes `raw_gps_logs.csv` into the current directory and reads it
#    back from there, so the listing only works if it was started in the right place. It
#    now writes and reads the file in the project's own output/ folder.
# 2. `bw_adjust=H_BANDWIDTH * 200`. `bw_adjust` is a *multiplier* on seaborn's own
#    reference bandwidth, not a bandwidth in degrees: the value 1.0 is what 0.005 * 200
#    happens to equal, and changing the constant would have changed nothing but a number in
#    a comment. The multiplier is now derived from the target bandwidth and the sample's
#    own spread, so the 0.005 degrees is real, and both numbers are printed.
# 3. `plt.show()` becomes a PNG in output/, because a script has no window.
#
# The coordinates are a city-sized box, so geopandas' warnings about a geographic CRS are
# about geometry, not about this file's arithmetic.

warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- 1. Mock Data Generation (Necessary setup for the exercise) ---
# Create a mock CSV file simulating large, noisy GPS logs
N_POINTS = 50000
np.random.seed(42)
data = {
    'latitude': np.concatenate([
        np.random.uniform(40.6, 40.8, int(N_POINTS * 0.95)),
        np.random.choice([0.0, np.nan, '40.9'], int(N_POINTS * 0.05)) # Noise
    ]),
    'longitude': np.concatenate([
        np.random.uniform(-74.05, -73.9, int(N_POINTS * 0.95)),
        np.random.choice([0.0, np.nan, '-73.8'], int(N_POINTS * 0.05)) # Noise
    ]),
    'start_time': pd.to_datetime(pd.date_range('2023-01-01', periods=N_POINTS, freq='min'))
}
raw_df = pd.DataFrame(data)
csv_path = OUTPUT / 'raw_gps_logs.csv'
raw_df.to_csv(csv_path, index=False)

# --- 2. Data Ingestion and Initial Filtering ---
df = pd.read_csv(csv_path)

# Convert potential string coordinates to numeric, coercing errors to NaN
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
COERCED = int(df[['latitude', 'longitude']].isna().any(axis=1).sum())

# Filter 1: Remove NaNs
df.dropna(subset=['latitude', 'longitude'], inplace=True)

# Filter 2: Remove zero coordinates (faulty sensor readings)
df = df[(df['latitude'] != 0.0) & (df['longitude'] != 0.0)]

# Filter 3: Remove outliers (standard geographical bounds)
df = df[
    (df['latitude'].between(-90, 90)) &
    (df['longitude'].between(-180, 180))
]

# --- 3. Data Type Enforcement ---
# CRITICAL: Geometric calculations require high-precision floating-point numbers.
# Keeping them as generic objects or lower-precision types can lead to
# spatial indexing errors or loss of precision in distance calculations.
df['latitude'] = df['latitude'].astype('float64')
df['longitude'] = df['longitude'].astype('float64')

print(f"Cleaned records: {len(df)}")

# --- 4. Spatial Conversion ---
geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# --- 5. KDE Calculation and Static Visualization ---
# We use seaborn/matplotlib for static visualization of the density distribution.
# Bandwidth (h): Chosen as 0.005 degrees, roughly 500 meters, appropriate for city scale.
H_BANDWIDTH = 0.005
# seaborn's reference bandwidth is the sample's standard deviation times n^(-1/6); the
# multiplier that turns it into H_BANDWIDTH degrees is the ratio of the two.
REFERENCE_BANDWIDTH = float(gdf['latitude'].std() * len(gdf) ** (-1 / 6))
BW_ADJUST = H_BANDWIDTH / REFERENCE_BANDWIDTH

plt.figure(figsize=(10, 10))
# Use seaborn's kdeplot for efficient 2D density estimation and plotting
sns.kdeplot(
    x=gdf.geometry.x,
    y=gdf.geometry.y,
    cmap="plasma",
    fill=True,
    alpha=0.6,
    levels=15,
    bw_adjust=BW_ADJUST
)

plt.title("Baseline Geospatial Density Map (KDE)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
figure_path = OUTPUT / "gps_density_baseline.png"
plt.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close()

# --- 6. Report the pipeline, stage by stage ---
print(f"--- Cleaning ---")
print(f"Rows written to {csv_path.relative_to(OUTPUT.parent)}: {len(raw_df)}")
print(f"Rows whose coordinates would not parse (zero, null or text): {COERCED}")
print(f"Rows left after dropping nulls, zeros and out-of-range values: {len(df)}")
print(f"Removed: {len(raw_df) - len(df)} rows "
      f"({(len(raw_df) - len(df)) / len(raw_df) * 100:.2f} %)")
print(f"Latitude: {gdf['latitude'].min():.4f} to {gdf['latitude'].max():.4f}")
print(f"Longitude: {gdf['longitude'].min():.4f} to {gdf['longitude'].max():.4f}")
print(f"CRS: {gdf.crs.to_string()}; points: {len(gdf)}")

print(f"\n--- Density ---")
print(f"Target bandwidth: {H_BANDWIDTH} degrees (about {H_BANDWIDTH * 111_320:.0f} m)")
print(f"seaborn reference bandwidth: {REFERENCE_BANDWIDTH:.4f} degrees; "
      f"bw_adjust = {BW_ADJUST:.3f}")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")
