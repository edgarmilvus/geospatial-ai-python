import folium
import pandas as pd
import numpy as np
import pathlib
from folium.plugins import MarkerCluster

# 1. Large Dataset Simulation (500 points, ~5% Priority 1)
N_POINTS = 500
np.random.seed(42)
data = {
    'latitude': 33.9 + np.random.rand(N_POINTS) * 0.2,
    'longitude': -118.5 + np.random.rand(N_POINTS) * 0.2,
    'Priority': np.random.choice([1, 2, 3], size=N_POINTS, p=[0.05, 0.35, 0.60])
}
df = pd.DataFrame(data)

# 2. Standard Clustering Implementation
m = folium.Map(location=[34.0, -118.4], zoom_start=10)
marker_cluster = MarkerCluster(
    name="Defect Clusters",
    overlay=True,
    control=False,
    # 3. Advanced Cluster Modification Logic: Injecting custom JS
    # This JS function checks the priority by iterating through the child markers' popups.
    icon_create_function="""
        function(cluster) {
            var markers = cluster.getAllChildMarkers();
            var hasPriorityOne = false;
            
            // Iterate through markers to check if any popup contains 'Priority: 1'
            for (var i = 0; i < markers.length; i++) {
                var popupContent = markers[i].getPopup().getContent();
                if (popupContent.includes('Priority: 1')) {
                    hasPriorityOne = true;
                    break;
                }
            }

            var size = cluster.getChildCount();
            var c = ' marker-cluster-';
            var iconSize = 40;

            // Conditional styling based on Priority 1 presence
            if (hasPriorityOne) {
                c += 'critical'; // Custom class defined in CSS
                iconSize = 50; // Make critical clusters larger
            } else if (size < 10) {
                c += 'small';
            } else if (size < 100) {
                c += 'medium';
            } else {
                c += 'large';
            }

            return new L.DivIcon({ 
                html: '<div><span>' + size + '</span></div>', 
                className: 'marker-cluster' + c, 
                iconSize: new L.Point(iconSize, iconSize) 
            });
        }
    """
)

# Inject custom CSS to define the 'critical' cluster style
# This must be done via HTML/CSS injection as folium doesn't have a direct CSS injection feature for this
css_style = """
<style>
    .marker-cluster-critical div {
        background-color: #ff3333; /* Bright Red */
        color: white;
        border: 2px solid #a30000;
        font-weight: bold;
    }
</style>
"""
m.get_root().html.add_child(folium.Element(css_style))


# Add markers to the cluster group
for index, row in df.iterrows():
    # iterrows() hands back a float Series when the row also holds coordinates, so
    # the integer priority arrives as 1.0; cast it or the JavaScript below, which
    # looks for the text 'Priority: 1', never matches.
    priority = int(row['Priority'])
    
    # 4. Popup Integrity: Ensure individual popups show priority
    popup_text = f"Defect ID: {index}<br>Priority: {priority}"
    
    # Conditional styling for individual markers (optional, but good practice)
    color = 'red' if priority == 1 else ('orange' if priority == 2 else 'blue')
    
    marker = folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color=color, icon='wrench', prefix='fa')
    )
    marker_cluster.add_child(marker)

m.add_child(marker_cluster)
# The map lives in memory until it is written; save it into the project's output/.
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "exercise3_conditional_clustering.html"
m.save(str(output_file))

priority_one = int((df['Priority'] == 1).sum())
print(f"Saved {output_file.relative_to(output_dir.parent)}: {len(df)} defects, "
      f"{priority_one} of them Priority 1, clustered by Leaflet at load time.")
