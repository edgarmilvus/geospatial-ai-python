import folium
import pathlib

# 1. Base Map Setup
london_coords = [51.5074, 0.1278]
london_map = folium.Map(location=london_coords, zoom_start=10)

# 2. Explicit Default Layer (OpenStreetMap)
# We use the default tileset but explicitly name it.
folium.TileLayer(
    tiles='OpenStreetMap',
    name='Project OSM Base',
    overlay=False,  # Ensures it's treated as a base layer
    control=True,   # Ensures it appears in the LayerControl
).add_to(london_map)

# 3. Custom Stamen Toner Layer
# Stamen's styles left folium's built-in tile table when they moved to Stadia Maps,
# so the template is passed explicitly; the attribution is the project's own.
custom_attribution = "Data provided by Stamen Design. Project Copyright 2024 GeoAI."
STAMEN_TONER = "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png"

folium.TileLayer(
    tiles=STAMEN_TONER,
    name='Toner for Data Overlay',
    attr=custom_attribution,  # Custom Attribution
    show=False,               # Non-Default Setting: Hidden on map load
    overlay=False
).add_to(london_map)

# 4. Control Integration
folium.LayerControl().add_to(london_map)

# 5. Output: the HTML belongs to the project, not to the current working directory
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "london_custom_tiles.html"
london_map.save(str(output_file))

print(f"Saved {output_file.relative_to(output_dir.parent)}: OSM is the visible base "
      f"layer, the Toner layer waits behind the layer control with its own attribution.")
