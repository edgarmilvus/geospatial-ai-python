"""Exercise 1 — the foundational GeoAI dashboard.

One dropdown of model run ids, one map, one callback. Running the file builds
the application and writes its layout to `output/`; `--serve` is the branch that
listens.
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
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data Simulation ---
N_SAMPLES = 500
np.random.seed(42)
data = pd.DataFrame({
    'latitude': np.random.uniform(34.0, 34.5, N_SAMPLES),
    'longitude': np.random.uniform(-118.5, -118.0, N_SAMPLES),
    'classification_label': np.random.choice(['Forest', 'Water', 'Urban'], N_SAMPLES),
    'confidence_score': np.random.rand(N_SAMPLES),
    'model_run_id': np.random.choice(['v1.0_2023', 'v1.1_2024', 'v1.2_2024'], N_SAMPLES)
})

# --- 2. Application Initialization ---
app = dash.Dash(__name__)

# NOTE: Replace 'YOUR_MAPBOX_TOKEN' with a valid token for production use
# A Mapbox token is a deployment secret, so it is read from the environment and
# never written into the listing. The placeholder keeps the app buildable without
# one: the figures still lay out, the tiles simply do not load.
MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN", "pk.placeholder")
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

unique_model_ids = data['model_run_id'].unique()

# --- 3. Layout Definition ---
app.layout = html.Div([
    html.H1("GeoAI Model Comparison Dashboard"),

    html.Div([
        html.Label("Select Model Run ID:"),
        dcc.Dropdown(
            id='model-run-selector',
            options=[{'label': i, 'value': i} for i in unique_model_ids],
            value=unique_model_ids[0],  # Default value
            clearable=False
        )
    ], style={'width': '50%', 'padding': '10px'}),

    dcc.Graph(id='geoai-map-output', style={'height': '70vh'})
])

# --- 4. Callback Implementation ---
@app.callback(
    Output('geoai-map-output', 'figure'),
    [Input('model-run-selector', 'value')]
)
def update_map(selected_model_id):
    """Filters data based on model ID and generates a scatter_mapbox figure."""
    if selected_model_id is None:
        # Handle case where no model is selected (shouldn't happen with default value).
        # An empty frame keeps the columns, so the figure is a valid empty map.
        return px.scatter_mapbox(
            data.iloc[0:0], lat="latitude", lon="longitude",
            title="Select a model run to plot its detections.")

    filtered_df = data[data['model_run_id'] == selected_model_id]

    fig = px.scatter_mapbox(
        filtered_df,
        lat="latitude",
        lon="longitude",
        color="classification_label",
        zoom=10,
        height=600,
        mapbox_style="satellite-streets"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig


# --- 5. Build, report, and serve only when asked ---

def build_and_report(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from plotly.io.json import to_json_plotly

    counts = data['model_run_id'].value_counts().sort_index()
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(json.loads(to_json_plotly(app.layout)), indent=2) + "\n",
        encoding="utf-8")
    (output_dir / "model_run_summary.json").write_text(
        json.dumps({
            "rows": int(len(data)),
            "model_run_ids": unique_model_ids.tolist(),
            "rows_per_model_run": {str(k): int(v) for k, v in counts.items()},
            "labels": sorted(data['classification_label'].unique().tolist()),
            "default_model_run": str(unique_model_ids[0]),
        }, indent=2) + "\n", encoding="utf-8")

    print("--- GeoAI Model Comparison Dashboard ---")
    print(f"Detections: {len(data)}")
    for run_id, count in counts.items():
        print(f"  {run_id}: {count} detections")
    print(f"Classes: {', '.join(sorted(data['classification_label'].unique()))}")
    print(f"Dropdown opens on: {unique_model_ids[0]}")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and model_run_summary.json")
    print("Serve it for real with: python3 model_run_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        app.run(debug=False, port=8050)
    else:
        build_and_report()
