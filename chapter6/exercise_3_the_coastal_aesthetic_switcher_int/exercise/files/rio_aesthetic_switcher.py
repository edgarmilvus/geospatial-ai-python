import folium
import pathlib

# Stamen Watercolor left folium's built-in tile table when the style moved to Stadia
# Maps, so the template is written out and given its attribution. CartoDB Dark
# Matter is still a built-in name and needs neither.
STAMEN_WATERCOLOR = "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.png"
STAMEN_ATTRIBUTION = (
    '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '
    '&copy; <a href="https://stamen.com/">Stamen Design</a> '
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
)

# 1. Define Rio de Janeiro coordinates and zoom level
rio_coords = [-22.9068, -43.1729]
zoom_level = 11

# 2. Map Initialization (Defaulting to OpenStreetMap)
m = folium.Map(location=rio_coords, zoom_start=zoom_level)

# 3. Tile Layer 1 (Default): Standard Detail
# We explicitly add it to ensure it gets the custom name in LayerControl
folium.TileLayer('OpenStreetMap', name='Standard Detail').add_to(m)

# 4. Tile Layer 2 (Water Emphasis): Stamen Water Color
folium.TileLayer(STAMEN_WATERCOLOR, name='Watercolor Presentation',
                 attr=STAMEN_ATTRIBUTION).add_to(m)

# 5. Tile Layer 3 (Dark Context): CartoDB Dark Matter
folium.TileLayer('CartoDB Dark Matter', name='Dark Context').add_to(m)

# 6. Layer Control Implementation
folium.LayerControl().add_to(m)

# 7. Saving: the HTML belongs to the project, not to the current working directory
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "rio_aesthetic_switcher.html"
m.save(str(output_file))

print(f"Saved {output_file.relative_to(output_dir.parent)} over Rio de Janeiro at zoom "
      f"{zoom_level}: OpenStreetMap on load, watercolour and dark context one click away.")
