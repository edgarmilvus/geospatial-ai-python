import folium
import pathlib

# --- 1. Define Geospatial Data and Metadata ---
# Coordinates represent a specific point of interest (The Eiffel Tower, Paris)
# Latitude (Y-axis) must always precede Longitude (X-axis) in map libraries.
LATITUDE = 48.8584
LONGITUDE = 2.2945
POPUP_CONTENT = "GeoAI Detection 9001: Classified as 'Historical Landmark' (Confidence: 98.5%)"
OUTPUT_FILENAME = "basic_marker_map.html"

# --- 2. Map Initialization ---
# Create a base map object. We center the map slightly north of the point
# to ensure the marker isn't immediately covered by the map controls.
# 'zoom_start' defines the initial magnification level (15 is close-up).
initial_location = [LATITUDE + 0.005, LONGITUDE]
m = folium.Map(
    location=initial_location,
    zoom_start=15,
    tiles="CartoDB positron"  # Using a light, neutral background tile set
)

# --- 3. Create the Interactive Popup Object ---
# A folium.Popup object wraps the content, allowing control over display properties.
# max_width ensures the popup box doesn't stretch infinitely for long text.
popup_object = folium.Popup(
    POPUP_CONTENT,
    max_width=350
)

# --- 4. Create the Marker Object ---
# The Marker links the geographical location with the interactive elements.
marker = folium.Marker(
    location=[LATITUDE, LONGITUDE],
    popup=popup_object,
    tooltip="Click for GeoAI Details" # Text displayed when the mouse hovers over the marker
)

# --- 5. Add Marker to Map and Save ---
# The marker is explicitly added to the map object 'm'.
marker.add_to(m)

# Save the map as a standalone HTML file, into the project's own output/ folder:
# the file does not depend on the directory the script was started from.
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / OUTPUT_FILENAME
m.save(str(output_file))

print(f"Interactive map successfully generated: {output_file.relative_to(output_dir.parent)}")
