"""Exercise 5 — inherit the input's spatial profile, change the output's data type.

The classification map is eight classes (0-7) with 255 for unclassified pixels. It
inherits width, height, CRS and transform from the four-band input, and overrides
count, dtype, nodata and interleave. The listing writes the map and reads it back,
because a profile that opens is the only evidence the template is valid.
"""
import copy
import pathlib

import rasterio
from rasterio.transform import from_origin
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
INPUT_PATH = OUTPUT_DIR / "classification_input.tif"
OUTPUT_PATH = OUTPUT_DIR / "classification_map.tif"
SCENE_WIDTH, SCENE_HEIGHT, SCENE_BANDS = 240, 180, 4
UNCLASSIFIED_ROWS = 20


def build_input(path=INPUT_PATH):
    """A four-band uint16 scene, the shape a segmentation model would receive."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'count': SCENE_BANDS,
        'height': SCENE_HEIGHT,
        'width': SCENE_WIDTH,
        'crs': 'EPSG:32612',
        'transform': from_origin(500000, 4400000, 30, 30),
        'nodata': 0,
    }
    with rasterio.open(path, 'w', **profile) as dst:
        for band in range(1, SCENE_BANDS + 1):
            rng = np.random.default_rng(600 + band)
            dst.write(rng.integers(100, 900, (SCENE_HEIGHT, SCENE_WIDTH),
                                   dtype=rasterio.uint16), band)
    return path


def classification_array():
    """Eight classes by pixel position, with the top rows left unclassified."""
    rows = np.arange(SCENE_HEIGHT)[:, None]
    cols = np.arange(SCENE_WIDTH)[None, :]
    classes = ((rows + cols) % 8).astype(np.uint8)
    classes[:UNCLASSIFIED_ROWS, :] = 255
    return classes


def create_output_template(image_path: str):
    """
    Creates a modified Rasterio metadata profile suitable for writing a
    single-band classification map based on the input image's spatial context.
    """
    try:
        with rasterio.open(image_path) as src:
            # 1. Metadata Inheritance
            # Use copy.deepcopy to ensure modifications don't affect the source profile
            input_profile = src.profile
            output_classification_profile = copy.deepcopy(input_profile)

            # 2. Metadata Modification
            output_classification_profile.update({
                'count': 1,                         # Change 1: Single band output
                'dtype': rasterio.uint8,            # Change 2: Classification map data type
                'nodata': 255,                      # Change 3: Set nodata value
                'interleave': 'band',               # Change 4: Standard interleave for single band
                'compress': 'deflate'               # Optional: Add compression
            })

            # 3. Verification
            print("--- GeoTIFF Template Creation ---")
            print("\nOriginal Input Profile Snippet:")
            print(f"  Count: {input_profile['count']}, Dtype: {input_profile['dtype']}, Nodata: {input_profile.get('nodata')}")

            print("\nModified Output Classification Profile Snippet:")
            print(f"  Count: {output_classification_profile['count']}")
            print(f"  Dtype: {output_classification_profile['dtype']}")
            print(f"  Nodata: {output_classification_profile.get('nodata')}")
            print(f"  Interleave: {output_classification_profile['interleave']}")

            return input_profile, output_classification_profile

    except rasterio.RasterioIOError as e:
        print(f"Error opening raster file: {pathlib.Path(image_path).name}")
        return None, None


def main():
    input_path = build_input()
    print(f"--- Wrote {input_path.name}: {SCENE_WIDTH} x {SCENE_HEIGHT}, "
          f"{SCENE_BANDS} bands ---")
    input_profile, output_profile = create_output_template(str(input_path))

    classes = classification_array()
    with rasterio.open(OUTPUT_PATH, 'w', **output_profile) as dst:
        dst.write(classes, 1)
    print(f"\n--- Wrote {OUTPUT_PATH.name} with {len(np.unique(classes))} values ---")

    with rasterio.open(OUTPUT_PATH) as written:
        read_back = written.read(1)
        print(f"Read back: count={written.count}, dtype={written.dtypes[0]}, "
              f"nodata={written.nodata}, shape={read_back.shape}")
        print(f"Class values: {sorted(np.unique(read_back).tolist())}")

    return {
        "input_profile": input_profile,
        "output_profile": output_profile,
        "classes": classes,
        "read_back": read_back,
    }


if __name__ == "__main__":
    main()
