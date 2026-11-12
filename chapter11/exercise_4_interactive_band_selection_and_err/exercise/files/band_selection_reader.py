"""Exercise 4 — pick one band, refuse bad input, never hang on a prompt.

The reader accepts a band number as an argument so it can be driven by a test; with
no argument it prompts only when stdin is a terminal and otherwise reads band 1
with a printed note. Both bad branches — text and out-of-range — return a status
instead of raising or looping forever.
"""
import pathlib
import sys

import rasterio
from rasterio.transform import from_origin
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
SCENE_PATH = OUTPUT_DIR / "band_selection_scene.tif"
SCENE_WIDTH, SCENE_HEIGHT, SCENE_BANDS = 200, 150, 4


def build_scene(path=SCENE_PATH):
    """A four-band scene, each band with its own value range."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'count': SCENE_BANDS,
        'height': SCENE_HEIGHT,
        'width': SCENE_WIDTH,
        'crs': 'EPSG:32611',
        'transform': from_origin(350000, 4100000, 15, 15),
        'nodata': 0,
    }
    with rasterio.open(path, 'w', **profile) as dst:
        for band in range(1, SCENE_BANDS + 1):
            rng = np.random.default_rng(500 + band)
            # Band n lives in [100*n, 100*n + 400), so a mixed-up band is visible.
            dst.write(rng.integers(100 * band, 100 * band + 400,
                                   (SCENE_HEIGHT, SCENE_WIDTH),
                                   dtype=rasterio.uint16), band)
    return path


def parse_band_choice(user_input, band_count):
    """Return (index, error) for one answer: exactly one of the two is None."""
    try:
        # Attempt 1: Non-Integer Input Check (ValueError)
        band_index = int(user_input)
    except (TypeError, ValueError):
        return None, "ERROR: Invalid input format. Please enter a whole number (integer)."

    # Attempt 2: Out-of-Range Band Check (POLA)
    if not (1 <= band_index <= band_count):
        return None, (f"ERROR: Band number {band_index} is out of range. "
                      f"Please enter an integer between 1 and {band_count}.")
    return band_index, None


def interactive_band_reader(image_path: str, choice=None):
    """
    Prompts the user for a band number and reads the corresponding band,
    handling input validation and range errors.
    """
    try:
        with rasterio.open(image_path) as src:
            band_count = src.count

            # POLA: Inform user of the valid range immediately
            print(f"The dataset has {band_count} bands (1-indexed).")

            if choice is None:
                if not sys.stdin.isatty():
                    # No keyboard: a documented default beats a hung process.
                    print("No terminal attached: reading band 1.")
                    choice = "1"
                else:
                    choice = input(f"Enter the band number (1 to {band_count}): ")

            band_index, error = parse_band_choice(choice, band_count)
            if error:
                print(error)
                return {"band": None, "error": error}

            # Reading Operation
            # Reading a single band results in a (Height, Width) array
            selected_band_data = src.read(band_index)

            # Verification
            print("\n--- Band Reading Successful ---")
            print(f"Band {band_index} loaded.")
            print(f"Array Shape (H, W): {selected_band_data.shape}")
            print(f"Minimum Pixel Value: {selected_band_data.min()}")
            print(f"Maximum Pixel Value: {selected_band_data.max()}")

            return {
                "band": band_index,
                "shape": selected_band_data.shape,
                "min": int(selected_band_data.min()),
                "max": int(selected_band_data.max()),
                "error": None,
            }

    except rasterio.RasterioIOError as e:
        print(f"Fatal Error: Could not open raster file: {pathlib.Path(image_path).name}")
        return {"band": None, "error": type(e).__name__}


def main():
    path = build_scene()
    print(f"--- Wrote {path.name}: {SCENE_WIDTH} x {SCENE_HEIGHT}, {SCENE_BANDS} bands ---")
    valid = interactive_band_reader(path, choice=2)
    print()
    text = interactive_band_reader(path, choice="NIR")
    print()
    outside = interactive_band_reader(path, choice=9)
    print()
    default = interactive_band_reader(path)
    return valid, text, outside, default


if __name__ == "__main__":
    main()
