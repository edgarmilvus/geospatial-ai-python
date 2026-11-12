import folium
import pathlib

# Stamen's styles are no longer in folium's built-in tile table: the templates live
# at Stadia Maps now, so the URL is passed explicitly and a custom template must
# carry its attribution. folium only writes the JavaScript that would request these
# tiles; nothing is downloaded when the map is built.
STAMEN_TONER = "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png"
STAMEN_ATTRIBUTION = (
    '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '
    '&copy; <a href="https://stamen.com/">Stamen Design</a> '
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
)

# 1. Define San Francisco coordinates and zoom level
sf_coords = [37.7749, -122.4194]
zoom_level = 12

# 2. Map Initialization: Uses default OpenStreetMap tiles
m = folium.Map(location=sf_coords, zoom_start=zoom_level, tiles='OpenStreetMap')

# The default tiles are already added, but we explicitly name them for clarity in the control
folium.TileLayer('OpenStreetMap', name='Standard Street Map').add_to(m)

# 3. Secondary Tile Layer: Stamen Toner (high contrast)
# Note: By default, folium.TileLayer() adds the layer to the map, but LayerControl handles selection.
folium.TileLayer(
    tiles=STAMEN_TONER,
    name='High Contrast Roads',
    attr=STAMEN_ATTRIBUTION
).add_to(m)

# 4. Interactivity: Add the layer control mechanism
folium.LayerControl().add_to(m)

# 5. Output: the HTML belongs to the project, not to the current working directory
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "sf_contrast_map.html"
m.save(str(output_file))

print(f"Saved {output_file.relative_to(output_dir.parent)}: OpenStreetMap on load, "
      f"the high-contrast layer one click away in the control.")
