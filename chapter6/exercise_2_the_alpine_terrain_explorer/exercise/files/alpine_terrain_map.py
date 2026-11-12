import folium
import pathlib

# Stamen's styles are no longer in folium's built-in tile table: the templates live
# at Stadia Maps now, so the URL is passed explicitly and a custom template must
# carry its attribution. Writing the map requests nothing; the browser does.
STAMEN_TERRAIN = "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png"
STAMEN_ATTRIBUTION = (
    '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '
    '&copy; <a href="https://stamen.com/">Stamen Design</a> '
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
)

# 1. Define Matterhorn coordinates and optimized zoom level
matterhorn_coords = [45.9766, 7.6585]
# Zoom 14 is chosen to show detailed mountain contours and surrounding valleys
zoom_level = 14 

# 2. Map Initialization: Set default tiles to Stamen Terrain
m = folium.Map(
    location=matterhorn_coords, 
    zoom_start=zoom_level, 
    tiles=STAMEN_TERRAIN,
    attr=STAMEN_ATTRIBUTION
)

# Explicitly add and name the default layer (Stamen Terrain)
folium.TileLayer(STAMEN_TERRAIN, name='Detailed Terrain',
                 attr=STAMEN_ATTRIBUTION).add_to(m)

# 3. Secondary Tile Layer (OpenTopoMap Simulation): Use OpenStreetMap but rename it
# We use folium.TileLayer to ensure it's treated as a switchable base layer
folium.TileLayer(
    tiles='OpenStreetMap', 
    name='OpenTopoMap Style'
).add_to(m)

# 4. Layer Control
folium.LayerControl().add_to(m)

# 5. Output: the HTML belongs to the project, not to the current working directory
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "alpine_terrain.html"
m.save(str(output_file))

print(f"Saved {output_file.relative_to(output_dir.parent)} centred on the Matterhorn at "
      f"zoom {zoom_level}: terrain on load, the 'OpenTopoMap Style' layer one click away.")
