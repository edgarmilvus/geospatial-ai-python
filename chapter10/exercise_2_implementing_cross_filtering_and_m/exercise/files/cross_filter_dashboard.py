"""Exercise 2 — cross-filtering: two outputs, one callback, three inputs.

The map sees all three filters; the histogram deliberately ignores the confidence
slider, so the analyst keeps the population in view while looking at a subset.
Running the file builds the app and writes the layout; `--serve` listens.
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
from datetime import date, timedelta

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data Simulation (Expanded) ---
N_SAMPLES = 1000
np.random.seed(42)
start_date = date(2024, 1, 1)
date_list = [start_date + timedelta(days=i) for i in range(30)]

data_ex2 = pd.DataFrame({
    'latitude': np.random.uniform(34.0, 34.5, N_SAMPLES),
    'longitude': np.random.uniform(-118.5, -118.0, N_SAMPLES),
    'classification_label': np.random.choice(['Forest', 'Water', 'Urban', 'Road'], N_SAMPLES),
    'confidence_score': np.random.uniform(0.0, 1.0, N_SAMPLES),
    'model_run_id': np.random.choice(['v1.0_2023', 'v1.1_2024', 'v1.2_2024'], N_SAMPLES),
    'acquisition_date': np.random.choice(date_list, N_SAMPLES)
})
data_ex2['acquisition_date'] = pd.to_datetime(data_ex2['acquisition_date'])

app = dash.Dash(__name__)
# A Mapbox token is a deployment secret, so it is read from the environment and
# never written into the listing. The placeholder keeps the app buildable without
# one: the figures still lay out, the tiles simply do not load.
MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN", "pk.placeholder")
px.set_mapbox_access_token(MAPBOX_ACCESS_TOKEN)

unique_model_ids = data_ex2['model_run_id'].unique()
min_date = data_ex2['acquisition_date'].min()
max_date = data_ex2['acquisition_date'].max()

# --- 2. Component Expansion and Layout ---
app.layout = html.Div([
    html.H1("GeoAI Cross-Filtering Dashboard"),

    html.Div([
        # Model Selector (from Ex 1)
        html.Div([
            html.Label("Model Run ID:"),
            dcc.Dropdown(
                id='model-run-selector',
                options=[{'label': i, 'value': i} for i in unique_model_ids],
                value=unique_model_ids[0],
                clearable=False
            )
        ], style={'width': '33%', 'display': 'inline-block', 'padding': '10px'}),

        # Confidence Slider
        html.Div([
            html.Label("Confidence Score Range:"),
            dcc.RangeSlider(
                id='confidence-slider',
                min=0.0, max=1.0, step=0.05,
                value=[0.7, 1.0],
                marks={i/10: f'{i/10:.1f}' for i in range(0, 11, 2)}
            )
        ], style={'width': '33%', 'display': 'inline-block', 'padding': '10px'}),

        # Date Picker
        html.Div([
            html.Label("Acquisition Date Range:"),
            dcc.DatePickerRange(
                id='date-range-picker',
                start_date=min_date,
                end_date=max_date,
                min_date_allowed=min_date,
                max_date_allowed=max_date,
                initial_visible_month=min_date
            )
        ], style={'width': '33%', 'display': 'inline-block', 'padding': '10px'}),
    ]),

    html.Div([
        dcc.Graph(id='geoai-map-output', style={'width': '60%', 'display': 'inline-block', 'height': '60vh'}),
        dcc.Graph(id='confidence-histogram', style={'width': '40%', 'display': 'inline-block', 'height': '60vh'})
    ])
])

# --- 3. Complex Callback Implementation ---
@app.callback(
    [Output('geoai-map-output', 'figure'),
     Output('confidence-histogram', 'figure')],
    [Input('model-run-selector', 'value'),
     Input('confidence-slider', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def update_outputs(selected_model_id, confidence_range, start_date_str, end_date_str):
    # Convert date strings to datetime objects
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)

    # --- Filtering for Statistical Context (Histogram Data) ---
    # Filter 1: Model ID and Date Range
    histogram_df = data_ex2[
        (data_ex2['model_run_id'] == selected_model_id) &
        (data_ex2['acquisition_date'] >= start_date) &
        (data_ex2['acquisition_date'] <= end_date)
    ].copy()

    # Generate Histogram
    hist_fig = px.histogram(
        histogram_df,
        x="confidence_score",
        title=f"Confidence Distribution for {selected_model_id}",
        nbins=20
    )
    hist_fig.update_layout(margin={"t":40, "b":20, "l":20, "r":20})

    # --- Filtering for Geospatial Map (Highly Filtered Data) ---
    min_conf, max_conf = confidence_range

    # Filter 2: Apply all criteria including Confidence Range
    map_df = histogram_df[
        (histogram_df['confidence_score'] >= min_conf) &
        (histogram_df['confidence_score'] <= max_conf)
    ]

    # Generate Map
    if map_df.empty:
        map_fig = px.scatter_mapbox(
            map_df, lat="latitude", lon="longitude",
            title="No data matching all criteria.")
    else:
        map_fig = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="classification_label",
            zoom=10,
            height=600,
            mapbox_style="satellite-streets"
        )
    map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return map_fig, hist_fig


# --- 4. Build, report, and serve only when asked ---

def build_and_report(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from plotly.io.json import to_json_plotly

    model_run = unique_model_ids[0]
    in_window = data_ex2[
        (data_ex2['model_run_id'] == model_run) &
        (data_ex2['acquisition_date'] >= min_date) &
        (data_ex2['acquisition_date'] <= max_date)
    ]
    in_band = in_window[in_window['confidence_score'].between(0.7, 1.0)]
    summary = {
        "rows": int(len(data_ex2)),
        "dates": {"start": str(min_date.date()), "end": str(max_date.date()),
                  "count": len(date_list)},
        "model_runs": unique_model_ids.tolist(),
        "default_model_run": str(model_run),
        "histogram_rows": int(len(in_window)),
        "map_rows_at_default_slider": int(len(in_band)),
        "confidence_min": round(float(data_ex2['confidence_score'].min()), 4),
        "confidence_max": round(float(data_ex2['confidence_score'].max()), 4),
    }
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(json.loads(to_json_plotly(app.layout)), indent=2) + "\n",
        encoding="utf-8")
    (output_dir / "cross_filter_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("--- GeoAI Cross-Filtering Dashboard ---")
    print(f"Rows: {summary['rows']}; model runs: {len(summary['model_runs'])}")
    print(f"Dates: {summary['dates']['start']} to {summary['dates']['end']} "
          f"({summary['dates']['count']} days)")
    print(f"Default run {model_run}: histogram {summary['histogram_rows']} rows, "
          f"map {summary['map_rows_at_default_slider']} rows at confidence 0.7-1.0")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and cross_filter_summary.json")
    print("Serve it for real with: python3 cross_filter_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        app.run(debug=False, port=8050)
    else:
        build_and_report()
