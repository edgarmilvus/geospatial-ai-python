"""A minimal GeoAI zone dashboard: one dropdown, one map, one text panel.

Running the file builds the application, writes the layout it would serve to
`output/dashboard_layout.json` and stops. It never opens a socket: a listing that
called `app.run()` would block the terminal and could not be checked. Serve it
for real with `python3 geoai_zone_dashboard.py --serve`, which is the branch at
the bottom.
"""
import json
import pathlib
import sys

import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. DATA PREPARATION ---

# Simulate geospatial results (e.g., detection centers or analysis zones)
data = {
    'city': ['Zone A', 'Zone B', 'Zone C'],
    'lat': [34.05, 34.10, 34.15],
    'lon': [-118.25, -118.30, -118.35],
    'value': [100, 250, 50]  # Hypothetical GeoAI metric (e.g., detected object count)
}
df = pd.DataFrame(data)

# --- 2. APPLICATION INITIALIZATION ---

# Initialize the Dash application instance
app = dash.Dash(__name__)

# --- 3. INITIAL VISUALIZATION SETUP ---

# Create the base Plotly figure using a geospatial mapbox style
initial_fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    hover_name="city",
    color="value",
    size="value",      # Size markers by the calculated value
    zoom=10,           # Set initial zoom level
    height=400,
    mapbox_style="carto-positron" # Use a standard, clean map background
)

# Optimize map layout for cleaner embedding
initial_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})


# --- 4. APPLICATION LAYOUT DEFINITION ---

# Define the structure of the dashboard using HTML and Dash Core Components (dcc)
app.layout = html.Div([
    # Header component
    html.H1("Minimal GeoAI Zone Dashboard", style={'textAlign': 'center', 'color': '#333'}),

    # Input Component: Dropdown selector
    dcc.Dropdown(
        id='zone-selector',
        options=[{'label': i, 'value': i} for i in df['city']],
        value='Zone A',  # Set a default selected value
        clearable=False,
        style={'width': '60%', 'margin': '20px auto', 'display': 'block'}
    ),

    # Output Component 1: The interactive map visualization
    dcc.Graph(
        id='geo-map-output',
        figure=initial_fig # Display the pre-generated map initially
    ),

    # Output Component 2: Text area to display details based on selection
    html.Div(
        id='selection-details',
        style={'padding': '20px', 'fontSize': '18px', 'borderTop': '2px solid #eee'}
    )
])


# --- 5. THE CALLBACK FUNCTION (INTERACTIVE LOGIC) ---

# The decorator defines the link: Input('zone-selector', 'value') -> Output('selection-details', 'children')
@app.callback(
    Output('selection-details', 'children'), # The property of the target component to be updated
    Input('zone-selector', 'value')         # The property of the source component that triggers the update
)
def update_details(selected_zone):
    """
    This function executes every time the 'value' property of the 'zone-selector' changes.
    It filters the data and returns a new string to update the 'children' property of the output Div.
    """
    # Filter the DataFrame to find the selected zone's data
    filtered_df = df[df['city'] == selected_zone].iloc[0]

    # Construct the dynamic output string
    output_text = (
        f"**Analysis Summary for {selected_zone}**\n\n"
        f"Coordinates: ({filtered_df['lat']:.2f}, {filtered_df['lon']:.2f})\n"
        f"Calculated GeoAI Metric Value: {filtered_df['value']}"
    )

    # Note: Dash automatically handles the conversion of this string into HTML text within the Div
    return html.Pre(output_text) # Use html.Pre to preserve line breaks and formatting


# --- 6. BUILD, REPORT, AND (ONLY WHEN ASKED) SERVE ---

def build_and_report(output_dir=OUTPUT_DIR):
    """Write the layout the server would hand to the browser, and a small summary."""
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Plotly's encoder handles the numpy arrays inside the figure, and Dash
    # components expose `to_plotly_json`, so this is the whole layout as JSON.
    from plotly.io.json import to_json_plotly
    layout_dict = json.loads(to_json_plotly(app.layout))
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(layout_dict, indent=2) + "\n", encoding="utf-8")
    (output_dir / "index.html").write_text(app.index_string, encoding="utf-8")

    summary = {
        "zones": df['city'].tolist(),
        "lat": df['lat'].tolist(),
        "lon": df['lon'].tolist(),
        "values": df['value'].tolist(),
        "default_zone": "Zone A",
        "mapbox_style": "carto-positron",
        "zoom": 10,
        "callbacks": sorted(app.callback_map),
    }
    (output_dir / "zone_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("--- Minimal GeoAI Zone Dashboard ---")
    for row in df.itertuples(index=False):
        print(f"  {row.city}: ({row.lat:.2f}, {row.lon:.2f}) -> value {row.value}")
    print(f"Layout children: {len(app.layout.children)}")
    print(f"Callback registered for: {sorted(app.callback_map)}")
    print(f"Default selection: Zone A; map style carto-positron at zoom 10")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and index.html")
    print("Serve it for real with: python3 geoai_zone_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        # The only branch that ever listens: `python3 geoai_zone_dashboard.py`
        # returns immediately, `--serve` blocks until Ctrl-C.
        app.run(debug=False, port=8050)
    else:
        build_and_report()
