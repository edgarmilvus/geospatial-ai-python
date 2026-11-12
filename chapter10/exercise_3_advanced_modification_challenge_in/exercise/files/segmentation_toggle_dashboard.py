"""Exercise 3 — toggle the same map between bounding-box points and segmentation
polygons.

Point mode is one `px.scatter_mapbox`; polygon mode builds a `go.Figure` whose
`layout.mapbox.layers` carry one GeoJSON source per object type. Running the file
writes the layout and the polygon counts; `--serve` listens.
"""
import json
import pathlib
import sys

import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data Simulation (GeoJSON Integration) ---
N_SAMPLES = 200
np.random.seed(43)

def create_geojson_polygon(lat, lon, size=0.001):
    """Simulates a small square polygon around a point."""
    coords = [
        [lon - size, lat - size],
        [lon + size, lat - size],
        [lon + size, lat + size],
        [lon - size, lat + size],
        [lon - size, lat - size]
    ]
    geojson = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [coords]},
        "properties": {}
    }
    return json.dumps(geojson)

# The coordinates are drawn once. Building the polygons from a second draw, as the
# first draft did, puts every mask somewhere other than the point it belongs to.
latitude = np.random.uniform(34.0, 34.5, N_SAMPLES)
longitude = np.random.uniform(-118.5, -118.0, N_SAMPLES)

data_ex3 = pd.DataFrame({
    'latitude': latitude,
    'longitude': longitude,
    'object_type': np.random.choice(['building', 'road', 'water'], N_SAMPLES),
    'model_run_id': np.random.choice(['v1.2_2024'], N_SAMPLES),
    'segmentation_geojson': [
        create_geojson_polygon(lat, lon)
        if i % 3 != 0 else None  # Only 2/3 of data have segmentation
        for i, (lat, lon) in enumerate(zip(latitude, longitude))
    ]
})

app = dash.Dash(__name__)
# A Mapbox token is a deployment secret, so it is read from the environment and
# never written into the listing. The placeholder keeps the app buildable without
# one: the figures still lay out, the tiles simply do not load.
MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN", "pk.placeholder")
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

# Color mapping for GeoJSON polygons
COLOR_MAP = {'building': 'rgba(255, 0, 0, 0.5)', 'road': 'rgba(0, 255, 0, 0.5)', 'water': 'rgba(0, 0, 255, 0.5)'}

# --- 2. New Input Component and Layout ---
app.layout = html.Div([
    html.H1("GeoAI Segmentation Visualization Toggle"),

    html.Div([
        html.Label("Visualization Mode:"),
        dcc.Checklist(
            id='visualization-mode-toggle',
            options=[
                {'label': ' Show Points', 'value': 'points'},
                {'label': ' Show Polygons', 'value': 'polygons'}
            ],
            value=['points'], # Default to points
            inline=True
        )
    ], style={'padding': '10px'}),

    dcc.Graph(id='geoai-map-output', style={'height': '70vh'})
])

# --- 3. Conditional Rendering Callback ---
@app.callback(
    Output('geoai-map-output', 'figure'),
    [Input('visualization-mode-toggle', 'value')]
)
def update_map_mode(mode_list):

    if not mode_list or 'points' in mode_list:
        # --- Mode 1: Scatter Mapbox (Points) ---
        fig = px.scatter_mapbox(
            data_ex3,
            lat="latitude",
            lon="longitude",
            color="object_type",
            zoom=10,
            height=600,
            title="Point Detections (Bounding Box Centers)",
            mapbox_style="satellite-streets"
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        return fig

    elif 'polygons' in mode_list:
        # --- Mode 2: Mapbox Layers (Polygons) ---
        polygon_df = data_ex3[data_ex3['segmentation_geojson'].notna()]

        if polygon_df.empty:
            return go.Figure().update_layout(title="No segmentation data available.")

        # Aggregate GeoJSON features by object type
        layers = []
        for obj_type, color_rgba in COLOR_MAP.items():
            type_data = polygon_df[polygon_df['object_type'] == obj_type]

            # Create a FeatureCollection for the current object type
            features = [json.loads(g) for g in type_data['segmentation_geojson']]
            feature_collection = {"type": "FeatureCollection", "features": features}

            if features:
                layers.append(dict(
                    sourcetype='geojson',
                    source=feature_collection,
                    type='fill',
                    color=color_rgba,
                    opacity=0.7,
                    name=obj_type
                ))

        # Determine center point for initial map view
        center_lat = polygon_df['latitude'].mean()
        center_lon = polygon_df['longitude'].mean()

        fig = go.Figure(
            layout=go.Layout(
                mapbox=dict(
                    style="satellite-streets",
                    center=dict(lat=center_lat, lon=center_lon),
                    zoom=10,
                    layers=layers
                ),
                height=600,
                margin={"r":0,"t":40,"l":0,"b":0},
                title="Segmentation Mask Visualization (Polygons)"
            )
        )
        return fig

    # Default fallback
    return go.Figure()


# --- 4. Build, report, and serve only when asked ---

def build_and_report(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from plotly.io.json import to_json_plotly

    with_polygon = data_ex3['segmentation_geojson'].notna()
    by_type = (data_ex3[with_polygon].groupby('object_type').size()
               .reindex(sorted(COLOR_MAP), fill_value=0))
    summary = {
        "rows": int(len(data_ex3)),
        "with_segmentation": int(with_polygon.sum()),
        "without_segmentation": int((~with_polygon).sum()),
        "polygons_by_type": {str(k): int(v) for k, v in by_type.items()},
        "colors": COLOR_MAP,
        "modes": ["points", "polygons"],
        "default_mode": "points",
    }
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(json.loads(to_json_plotly(app.layout)), indent=2) + "\n",
        encoding="utf-8")
    (output_dir / "segmentation_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("--- GeoAI Segmentation Visualization Toggle ---")
    print(f"Detections: {summary['rows']}; with a mask: {summary['with_segmentation']}")
    for obj_type, count in by_type.items():
        print(f"  {obj_type:<8}: {count} polygons ({COLOR_MAP[obj_type]})")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and segmentation_summary.json")
    print("Serve it for real with: python3 segmentation_toggle_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        app.run(debug=False, port=8050)
    else:
        build_and_report()
