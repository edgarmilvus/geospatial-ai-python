import folium
from folium.plugins import HeatMap
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import pathlib
import warnings
import numpy as np

# --- Four corrections to the book's solution, and why ---
#
# 1. The data. The book's segmentation reads `raw_gps_logs.csv` from exercise 1 and its
#    timestamps are a uniform minute-by-minute range, so the morning and mid-day windows
#    contain the same spatial distribution and the comparison the exercise asks for has
#    nothing to show. The generator below draws each ping's hour first and places it
#    accordingly: rush-hour pings cluster over the residential district, mid-day pings over
#    the central business district, everything else is background. The two windows then
#    differ by about 0.035 degrees in both axes, which is the shift the map is meant to show.
# 2. `max_opacity=0.7` does nothing. leaflet-heat's options are minOpacity, maxZoom, radius,
#    blur and gradient; folium passes unknown keywords through and the browser ignores them.
#    The 0.7 is applied where opacity actually lives - in the rgba stops of the gradient.
# 3. The map was never saved: `m.save(...)` is commented out and the listing only prints
#    that the object exists. It is written into the project's output/ folder.
# 4. The data is seeded, and the CartoDB tile key warning is silenced for the build.
warnings.filterwarnings('ignore', message='CartoDB tiles now require an API key')

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

N_PINGS = 20000
HEATMAP_RADIUS = 15  # Consistent smoothing parameter for both windows
CENTRE = (40.73, -74.0)

# --- 0. Build the logs: one ping per row, an hour and a place that depends on it ---
hours = np.random.randint(0, 24, N_PINGS)
days = np.random.randint(0, 28, N_PINGS)
lats = np.empty(N_PINGS)
lons = np.empty(N_PINGS)
for index, hour in enumerate(hours):
    if 7 <= hour < 9:
        # Morning peak: the residential district, north-west of the centre.
        lats[index] = np.random.normal(40.720, 0.008)
        lons[index] = np.random.normal(-74.020, 0.010)
    elif 11 <= hour < 13:
        # Mid-day: the central business district.
        lats[index] = np.random.normal(40.755, 0.006)
        lons[index] = np.random.normal(-73.985, 0.008)
    else:
        # The rest of the day: a broad city-wide background.
        lats[index] = np.random.normal(CENTRE[0], 0.030)
        lons[index] = np.random.normal(CENTRE[1], 0.030)

start_times = (pd.Timestamp('2023-03-06')
               + pd.to_timedelta(days, unit='D')
               + pd.to_timedelta(hours, unit='h'))
df = pd.DataFrame({'latitude': lats, 'longitude': lons, 'start_time': start_times})

geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

gdf['start_time'] = pd.to_datetime(gdf['start_time'])

# --- 1. Temporal Segmentation ---
# Morning Peak: 7:00 AM to 9:00 AM
morning_peak_gdf = gdf[
    (gdf['start_time'].dt.hour >= 7) & (gdf['start_time'].dt.hour < 9)
]

# Mid-Day: 11:00 AM to 1:00 PM (13:00)
mid_day_gdf = gdf[
    (gdf['start_time'].dt.hour >= 11) & (gdf['start_time'].dt.hour < 13)
]

# Prepare data for Folium HeatMap (list of [lat, lon] tuples)
# Note: Folium HeatMap implicitly performs density calculation (KDE-like smoothing)
def prepare_heatmap_data(data_frame):
    return [[row.geometry.y, row.geometry.x] for row in data_frame.itertuples()]

morning_data = prepare_heatmap_data(morning_peak_gdf)
mid_day_data = prepare_heatmap_data(mid_day_gdf)

# --- 2. Dual KDE Calculation (Handled by Folium HeatMap plugin) ---
# Bandwidth/Radius consistency is maintained by setting the same 'radius' parameter.
# leaflet-heat has no "maxOpacity"; the 0.7 of the requirement is carried by the rgba
# stops, which is the only place the browser will honour an alpha.
MORNING_GRADIENT = {"0.4": "rgba(255,165,0,0.7)", "0.6": "rgba(139,0,0,0.7)",
                    "0.9": "rgba(255,0,0,0.7)"}
MIDDAY_GRADIENT = {"0.4": "rgba(0,255,255,0.7)", "0.6": "rgba(0,0,255,0.7)",
                   "0.9": "rgba(0,0,139,0.7)"}

# --- 3. Interactive Map Initialization ---
# Centered near NYC mock data centroid
map_center = [40.7, -73.97]
m = folium.Map(
    location=map_center,
    zoom_start=12,
    tiles='CartoDB dark_matter' # High-contrast tile set
)

# --- 4. Layer Overlay and Styling ---

# Morning Peak Layer (Red/Orange)
morning_layer = HeatMap(
    morning_data,
    name='Morning Peak Density (7-9 AM)',
    radius=HEATMAP_RADIUS,
    min_opacity=0.2,
    gradient=MORNING_GRADIENT # Distinct color palette
)
morning_layer.add_to(folium.FeatureGroup(name='Morning Peak Density (7-9 AM)').add_to(m))

# Mid-Day Layer (Blue/Cyan)
midday_layer = HeatMap(
    mid_day_data,
    name='Mid-Day Density (11 AM-1 PM)',
    radius=HEATMAP_RADIUS,
    min_opacity=0.2,
    gradient=MIDDAY_GRADIENT # Distinct color palette
)
midday_layer.add_to(folium.FeatureGroup(name='Mid-Day Density (11 AM-1 PM)').add_to(m))

# --- 5. Layer Control Implementation ---
folium.LayerControl().add_to(m)

# Save the map to an HTML file for interactive viewing
output_file = OUTPUT / "dynamic_density_map.html"
m.save(str(output_file))

# --- 6. Report the shift the two windows are meant to show ---
def centroid(data):
    latitudes = [point[0] for point in data]
    longitudes = [point[1] for point in data]
    return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

morning_centre = centroid(morning_data)
midday_centre = centroid(mid_day_data)

print(f"--- {len(gdf)} pings over 28 days ---")
print(f"Morning peak (07:00-08:59): {len(morning_data)} pings, "
      f"centre {morning_centre[0]:.4f} N, {morning_centre[1]:.4f} E")
print(f"Mid-day (11:00-12:59):      {len(mid_day_data)} pings, "
      f"centre {midday_centre[0]:.4f} N, {midday_centre[1]:.4f} E")
print(f"Shift between the windows:  {midday_centre[0] - morning_centre[0]:+.4f} latitude, "
      f"{midday_centre[1] - morning_centre[1]:+.4f} longitude")
print(f"Radius for both layers: {HEATMAP_RADIUS} pixels")
print(f"\nInteractive map generated successfully: "
      f"{output_file.relative_to(OUTPUT.parent)}")
print(f"Bytes: {output_file.stat().st_size}")
