"""Exercise 5 — a live data store, a DBC grid and a refresh interval.

Every 60 seconds the interval callback replaces `live-raw-data-store`, stage 1
re-filters it, stage 2 redraws. The simulated clock is deterministic: cycle *n*
produces the data and the timestamp of minute *n*, so a run is reproducible while
still differing from the cycle before it.
"""
import json
import pathlib
import sys
from datetime import datetime, timedelta

import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- Data Simulation Functions ---
N_SAMPLES = 500 # Keep sample size smaller for live updates simulation
BASE_TIME = datetime(2024, 6, 1, 12, 0, 0)

def query_latest_geoai_results(cycle: int = 0):
    """Simulates querying a database for the data of refresh cycle `cycle`."""
    np.random.seed(1000 + cycle)  # A new draw each cycle, the same draw each run
    timestamp = BASE_TIME + timedelta(minutes=cycle)
    df = pd.DataFrame({
        'latitude': np.random.uniform(34.0, 34.5, N_SAMPLES),
        'longitude': np.random.uniform(-118.5, -118.0, N_SAMPLES),
        'classification_label': np.random.choice(['A', 'B', 'C', 'D'], N_SAMPLES),
        'confidence_score': np.random.uniform(0.0, 1.0, N_SAMPLES),
        'model_run_id': np.random.choice(['v_prod', 'v_test'], N_SAMPLES),
        'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S")
    })
    return df

def serialize_df(df):
    return df.to_json(date_format='iso', orient='split')

def deserialize_df(json_data):
    import io
    return pd.read_json(io.StringIO(json_data), orient='split')

# --- Initialization ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# A Mapbox token is a deployment secret, so it is read from the environment and
# never written into the listing. The placeholder keeps the app buildable without
# one: the figures still lay out, the tiles simply do not load.
MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN", "pk.placeholder")
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

# Initial data load for startup
initial_df = query_latest_geoai_results()
unique_model_ids = initial_df['model_run_id'].unique()

# --- 2. Layout Refactoring with DBC ---
controls = dbc.Card(
    [
        html.H4("Control Panel", className="card-title"),
        html.P(f"Last updated: {initial_df['timestamp'].iloc[0]}", id='last-updated-time'),
        html.Div([
            html.Label("Model Run ID:"),
            dcc.Dropdown(
                id='model-run-selector',
                options=[{'label': i, 'value': i} for i in unique_model_ids],
                value=unique_model_ids[0],
                clearable=False
            )
        ], className="mb-3"),
        html.Div([
            html.Label("Confidence Score Range:"),
            dcc.RangeSlider(
                id='confidence-slider',
                min=0.0, max=1.0, step=0.05,
                value=[0.8, 1.0],
                marks={i/10: f'{i/10:.1f}' for i in range(0, 11, 2)}
            )
        ])
    ],
    body=True,
    className="h-100"
)

app.layout = dbc.Container([
    dcc.Store(id='live-raw-data-store', data=serialize_df(initial_df)),
    dcc.Store(id='filtered-data-store'),
    dcc.Interval(
        id='data-refresh-interval',
        interval=60 * 1000,  # 60 seconds
        n_intervals=0
    ),

    html.H1("Dynamic GeoAI Dashboard (DBC & Live Data)", className="my-4"),

    # Row 1: Map and Controls
    dbc.Row([
        # Control Panel: xs=12 (full width on mobile), lg=3 (25% on desktop)
        dbc.Col(controls, xs=12, lg=3, className="mb-3"),

        # Primary Map: xs=12 (full width on mobile), lg=9 (75% on desktop)
        dbc.Col(dcc.Graph(id='geoai-map-output', style={'height': '70vh'}), xs=12, lg=9, className="mb-3"),
    ]),

    # Row 2: Secondary Chart (Always full width)
    dbc.Row([
        # Secondary Chart: xs=12 (100% width)
        dbc.Col(dcc.Graph(id='confidence-histogram', style={'height': '40vh'}), xs=12, className="mb-3"),
    ])
], fluid=True)


