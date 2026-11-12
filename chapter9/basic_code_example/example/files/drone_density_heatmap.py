import folium
from folium.plugins import HeatMap
import pathlib
import random
import warnings
import numpy as np

# --- Three corrections to the book's script, and why ---
#
# 1. The data is seeded. `random.random()` and `np.random.normal()` without a seed draw a
#    different 500 points on every run, so the map - and every number below it - changes
#    each time the listing is executed.
# 2. The output file went into whatever directory the script was started from. It goes to
#    the project's own output/ folder instead, which is where every artefact here lives.
# 3. Folium 0.19 warns that the built-in CartoDB tile names now need an API key. Nothing is
#    fetched while the file is built - the reader's browser loads the tiles - so the build
#    stays quiet and the warning is not hidden from the reader's browser.
warnings.filterwarnings('ignore', message='CartoDB tiles now require an API key')

random.seed(42)
np.random.seed(42)

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- 1. Configuration and Context Setting ---
# Define the central coordinates for the simulated urban area (Los Angeles)
CENTER_LAT, CENTER_LON = 34.0522, -118.2437
# Total number of simulated drone sightings
NUM_POINTS = 500
# Output file name for the generated interactive map
OUTPUT_FILE = "basic_drone_density_map.html"

# --- 2. Synthetic Data Generation (Simulation of Raw GPS Logs) ---
# We create 500 random points, intentionally clustering 70% in one area
# and 30% in a secondary area to ensure density variation is visible.
data_points = []
cluster_counts = [0, 0]
for i in range(NUM_POINTS):
    # Decision logic: 70% chance to belong to Cluster 1 (Main Downtown)
    if random.random() < 0.7:
        # Cluster 1: Tightly centered around the main coordinates
        # np.random.normal(mean, standard_deviation) generates realistic noise
        lat = CENTER_LAT + np.random.normal(0, 0.01)
        lon = CENTER_LON + np.random.normal(0, 0.015)
        cluster_counts[0] += 1

    # 30% chance to belong to Cluster 2 (Suburban Outpost)
    else:
        # Cluster 2: Offset significantly from the main center
        lat = CENTER_LAT + 0.05 + np.random.normal(0, 0.005)
        lon = CENTER_LON - 0.03 + np.random.normal(0, 0.01)
        cluster_counts[1] += 1

    # Append the coordinate pair [latitude, longitude] to the main list
    # The Folium HeatMap plugin expects data in this format: [lat, lon] or [lat, lon, intensity]
    data_points.append([lat, lon])

# --- 3. Map Initialization ---
# Create a base map object centered on the study area.
# 'tiles' defines the visual style of the base layer (CartoDB Positron is light and clear)
m = folium.Map(
    location=[CENTER_LAT, CENTER_LON],
    zoom_start=12,
    tiles="cartodbpositron"
)

# --- 4. HeatMap Layer Creation and Addition ---
# The HeatMap constructor processes the raw point data (data_points)
# and calculates the underlying spatial density (KDE).
density_layer = HeatMap(data_points)

# Attach the calculated density visualization layer to the map object 'm'.
density_layer.add_to(m)

# --- 5. Output Generation ---
# Save the resulting interactive map as a standalone HTML file.
output_file = OUTPUT / OUTPUT_FILE
m.save(str(output_file))

# --- 6. Report what the map is made of ---
lats = [point[0] for point in data_points]
lons = [point[1] for point in data_points]
print(f"Sightings: {len(data_points)} around {CENTER_LAT} N, {CENTER_LON} E")
print(f"Downtown cluster: {cluster_counts[0]} points; "
      f"suburban outpost: {cluster_counts[1]} points")
print(f"Latitude span: {min(lats):.4f} to {max(lats):.4f}")
print(f"Longitude span: {min(lons):.4f} to {max(lons):.4f}")
print(f"First three pairs [lat, lon]: "
      f"{[[round(value, 4) for value in point] for point in data_points[:3]]}")

print(f"\nSuccess: Interactive heatmap saved to {output_file.relative_to(OUTPUT.parent)}")
print(f"Bytes: {output_file.stat().st_size}")
print("Open the HTML file in a web browser to analyze drone traffic density.")
