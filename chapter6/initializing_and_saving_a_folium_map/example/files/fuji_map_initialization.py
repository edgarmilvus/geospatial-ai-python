import folium
import pathlib

# --- 1. Define Map Parameters ---
# We use constants (uppercase names) for clarity and adherence to PEP 8 standards
# for values that should not change during execution.

# Latitude (y-axis) and Longitude (x-axis) for Mount Fuji, Japan
FUJI_LATITUDE = 35.3606
FUJI_LONGITUDE = 138.7278

# Initial zoom level: 12 provides a good regional view.
# Zoom levels typically range from 0 (world view) to 18 (street level).
INITIAL_ZOOM = 12

# --- 2. Initialize the Folium Map Object ---
# The Map class constructor requires the 'location' argument (a list/tuple of [lat, lon]).
# We also explicitly specify the 'tiles' provider, although 'OpenStreetMap' is the default.
basic_map = folium.Map(
    location=[FUJI_LATITUDE, FUJI_LONGITUDE],
    zoom_start=INITIAL_ZOOM,
    tiles="OpenStreetMap"
)

# --- 3. Save the Map to HTML ---
# The .save() method serializes the Python object into a complete, interactive HTML file.
# The file belongs to the project, not to the folder this script was started from.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILENAME = OUTPUT_DIR / "06_02_fuji_map.html"
basic_map.save(str(OUTPUT_FILENAME))

# Confirmation message for the user: a path relative to the project, so the line
# carries no machine's home directory.
print(f"Interactive map successfully generated and saved to: "
      f"{OUTPUT_FILENAME.relative_to(OUTPUT_DIR.parent)}")