# --- 1. Dynamic Data Refresh Callback ---
@app.callback(
    [Output('live-raw-data-store', 'data'),
     Output('last-updated-time', 'children')],
    [Input('data-refresh-interval', 'n_intervals')]
)
def refresh_data(n):
    """Triggers database query simulation and updates the raw data store."""
    new_df = query_latest_geoai_results(n or 0)
    new_data_json = serialize_df(new_df)
    timestamp = new_df['timestamp'].iloc[0]
    return new_data_json, f"Last updated: {timestamp} (Interval {n})"


# --- 2. Stage 1 Callback: Filtering Logic (Uses live-raw-data-store) ---
@app.callback(
    Output('filtered-data-store', 'data'),
    [Input('model-run-selector', 'value'),
     Input('confidence-slider', 'value'),
     Input('live-raw-data-store', 'data')] # Now an Input, triggering filter upon refresh
)
def filter_data_and_store(selected_model_id, confidence_range, raw_json_data):
    """Filters the raw data based on user inputs AND live data changes."""

    if raw_json_data is None:
        return None

    df_raw = deserialize_df(raw_json_data)

    min_conf, max_conf = confidence_range

    df_filtered = df_raw[
        (df_raw['model_run_id'] == selected_model_id) &
        (df_raw['confidence_score'] >= min_conf) &
        (df_raw['confidence_score'] <= max_conf)
    ]

    return serialize_df(df_filtered)

# --- 3. Stage 2 Callback: Visualization Rendering (Unchanged) ---
@app.callback(
    [Output('geoai-map-output', 'figure'),
     Output('confidence-histogram', 'figure')],
    [Input('filtered-data-store', 'data')]
)
def render_visualizations(filtered_json_data):
    """Reads the pre-filtered data and generates figures quickly."""

    if filtered_json_data is None:
        empty = initial_df.iloc[0:0]
        return (px.scatter_mapbox(empty, lat="latitude", lon="longitude",
                                  title="Waiting for data..."),
                px.histogram(empty, x="confidence_score", title="Waiting for data..."))

    df_filtered = deserialize_df(filtered_json_data)

    # ... (Map and Histogram generation logic from Ex 4) ...
    map_fig = px.scatter_mapbox(
        df_filtered, lat="latitude", lon="longitude", color="classification_label", zoom=10, height=600, mapbox_style="satellite-streets"
    )
    map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    hist_fig = px.histogram(
        df_filtered, x="confidence_score", title="Confidence Distribution (Filtered Subset)", nbins=20
    )
    hist_fig.update_layout(margin={"t":40, "b":20, "l":20, "r":20})

    return map_fig, hist_fig


# --- 4. Build, report, and serve only when asked ---

def build_and_report(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from plotly.io.json import to_json_plotly

    run = unique_model_ids[0]
    default_rows = initial_df[
        (initial_df['model_run_id'] == run) &
        (initial_df['confidence_score'].between(0.8, 1.0))
    ]
    summary = {
        "rows_per_cycle": int(len(initial_df)),
        "cycle": 0,
        "timestamp": str(initial_df['timestamp'].iloc[0]),
        "interval_ms": 60 * 1000,
        "model_runs": {str(k): int(v) for k, v in
                       initial_df['model_run_id'].value_counts().items()},
        "default_model_run": str(run),
        "filtered_rows_default": int(len(default_rows)),
        "grid": {"controls": {"xs": 12, "lg": 3},
                 "map": {"xs": 12, "lg": 9},
                 "histogram": {"xs": 12}},
    }
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(json.loads(to_json_plotly(app.layout)), indent=2) + "\n",
        encoding="utf-8")
    (output_dir / "live_dashboard_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("--- Dynamic GeoAI Dashboard (DBC & Live Data) ---")
    print(f"Cycle 0 at {summary['timestamp']}: {len(initial_df)} detections")
    for run_id, count in summary["model_runs"].items():
        print(f"  {run_id}: {count} detections")
    print(f"Default filter {run} at 0.8-1.0 keeps {len(default_rows)} rows")
    print("Grid: controls xs=12/lg=3, map xs=12/lg=9, histogram xs=12 in its own row")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and live_dashboard_summary.json")
    print("Serve it for real with: python3 live_dbc_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        app.run(debug=False, port=8050)
    else:
        build_and_report()
