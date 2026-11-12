import folium
import pandas as pd
import pathlib
from datetime import datetime

# 1. Advanced Data Structure
data = [
    {'lat': 34.051, 'lon': -118.251, 'classification': 'Forest', 'confidence_score': 0.985, 'analysis_date': '2023-10-15'},
    {'lat': 34.049, 'lon': -118.249, 'classification': 'Water', 'confidence_score': 0.721, 'analysis_date': '2023-10-16'},
    {'lat': 34.060, 'lon': -118.260, 'classification': 'Agriculture', 'confidence_score': 0.850, 'analysis_date': '2023-10-17'},
    {'lat': 34.055, 'lon': -118.255, 'classification': 'Urban', 'confidence_score': 0.999, 'analysis_date': '2023-10-18'},
    {'lat': 34.045, 'lon': -118.265, 'classification': 'Barren Land', 'confidence_score': 0.655, 'analysis_date': '2023-10-19'},
]
df = pd.DataFrame(data)

# 2. Map Initialization
m = folium.Map(location=[34.05, -118.25], zoom_start=14)

# 3. Dynamic Popup Generation and Marker Placement
for index, row in df.iterrows():
    # 2. Data Preparation: Format confidence score
    confidence_percent = f"{row['confidence_score'] * 100:.1f}%"
    
    # 3. Dynamic Popup Generation (using HTML structure)
    html = f"""
    <div style="width: 200px;">
        <h3 style="color: #0056b3; margin-bottom: 5px;">GeoAI Classification</h3>
        <hr style="margin: 5px 0;">
        <b>Type:</b> {row['classification']}<br>
        <b>Confidence:</b> <span style="color: {'green' if row['confidence_score'] > 0.8 else 'red'};">{confidence_percent}</span><br>
        <i>Analyzed On:</i> {row['analysis_date']}
    </div>
    """
    
    # Create the HTML object and the Popup object
    iframe = folium.IFrame(html, width=220, height=120)
    popup = folium.Popup(iframe, max_width=2650) # max_width is often required for embedded HTML
    
    # 4. Marker Placement
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=popup,
        tooltip=row['classification'] # Add tooltip for quick hover info
    ).add_to(m)

# The map lives in memory until it is written; save it into the project's output/.
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "exercise2_dynamic_popups.html"
m.save(str(output_file))

print(f"Saved {output_file.relative_to(output_dir.parent)}: {len(df)} markers, "
      f"confidence shown as a percentage and coloured at the 80% threshold.")
