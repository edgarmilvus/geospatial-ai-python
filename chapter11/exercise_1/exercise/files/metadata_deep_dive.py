"""Exercise 1 — read the five metadata properties and warn on a thin raster.

The book's solution read a path the reader did not have. This one writes the two
scenes it reads: a three-band 120 x 90 scene in UTM zone 33N, and a single-band
scene that triggers the POLA warning.
"""
import pathlib

import rasterio
import numpy as np
from rasterio.transform import from_origin

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
MULTI_BAND_PATH = OUTPUT_DIR / "metadata_scene.tif"
SINGLE_BAND_PATH = OUTPUT_DIR / "single_band_scene.tif"


def build_scene(path, count=3, width=120, height=90):
    """Write a deterministic uint16 scene and return its path."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'count': count,
        'height': height,
        'width': width,
        'crs': 'EPSG:32633',            # WGS 84 / UTM zone 33N
        'transform': from_origin(300000, 5000000, 30, 30),  # 30 m pixels
        'nodata': 0,
    }
    with rasterio.open(path, 'w', **profile) as dst:
        for band in range(1, count + 1):
            rng = np.random.default_rng(200 + band)
            dst.write(rng.integers(100, 900, (height, width),
                                   dtype=rasterio.uint16), band)
    return path


def inspect_raster_metadata(image_path: str):
    """
    Opens a geospatial raster and extracts its core spatial metadata.
    """
    try:
        # 2. Opening: Use context manager for safe resource handling
        with rasterio.open(image_path) as dataset:

            # 3. Extraction
            crs_info = dataset.crs.to_string()
            band_count = dataset.count
            width = dataset.width
            height = dataset.height
            transform_matrix = dataset.transform
            data_type = dataset.dtypes[0]

            print("--- Geospatial Metadata Deep Dive ---")
            print(f"1. Coordinate Reference System (CRS): {crs_info}")
            print(f"2. Total Number of Bands (count): {band_count}")
            print(f"3. Dimensions (Width x Height): {width} x {height}")
            print(f"4. Affine Transform Matrix:\n{transform_matrix}")
            print(f"5. Pixel Data Type (dtype): {data_type}")
            print("-" * 35)

            # 4. Verification and POLA check
            if band_count < 3:
                print(f"WARNING: Band count ({band_count}) is insufficient for standard RGB/multispectral tasks.")
                warned = True
            else:
                print("Verification successful: Raster has 3 or more bands.")
                warned = False

            return {
                "crs": crs_info,
                "count": band_count,
                "width": width,
                "height": height,
                "transform": tuple(transform_matrix)[:6],
                "dtype": data_type,
                "warned": warned,
            }

    except rasterio.RasterioIOError as e:
        # The rasterio message repeats the absolute path; the reader only needs
        # the file name and the reason.
        print(f"Error opening raster file at {pathlib.Path(image_path).name}: "
              f"{type(e).__name__}")
        return None


def main(output_dir=OUTPUT_DIR):
    output_dir = pathlib.Path(output_dir)
    multi = build_scene(output_dir / MULTI_BAND_PATH.name, count=3)
    single = build_scene(output_dir / SINGLE_BAND_PATH.name, count=1)

    print(f"--- Wrote {multi.name} and {single.name} ---\n")
    full = inspect_raster_metadata(str(multi))
    print()
    thin = inspect_raster_metadata(str(single))
    print()
    missing = inspect_raster_metadata(str(output_dir / "does_not_exist.tif"))
    return full, thin, missing


if __name__ == "__main__":
    main()
