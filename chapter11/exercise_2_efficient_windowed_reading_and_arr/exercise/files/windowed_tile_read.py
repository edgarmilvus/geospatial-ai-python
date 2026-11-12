"""Exercise 2 — read a 512-pixel tile from the centre of the scene, nothing more.

The solution computes the window, reads three of the four bands through it, casts
to float32 for the model, and raises a readable error when the tile is larger than
the image instead of letting GDAL return a short read.
"""
import pathlib

import rasterio
from rasterio.windows import Window
from rasterio.transform import from_origin
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
SCENE_PATH = OUTPUT_DIR / "windowed_scene.tif"
SCENE_WIDTH, SCENE_HEIGHT, SCENE_BANDS = 800, 600, 4


def build_scene(path=SCENE_PATH):
    """A four-band 800 x 600 scene at 20 m resolution, deterministic."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'count': SCENE_BANDS,
        'height': SCENE_HEIGHT,
        'width': SCENE_WIDTH,
        'crs': 'EPSG:32610',
        'transform': from_origin(400000, 4600000, 20, 20),
        'nodata': 0,
    }
    with rasterio.open(path, 'w', **profile) as dst:
        for band in range(1, SCENE_BANDS + 1):
            rng = np.random.default_rng(300 + band)
            dst.write(rng.integers(200, 1200, (SCENE_HEIGHT, SCENE_WIDTH),
                                   dtype=rasterio.uint16), band)
    return path


def read_centered_tile(image_path: str, tile_size: int = 512):
    """
    Reads a centered tile of specified size from the first three bands.
    """
    try:
        with rasterio.open(image_path) as src:
            src_width = src.width
            src_height = src.height

            # POLA Check: Ensure image is large enough
            if src_width < tile_size or src_height < tile_size:
                raise ValueError(f"Image dimensions ({src_width}x{src_height}) "
                                 f"are too small for the requested tile size ({tile_size}).")

            # 1. Window Calculation: Find the top-left corner for centering
            start_col = (src_width // 2) - (tile_size // 2)
            start_row = (src_height // 2) - (tile_size // 2)

            # 2. Window Definition (col_off, row_off, width, height)
            tile_window = Window(start_col, start_row, tile_size, tile_size)

            # 3. Reading Operation: Read the first three bands (1-indexed)
            # 5. Data Type Consistency: Read and explicitly cast to float32
            tile_data = src.read(
                indexes=(1, 2, 3),
                window=tile_window,
                out_dtype=np.float32
            )

            # 4. Output Verification
            print(f"Tile successfully read using windowing.")
            print(f"Window defined: {tile_window}")
            print(f"Resulting NumPy array shape (Bands, H, W): {tile_data.shape}")
            print(f"Resulting NumPy array dtype: {tile_data.dtype}")

            return {
                "data": tile_data,
                "window": tile_window,
                "transform": src.window_transform(tile_window),
                "source_dtype": src.dtypes[0],
                "source_count": src.count,
            }

    except (rasterio.RasterioIOError, ValueError) as e:
        # Graceful error handling for boundary/file issues (POLA)
        print(f"Error during tile reading: {e}")
        return None


def main():
    path = build_scene()
    print(f"--- Wrote {path.name}: {SCENE_WIDTH} x {SCENE_HEIGHT}, {SCENE_BANDS} bands ---")
    tile = read_centered_tile(path)
    print()
    # The boundary the exercise asks the student to handle.
    too_big = read_centered_tile(path, tile_size=700)
    return tile, too_big


if __name__ == "__main__":
    main()
