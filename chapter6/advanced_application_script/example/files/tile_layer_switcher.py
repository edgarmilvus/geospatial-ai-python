import folium
import pathlib
from datetime import datetime

# --- 1. Configuration Constants ---
# Define the project focus area (e.g., San Francisco Bay Area)
TARGET_COORDINATES = (37.7749, -122.4194)
INITIAL_ZOOM = 12

# The HTML file belongs to the project, not to the folder the script was started from.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILENAME = OUTPUT_DIR / "Infrastructure_Tile_Switcher.html"

# The three Stamen styles left folium's built-in tile table when the tiles moved to
# Stadia Maps, so the template is passed explicitly, and a custom template must
# bring its attribution with it. Nothing is downloaded here: folium only writes the
# JavaScript that would request these tiles in the reader's browser.
STAMEN_ATTRIBUTION = (
    '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '
    '&copy; <a href="https://stamen.com/">Stamen Design</a> '
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
)

# Define the standard tile layer dictionary for different visualization needs
# Key: Display Name (for LayerControl), Value: Folium Tile String Identifier
TILE_LAYERS = {
    "OpenStreetMap (Default)": "OpenStreetMap",
    "Stamen Toner (High Contrast Roads)":
        "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png",
    "Stamen Terrain (Topography Focus)":
        "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
    "CartoDB Positron (Light Background)": "CartoDB Positron",
    "CartoDB DarkMatter (Night Mode/Data Focus)": "CartoDB dark_matter"
}

def stamen_attribution(tile_string: str):
    """
    Returns the attribution a tile string needs, or None for a built-in provider.

    A name from folium's built-in table (\"OpenStreetMap\", \"CartoDB Positron\")
    arrives with its own attribution. A URL template does not, and folium refuses
    to build a layer without one.
    """
    if tile_string.startswith("http"):
        return STAMEN_ATTRIBUTION
    return None

def create_base_map(location: tuple, zoom_start: int, default_tiles: str = "OpenStreetMap") -> folium.Map:
    """
    Initializes the core Folium map object centered on the target location.
    
    Args:
        location: (latitude, longitude) tuple for map center.
        zoom_start: Initial zoom level integer.
        default_tiles: The initial tile set to display upon loading.
        
    Returns:
        A configured folium.Map object.
    """
    # Instantiate the map object, defining its initial state and default tile set
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        tiles=default_tiles,
        attr=stamen_attribution(default_tiles),
        # Setting control_scale=True adds a scale indicator to the map
        control_scale=True 
    )
    return m

def add_multiple_tile_layers(folium_map: folium.Map, layers: dict) -> None:
    """
    Iterates through a dictionary of tile layers and adds them to the map 
    as selectable options, excluding the default layer already loaded.
    
    Args:
        folium_map: The existing Folium Map object.
        layers: Dictionary mapping display names to Folium tile strings.
    """
    # Identify the key of the layer already set as the map's default tile set
    default_key = list(layers.keys())[0] 
    
    for display_name, tile_string in layers.items():
        if display_name != default_key:
            # Create a TileLayer object and attach it to the map.
            # CRITICAL: overlay=False ensures this is treated as a BASE LAYER, 
            # meaning only one can be active at a time.
            folium.TileLayer(
                tiles=tile_string,
                name=display_name,
                overlay=False, 
                control=True,  # Ensure it appears in the LayerControl widget
                attr=stamen_attribution(tile_string)
            ).add_to(folium_map)

def finalize_and_save_map(folium_map: folium.Map, filename: pathlib.Path) -> str:
    """
    Adds the LayerControl interface and saves the final map to an HTML file.
    
    Args:
        folium_map: The fully configured Folium Map object.
        filename: The desired output path.
        
    Returns:
        Confirmation message string detailing the output location and size.
    """
    # Add the LayerControl object. This automatically scans the map for 
    # all TileLayers (Base Layers) and FeatureGroups (Overlays).
    folium.LayerControl(position='topright', collapsed=False).add_to(folium_map)
    
    # Save the map as a standalone HTML file containing all necessary CSS/JS
    folium_map.save(str(filename))
    
    # Return confirmation details, with the path relative to the project so the
    # message carries no machine's home directory.
    file_path = filename.relative_to(filename.parent.parent)
    size_kb = filename.stat().st_size / 1024
    
    return f"Map successfully saved to {file_path}. Size: {size_kb:.2f} KB."

# --- 4. Main Execution Block ---
if __name__ == "__main__":
    print(f"--- Starting Folium Map Generation ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    try:
        # Step 1: Initialize the core map structure
        base_map = create_base_map(
            location=TARGET_COORDINATES, 
            zoom_start=INITIAL_ZOOM,
            default_tiles=TILE_LAYERS[list(TILE_LAYERS.keys())[0]] # Use the first defined layer as default
        )
        print(f"Base map initialized at {TARGET_COORDINATES} with zoom {INITIAL_ZOOM}.")
        
        # Step 2: Add the remaining tile layers to the map object
        add_multiple_tile_layers(base_map, TILE_LAYERS)
        print(f"Added {len(TILE_LAYERS) - 1} selectable tile layers on top of the default.")
        
        # Step 3: Finalize and export the map
        result_message = finalize_and_save_map(base_map, OUTPUT_FILENAME)
        
        print("\n--- Process Complete ---")
        print(result_message)
        print("Open the HTML file in any web browser to view the interactive map.")

    except Exception as e:
        print(f"An error occurred during map generation: {e}")
