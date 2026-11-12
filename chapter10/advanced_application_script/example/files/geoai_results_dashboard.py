"""A two-output GeoAI results dashboard: a region selector, a feature selector,
a choropleth map and a time-series chart, driven by one callback.

Running the file builds the application and writes what it would serve to
`output/`; it does not open a socket. `python3 geoai_results_dashboard.py --serve`
is the branch that actually listens.
"""
import json
import pathlib
import sys

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data Simulation (Representing GeoAI Model Output) ---
# In a real application, this would be loaded from a PostGIS database or S3 bucket.

# A. Simulate Statistical Data (Area coverage over time)
# The generator is seeded so the dashboard, its counts and its figures are the
# same on every run; an unseeded `np.random.choice` is the reason a printed
# dashboard is impossible to check.
rng = np.random.default_rng(7)
data = {
    'Region': rng.choice(['District Alpha', 'District Beta', 'District Gamma'], 100),
    'Feature_Type': rng.choice(['Water Bodies', 'Urban Sprawl', 'Deforestation',
                                'Infrastructure Damage'], 100),
    'Area_sq_km': rng.integers(5, 300, 100) / 10,
    'Date': pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='W'))
}
df = pd.DataFrame(data)

# B. Simulate Geospatial Data (Simplified GeoJSON for map boundaries/features)
# We create a simple GeoJSON structure where each feature corresponds to a unique (Region, Feature_Type) combination.
# Note: Coordinates are simplified for demonstration purposes.
GEOJSON_DATA = {
    "type": "FeatureCollection",
    "features": []
}
coords = [
    [[-74.0, 40.7], [-74.1, 40.7], [-74.1, 40.8], [-74.0, 40.8], [-74.0, 40.7]], # Alpha
    [[-73.5, 40.0], [-73.6, 40.0], [-73.6, 40.1], [-73.5, 40.1], [-73.5, 40.0]], # Beta
    [[-75.0, 41.0], [-75.1, 41.0], [-75.1, 41.1], [-75.0, 41.1], [-75.0, 41.0]]  # Gamma
]
# Name the coordinates by region. Indexing `coords` by the position of a name in
# `df['Region'].unique()` attaches Alpha's outline to whichever district happens
# to come first in the random draw.
REGION_COORDS = {
    'District Alpha': coords[0],
    'District Beta': coords[1],
    'District Gamma': coords[2],
}

for region in df['Region'].unique():
    for feature_type in df['Feature_Type'].unique():
        # Create a unique ID linked to the combination
        feature_id = f"{region}_{feature_type}"
        GEOJSON_DATA["features"].append({
            "type": "Feature",
            "properties": {"id": feature_id, "region": region, "feature_type": feature_type},
            "geometry": {"type": "Polygon", "coordinates": [REGION_COORDS[region]]}
        })

# --- 2. Dash Application Setup and Layout ---
app = dash.Dash(__name__, title="GeoAI Monitoring Dashboard")
server = app.server

# Get unique options for controls
region_options = [{'label': r, 'value': r} for r in df['Region'].unique()]
feature_options = [{'label': f, 'value': f} for f in df['Feature_Type'].unique()]

app.layout = html.Div(className='container', children=[
    html.H1("GeoAI Segmentation Results Monitor", style={'textAlign': 'center'}),

    # Control Panel Row
    html.Div(className='row', style={'display': 'flex', 'padding': '10px'}, children=[
        # Region Selector (Dropdown)
        html.Div(style={'width': '48%', 'paddingRight': '2%'}, children=[
            html.Label("Select Administrative Region:"),
            dcc.Dropdown(
                id='region-selector',
                options=region_options,
                value=df['Region'].iloc[0],  # Default value
                clearable=False
            )
        ]),
        # Feature Type Selector (Radio Items)
        html.Div(style={'width': '48%', 'paddingLeft': '2%'}, children=[
            html.Label("Select Segmented Feature Type:"),
            dcc.RadioItems(
                id='feature-selector',
                options=feature_options,
                value=df['Feature_Type'].iloc[0], # Default value
                inline=True,
                style={'marginTop': '5px'}
            )
        ])
    ]),

    # Visualization Row
    html.Div(className='row', style={'display': 'flex', 'marginTop': '20px'}, children=[
        # Map Visualization (Left)
        html.Div(style={'width': '60%', 'paddingRight': '10px'}, children=[
            dcc.Graph(id='geoai-map')
        ]),
        # Time Series Chart (Right)
        html.Div(style={'width': '40%', 'paddingLeft': '10px'}, children=[
            dcc.Graph(id='area-chart')
        ])
    ])
])


