import pandas as pd
import numpy as np
import folium
import pathlib
from folium.plugins import MarkerCluster

# --- 1. Configuration and Constants ---
# Central coordinates for the visualization area (e.g., a major metropolitan area)
CENTER_COORDS = [34.0522, -118.2437]  # Los Angeles area
INITIAL_ZOOM = 10
DUMP_SITES_COUNT = 50  # Number of simulated detections
MAP_FILENAME = "geoai_detection_map.html"

# The HTML file belongs to the project, not to the folder the script was started from.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- 2. Synthetic Data Generation (Simulating GeoAI Output) ---
def generate_synthetic_detections(count):
    """
    Generates a DataFrame simulating GeoAI detection results, including
    coordinates, confidence scores, and identifiers.
    """
    
    # Fixed seed: the simulated detection set must be the same on every run, so a
    # reader comparing two maps is comparing the styling, not the random draw.
    np.random.seed(42)

    # Generate random coordinates centered around LA
    lats = CENTER_COORDS[0] + np.random.uniform(-0.5, 0.5, count)
    lons = CENTER_COORDS[1] + np.random.uniform(-0.8, 0.8, count)
    
    # Simulate AI confidence scores (ranging from 60% to 99%)
    confidences = np.random.uniform(0.60, 0.99, count).round(3)
    
    # Simulate unique identifiers and dummy image links for external review
    data = {
        'site_id': [f'DS_{i+1:03d}' for i in range(count)],
        'latitude': lats,
        'longitude': lons,
        'confidence': confidences,
        'image_link': [f'https://example.com/sat_img/{i+1}.jpg' for i in range(count)]
    }
    return pd.DataFrame(data)

# --- 3. Custom Popup HTML Generation ---
def create_rich_popup_html(row):
    """
    Generates complex, styled HTML content for the Folium popup using f-strings.
    This mimics the functionality of a lightweight templating engine like Jinja2.
    """
    
    # Conditional logic to assign visual status based on confidence threshold
    if row['confidence'] >= 0.90:
        status_class = "high-conf"
        status_text = "Confirmed High Priority"
    elif row['confidence'] >= 0.75:
        status_class = "medium-conf"
        status_text = "Review Required"
    else:
        status_class = "low-conf"
        status_text = "Low Confidence/Verify"

    # Define the HTML structure with embedded CSS for a clean, report-like appearance
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Basic styling for the popup container */
            .popup-header {{ background-color: #34495e; color: white; padding: 5px; font-weight: bold; font-size: 14px; margin-bottom: 5px;}}
            .data-row {{ margin-top: 3px; font-size: 12px; font-family: Arial, sans-serif; }}
            .data-label {{ font-weight: bold; display: inline-block; width: 80px; color: #555; }}
            /* Dynamic status badge styling */
            .{status_class} {{ 
                background-color: {'#2ecc71' if status_class == 'high-conf' else ('#f39c12' if status_class == 'medium-conf' else '#e74c3c')}; 
                color: white; 
                padding: 2px 5px; 
                border-radius: 3px; 
                font-weight: bold;
            }}
            .link-style {{ display: block; margin-top: 10px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="popup-header">GeoAI Detection: {row['site_id']}</div>
        <div class="data-row"><span class="data-label">Status:</span> <span class="{status_class}">{status_text}</span></div>
        <div class="data-row"><span class="data-label">Confidence:</span> {row['confidence']:.3f}</div>
        <div class="data-row"><span class="data-label">Location:</span> ({row['latitude']:.4f}, {row['longitude']:.4f})</div>
        <div class="link-style">
            <a href="{row['image_link']}" target="_blank">Review Satellite Snippet</a>
        </div>
    </body>
    </html>
    """
    return html

# --- 4. Main Mapping Function ---
def map_geoai_detections(df):
    """Initializes the map, applies clustering, and adds custom markers and popups."""
    
    # Initialize the base map using a neutral tile set for clear data visualization
    m = folium.Map(location=CENTER_COORDS, zoom_start=INITIAL_ZOOM, tiles="CartoDB positron")

    # Initialize MarkerCluster for performance optimization
    marker_cluster = MarkerCluster(
        name='GeoAI Detections',
        options={'disableClusteringAtZoom': 14} # Stop clustering when zoomed in close
    ).add_to(m)

    for index, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        confidence = row['confidence']
        
        # --- Conditional Marker Styling (Mapping Analysis to Visualization) ---
        if confidence >= 0.90:
            icon_color = 'darkgreen'
            icon_type = 'check-circle' # Confirmed site
        elif confidence >= 0.75:
            icon_color = 'orange'
            icon_type = 'exclamation-triangle' # Site needing manual review
        else:
            icon_color = 'red'
            icon_type = 'times-circle' # Potential false positive/low priority

        # 1. Generate the rich HTML content
        popup_html = create_rich_popup_html(row)
        
        # 2. Wrap the HTML in an IFrame for isolated rendering and sizing
        iframe = folium.IFrame(html=popup_html, width=280, height=180)
        
        # 3. Create the Folium Popup object
        popup = folium.Popup(iframe, max_width=300)
        
        # 4. Create the custom Icon using Font Awesome (prefix='fa')
        custom_icon = folium.Icon(color=icon_color, icon=icon_type, prefix='fa')
        
        # 5. Create the Marker and add it to the MarkerCluster group
        folium.Marker(
            location=[lat, lon],
            popup=popup,
            icon=custom_icon,
            tooltip=f"Site {row['site_id']} | Conf: {confidence:.2f}" # Quick hover information
        ).add_to(marker_cluster)

    # Add a Layer Control to allow users to toggle the cluster visibility
    folium.LayerControl().add_to(m)
    
    # Save the final map to an HTML file, one output/ folder for the project
    output_file = OUTPUT_DIR / MAP_FILENAME
    m.save(str(output_file))
    print(f"Map saved successfully to {output_file.relative_to(OUTPUT_DIR.parent)}")
    
# --- 5. Execution ---
if __name__ == "__main__":
    detection_df = generate_synthetic_detections(DUMP_SITES_COUNT)
    map_geoai_detections(detection_df)
