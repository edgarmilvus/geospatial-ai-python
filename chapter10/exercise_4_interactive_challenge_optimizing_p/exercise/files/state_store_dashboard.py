"""Exercise 4 — split the dashboard into a filtering stage and a rendering stage.

Stage 1 reads the serialised raw data from a `dcc.Store` passed as `State`, filters
it against the controls and writes a smaller `filtered-data-store`. Stage 2 reads
only that store, so moving a slider never re-sends the 100 000 rows. Running the
file builds the app and writes its layout; `--serve` listens.
"""
import base64
import io
import json
import pathlib
import sys

import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data Simulation (Large Scale) ---
N_SAMPLES_LARGE = 100000 # Simulate a large dataset for performance testing
np.random.seed(44)
large_data = pd.DataFrame({
    'latitude': np.random.uniform(34.0, 34.5, N_SAMPLES_LARGE),
    'longitude': np.random.uniform(-118.5, -118.0, N_SAMPLES_LARGE),
    'classification_label': np.random.choice(['A', 'B', 'C', 'D'], N_SAMPLES_LARGE),
    'confidence_score': np.random.uniform(0.0, 1.0, N_SAMPLES_LARGE),
    'model_run_id': np.random.choice(['v_prod', 'v_test'], N_SAMPLES_LARGE)
})

# Function to serialize DataFrame (using JSON for simplicity, though feather/parquet is often better)
def serialize_df(df):
    return df.to_json(date_format='iso', orient='split')

# Function to deserialize DataFrame
def deserialize_df(json_data):
    # StringIO keeps pandas from treating the payload as a path or a URL.
    return pd.read_json(io.StringIO(json_data), orient='split')

# Initial serialization of the raw data (happens once at startup)
INITIAL_RAW_DATA = serialize_df(large_data)

# --- 2. Application Initialization and Layout ---
app = dash.Dash(__name__)
# A Mapbox token is a deployment secret, so it is read from the environment and
# never written into the listing. The placeholder keeps the app buildable without
# one: the figures still lay out, the tiles simply do not load.
MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN", "pk.placeholder")
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

unique_model_ids = large_data['model_run_id'].unique()

app.layout = html.Div([
    html.H1("Performance Optimized Dashboard (100K Detections)"),

    # Hidden storage for raw data (loaded only once)
    dcc.Store(id='raw-data-store', data=INITIAL_RAW_DATA),
    # Hidden storage for filtered data (updated by Stage 1)
    dcc.Store(id='filtered-data-store'),

    html.Div([
        html.Div([
            html.Label("Model Run ID:"),
            dcc.Dropdown(
                id='model-run-selector',
                options=[{'label': i, 'value': i} for i in unique_model_ids],
                value=unique_model_ids[0],
                clearable=False
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Confidence Score Range:"),
            dcc.RangeSlider(
                id='confidence-slider',
                min=0.0, max=1.0, step=0.05,
                value=[0.8, 1.0],
                marks={i/10: f'{i/10:.1f}' for i in range(0, 11, 2)}
            )
        ], style={'width': '60%', 'display': 'inline-block', 'padding': '10px'}),
    ]),

    html.Div([
        dcc.Graph(id='geoai-map-output', style={'width': '60%', 'display': 'inline-block', 'height': '60vh'}),
        dcc.Graph(id='confidence-histogram', style={'width': '40%', 'display': 'inline-block', 'height': '60vh'})
    ])
])

# --- Stage 1 Callback: Filtering Logic (Heavy Lifting) ---
@app.callback(
    Output('filtered-data-store', 'data'),
    [Input('model-run-selector', 'value'),
     Input('confidence-slider', 'value')],
    [State('raw-data-store', 'data')]
)
def filter_data_and_store(selected_model_id, confidence_range, raw_json_data):
    """Filters the raw data based on user inputs and stores the result."""

    # 1. Deserialize the full dataset (State)
    df_raw = deserialize_df(raw_json_data)

    # 2. Perform heavy filtering
    min_conf, max_conf = confidence_range

    df_filtered = df_raw[
        (df_raw['model_run_id'] == selected_model_id) &
        (df_raw['confidence_score'] >= min_conf) &
        (df_raw['confidence_score'] <= max_conf)
    ]

    # 3. Serialize and return the filtered subset (Output)
    return serialize_df(df_filtered)

# --- Stage 2 Callback: Visualization Rendering (Light Lifting) ---
@app.callback(
    [Output('geoai-map-output', 'figure'),
     Output('confidence-histogram', 'figure')],
    [Input('filtered-data-store', 'data')]
)
def render_visualizations(filtered_json_data):
    """Reads the pre-filtered data and generates figures quickly."""

    if filtered_json_data is None:
        empty = large_data.iloc[0:0]
        return (px.scatter_mapbox(empty, lat="latitude", lon="longitude",
                                  title="Loading..."),
                px.histogram(empty, x="confidence_score", title="Loading..."))

    # 1. Deserialize the filtered dataset (Input)
    df_filtered = deserialize_df(filtered_json_data)

    if df_filtered.empty:
        empty_map = px.scatter_mapbox(
            df_filtered, lat="latitude", lon="longitude",
            title="No data matching filter criteria.")
        empty_hist = px.histogram(df_filtered, x="confidence_score",
                                  title="No data matching filter criteria.")
        return empty_map, empty_hist

    # 2. Generate Map
    map_fig = px.scatter_mapbox(
        df_filtered,
        lat="latitude",
        lon="longitude",
        color="classification_label",
        zoom=10,
        height=600,
        mapbox_style="satellite-streets"
    )
    map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # 3. Generate Histogram (using the already filtered data)
    hist_fig = px.histogram(
        df_filtered,
        x="confidence_score",
        title="Confidence Distribution (Filtered Subset)",
        nbins=20
    )
    hist_fig.update_layout(margin={"t":40, "b":20, "l":20, "r":20})

    return map_fig, hist_fig


# --- 3. Build, report, and serve only when asked ---

def build_and_report(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from plotly.io.json import to_json_plotly

    default_run = unique_model_ids[0]
    default_rows = large_data[
        (large_data['model_run_id'] == default_run) &
        (large_data['confidence_score'].between(0.8, 1.0))
    ]
    summary = {
        "raw_rows": int(len(large_data)),
        "raw_payload_bytes": len(INITIAL_RAW_DATA),
        "model_runs": {str(k): int(v) for k, v in
                       large_data['model_run_id'].value_counts().items()},
        "default_model_run": str(default_run),
        "default_slider": [0.8, 1.0],
        "filtered_rows_default": int(len(default_rows)),
        "reduction_factor": round(len(large_data) / max(1, len(default_rows)), 1),
        "stages": ["filter_data_and_store", "render_visualizations"],
    }
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(json.loads(to_json_plotly(app.layout)), indent=2) + "\n",
        encoding="utf-8")
    (output_dir / "state_store_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("--- Performance Optimized Dashboard (100K Detections) ---")
    print(f"Raw rows: {summary['raw_rows']}; serialised: "
          f"{summary['raw_payload_bytes'] / 1024:.0f} KiB")
    for run_id, count in summary["model_runs"].items():
        print(f"  {run_id}: {count} detections")
    print(f"Default filter {default_run} at 0.8-1.0 keeps {len(default_rows)} rows "
          f"({summary['reduction_factor']}x smaller)")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and state_store_summary.json")
    print("Serve it for real with: python3 state_store_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        app.run(debug=False, port=8050)
    else:
        build_and_report()
