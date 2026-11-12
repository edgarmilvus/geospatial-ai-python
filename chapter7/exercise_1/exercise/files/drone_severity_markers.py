import folium
import pandas as pd
import numpy as np
import pathlib

# 1. Data Simulation
data = [
    {'lat': 34.05, 'lon': -118.25, 'severity': 'Critical'},
    {'lat': 34.06, 'lon': -118.24, 'severity': 'Critical'},
    {'lat': 34.04, 'lon': -118.26, 'severity': 'High'},
    {'lat': 34.07, 'lon': -118.23, 'severity': 'High'},
    {'lat': 34.055, 'lon': -118.255, 'severity': 'Medium'},
    {'lat': 34.045, 'lon': -118.245, 'severity': 'Medium'},
    {'lat': 34.065, 'lon': -118.265, 'severity': 'Medium'},
    {'lat': 34.03, 'lon': -118.27, 'severity': 'Low'},
    {'lat': 34.08, 'lon': -118.22, 'severity': 'Low'},
    {'lat': 34.05, 'lon': -118.28, 'severity': 'Low'},
]
df = pd.DataFrame(data)

# Define styling rules
severity_styles = {
    'Critical': {'color': 'red', 'icon': 'exclamation-triangle', 'prefix': 'fa'},
    'High': {'color': 'orange', 'icon': 'bell', 'prefix': 'fa'},
    'Medium': {'color': 'yellow', 'icon': 'info', 'prefix': 'fa'},
    'Low': {'color': 'green', 'icon': 'info', 'prefix': 'fa'}
}

# 2. Map Initialization (Centered near simulated LA data)
m = folium.Map(location=[34.05, -118.25], zoom_start=13)

# 3 & 4. Marker Iteration and Conditional Styling
for index, row in df.iterrows():
    severity = row['severity']
    style = severity_styles.get(severity)
    
    # Create the Icon object based on severity
    custom_icon = folium.Icon(
        color=style['color'],
        icon=style['icon'],
        prefix=style['prefix']
    )
    
    # 5. Basic Popups
    popup_text = f"Severity: {severity}"
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=popup_text,
        icon=custom_icon
    ).add_to(m)

# The map lives in memory until it is written; save it into the project's output/.
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "exercise1_drone_hotspots.html"
m.save(str(output_file))

print(f"Saved {output_file.relative_to(output_dir.parent)}: {len(df)} markers, "
      f"{df['severity'].nunique()} severity levels, "
      f"one colour and icon per level.")