def region_center(region):
    """The centre of a region's outline, read from its own GeoJSON feature."""
    for feature in GEOJSON_DATA['features']:
        if feature['properties']['region'] == region:
            ring = feature['geometry']['coordinates'][0]
            lon = sum(point[0] for point in ring) / len(ring)
            lat = sum(point[1] for point in ring) / len(ring)
            return lat, lon
    return 40.7, -74.0  # Fallback to the New York area


# --- 3. Complex Callback Definition ---
@app.callback(
    [Output('geoai-map', 'figure'),
     Output('area-chart', 'figure')],
    [Input('region-selector', 'value'),
     Input('feature-selector', 'value')]
)
def update_dashboard(selected_region, selected_feature):
    # 1. Filter the statistical DataFrame based on user inputs
    filtered_df = df[
        (df['Region'] == selected_region) &
        (df['Feature_Type'] == selected_feature)
    ].sort_values(by='Date')

    # 2. Prepare data for Map Visualization (Choropleth Mapbox)
    # We create a temporary DataFrame linking the filtered data back to the GeoJSON IDs
    map_data = pd.DataFrame({
        'id': [f"{selected_region}_{selected_feature}"],
        'Area_sq_km': [filtered_df['Area_sq_km'].sum()] # Sum area for visualization
    })

    # The view must follow the selected region, not the first feature in the
    # collection, or District Beta opens over District Alpha.
    lat_center, lon_center = region_center(selected_region)

    # Create the Choropleth Mapbox figure
    map_fig = px.choropleth_mapbox(
        map_data,
        geojson=GEOJSON_DATA,
        locations='id', # Column in map_data matching feature ID in GeoJSON
        color='Area_sq_km',
        featureidkey="properties.id", # Key in GeoJSON to match 'locations'
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": lat_center, "lon": lon_center},
        opacity=0.7,
        title=f"Segmented Area in {selected_region}"
    )
    map_fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})


    # 3. Prepare data for Time Series Chart
    chart_fig = px.line(
        filtered_df,
        x='Date',
        y='Area_sq_km',
        title=f"Area Trend: {selected_feature}",
        markers=True
    )
    chart_fig.update_layout(xaxis_title="Date of Satellite Pass", yaxis_title="Area (sq km)")


    # 4. Return both figures to their respective components
    return map_fig, chart_fig


# --- 4. BUILD, REPORT, AND (ONLY WHEN ASKED) SERVE ---

def build_and_report(output_dir=OUTPUT_DIR):
    """Write the layout, the feature collection and the counts the dashboard uses."""
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from plotly.io.json import to_json_plotly

    counts = (df.groupby(['Region', 'Feature_Type']).size()
                .rename('rows').reset_index().sort_values(['Region', 'Feature_Type']))
    summary = {
        "rows": int(len(df)),
        "regions": df['Region'].unique().tolist(),
        "features": df['Feature_Type'].unique().tolist(),
        "combinations": len(GEOJSON_DATA['features']),
        "rows_per_combination": counts.to_dict(orient="records"),
        "default_region": df['Region'].iloc[0],
        "default_feature": df['Feature_Type'].iloc[0],
        "total_area_sq_km": round(float(df['Area_sq_km'].sum()), 2),
    }
    (output_dir / "dashboard_layout.json").write_text(
        json.dumps(json.loads(to_json_plotly(app.layout)), indent=2) + "\n",
        encoding="utf-8")
    (output_dir / "dashboard_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "geojson_features.json").write_text(
        json.dumps(GEOJSON_DATA, indent=2) + "\n", encoding="utf-8")

    print("--- GeoAI Segmentation Results Monitor ---")
    print(f"Rows: {len(df)}; regions: {len(summary['regions'])}; "
          f"feature types: {len(summary['features'])}")
    print(f"GeoJSON features: {summary['combinations']}")
    for row in counts.itertuples(index=False):
        print(f"  {row.Region:<16} {row.Feature_Type:<22} {row.rows:>2} rows")
    print(f"Default view: {summary['default_region']} / {summary['default_feature']}")
    print(f"Wrote {output_dir.name}/dashboard_layout.json and dashboard_summary.json")
    print("Serve it for real with: python3 geoai_results_dashboard.py --serve")


if __name__ == '__main__':
    if "--serve" in sys.argv:
        app.run(debug=False, port=8050)
    else:
        build_and_report()
