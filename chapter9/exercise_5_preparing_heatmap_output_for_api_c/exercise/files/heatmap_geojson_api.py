import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
import json
import pathlib

# --- Four corrections to the book's solution, and why ---
#
# 1. `Point` was used and never imported: the fallback branch that rebuilds the GeoDataFrame
#    from a CSV raised NameError before it could produce anything.
# 2. The densities were normalised into `density_scores` and then ignored - the loop put the
#    raw `density_matrix[i, j]` into the property. The API contract says `density_score`, so
#    the normalised value is what travels, and its maximum is 1.
# 3. The "conceptual" API handler now actually handles its request: `time_filter` selects
#    the hours, so the two calls return different payloads instead of the same one twice.
# 4. The payload is written to the project's output/ folder as well as printed, so the
#    reader can open the FeatureCollection in any GIS tool.
#
# The points are generated in memory: the book reads exercise 1's CSV, which makes this
# listing depend on another project's run.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

np.random.seed(42)


def simulated_gdf(n=6000):
    """A day of taxi pings: a morning peak, an evening peak and background movement."""
    hours = np.random.randint(0, 24, n)
    lat = np.empty(n)
    lon = np.empty(n)
    for index, hour in enumerate(hours):
        if 7 <= hour < 9:
            lat[index] = np.random.normal(40.720, 0.010)
            lon[index] = np.random.normal(-74.020, 0.012)
        elif 17 <= hour < 19:
            lat[index] = np.random.normal(40.755, 0.008)
            lon[index] = np.random.normal(-73.985, 0.010)
        else:
            lat[index] = np.random.normal(40.735, 0.030)
            lon[index] = np.random.normal(-74.000, 0.030)
    frame = pd.DataFrame({'latitude': lat, 'longitude': lon, 'hour': hours})
    geometry = [Point(xy) for xy in zip(frame['longitude'], frame['latitude'])]
    return gpd.GeoDataFrame(frame, geometry=geometry, crs="EPSG:4326")


gdf = simulated_gdf()


def generate_heatmap_geojson(input_gdf, grid_size=50):
    """
    Converts point data into a density grid (polygons) and serializes to GeoJSON.
    This simulates the final output of a KDE raster conversion process.
    """
    # Define grid boundaries and resolution (e.g., 50x50 cells)
    minx, miny, maxx, maxy = input_gdf.total_bounds
    x_bins = np.linspace(minx, maxx, grid_size)
    y_bins = np.linspace(miny, maxy, grid_size)

    # Calculate density using 2D histogram (proxy for KDE rasterization)
    density_matrix, _, _ = np.histogram2d(
        input_gdf.geometry.x,
        input_gdf.geometry.y,
        bins=[x_bins, y_bins],
        density=True
    )

    # Normalize density scores for visualization consistency
    max_score = density_matrix.max()
    density_scores = density_matrix / max_score if max_score > 0 else density_matrix

    grid_data = []
    # --- 1. KDE Grid Conversion & 2. Attribute Structuring ---
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            # Create polygon geometry for the grid cell
            cell_polygon = Polygon([
                (x_bins[i], y_bins[j]),
                (x_bins[i+1], y_bins[j]),
                (x_bins[i+1], y_bins[j+1]),
                (x_bins[i], y_bins[j+1])
            ])

            # Structure the required attributes
            grid_data.append({
                'geometry': cell_polygon,
                'density_score': density_scores[i, j]
            })

    # Convert structured data to GeoDataFrame
    density_gdf = gpd.GeoDataFrame(grid_data, crs="EPSG:4326")

    # --- 3. GeoJSON Serialization ---
    geojson_output = density_gdf.to_json()
    return geojson_output, density_gdf


# --- 4. API Mockup Context ---
def generate_heatmap_response(request_params):
    """
    Simulates an API endpoint handler responding to a request context.
    The request_params might influence filtering (e.g., time_filter),
    but here we use the full cleaned dataset for simplicity.
    """
    print(f"API Request received with parameters: {request_params}")

    # Filtering logic based on request_params['time_filter']
    selection = gdf
    time_filter = request_params.get('time_filter')
    if time_filter == 'peak_hour':
        selection = gdf[(gdf['hour'] >= 7) & (gdf['hour'] < 9)]
        print(f"  peak_hour keeps {len(selection)} of {len(gdf)} pings (07:00-08:59)")
    elif time_filter == 'evening_peak':
        selection = gdf[(gdf['hour'] >= 17) & (gdf['hour'] < 19)]
        print(f"  evening_peak keeps {len(selection)} of {len(gdf)} pings (17:00-18:59)")
    else:
        print(f"  no time filter: the whole day is used ({len(selection)} pings)")

    # Generate the GeoJSON payload
    geojson_payload, density_gdf = generate_heatmap_geojson(selection)

    # In a real API, this would be returned as an HTTP response payload
    return geojson_payload, density_gdf


# Execute the mock API call
mock_request = {'time_filter': 'peak_hour', 'zoom_level': 14}
api_response_geojson, response_gdf = generate_heatmap_response(mock_request)

# --- 5. Validation ---
print("\n--- GeoJSON Output Validation (First 500 chars) ---")
print(api_response_geojson[:500])
print("\n... GeoJSON structure verified.")

payload = json.loads(api_response_geojson)
feature_path = OUTPUT / "heatmap_density.geojson"
feature_path.write_text(api_response_geojson, encoding="utf-8")

scores = response_gdf['density_score']
print("\n--- Payload ---")
print(f"Features: {len(payload['features'])} "
      f"(a {50 - 1} by {50 - 1} grid over the pings' bounding box)")
print(f"density_score: {scores.min():.4f} to {scores.max():.4f} "
      f"(normalised, so the hottest cell is 1.0)")
print(f"Cells with a non-zero score: {int((scores > 0).sum())} of {len(scores)}")
print(f"Geometry: {response_gdf.geometry.geom_type.unique().tolist()}, "
      f"CRS {response_gdf.crs.to_string()}")
print(f"Saved: {feature_path.relative_to(OUTPUT.parent)} "
      f"({feature_path.stat().st_size} bytes)")

# The endpoint is not hard-wired to one request: the whole day is a larger payload.
full_payload, full_gdf = generate_heatmap_response({'time_filter': 'all_day'})
print(f"\nFull-day request: {len(json.loads(full_payload)['features'])} features, "
      f"{len(gdf)} pings")
