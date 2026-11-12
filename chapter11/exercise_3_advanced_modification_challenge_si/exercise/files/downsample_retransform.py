"""Exercise 3 — downsample by four and fix the transform that goes with it.

`out_shape` asks Rasterio to resample on read. The new transform is the old one
scaled by the factor, which is the step that keeps the coarse pixels over the same
ground: the origin stays, the pixel size grows fourfold, the bounds do not move.
"""
import pathlib

import rasterio
from rasterio import Affine
import numpy as np

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
SCENE_PATH = OUTPUT_DIR / "downsample_scene.tif"
SCENE_WIDTH, SCENE_HEIGHT, SCENE_BANDS = 960, 720, 3


def build_scene(path=SCENE_PATH):
    """A three-band scene whose sides divide by four, at 10 m resolution."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        'driver': 'GTiff',
        'dtype': rasterio.uint16,
        'count': SCENE_BANDS,
        'height': SCENE_HEIGHT,
        'width': SCENE_WIDTH,
        'crs': 'EPSG:32618',
        'transform': rasterio.transform.from_origin(600000, 4200000, 10, 10),
        'nodata': 0,
    }
    with rasterio.open(path, 'w', **profile) as dst:
        for band in range(1, SCENE_BANDS + 1):
            rng = np.random.default_rng(400 + band)
            dst.write(rng.integers(100, 900, (SCENE_HEIGHT, SCENE_WIDTH),
                                   dtype=rasterio.uint16), band)
    return path


def downsample_and_retransform(image_path: str, factor: int = 4):
    """
    Reads the raster, downsamples it by a factor, and calculates the corresponding
    new affine transformation matrix.
    """
    try:
        with rasterio.open(image_path) as src:
            # 1. Initialization
            original_width = src.width
            original_height = src.height
            original_transform = src.transform
            original_crs = src.crs

            # 2. New Dimensions (ensuring integer results)
            downsampled_width = original_width // factor
            downsampled_height = original_height // factor

            new_out_shape = (downsampled_height, downsampled_width)

            # 3. Reading with Resampling
            # Reading with out_shape forces Rasterio to resample the data
            downsampled_data = src.read(
                out_shape=new_out_shape,
                resampling=rasterio.enums.Resampling.nearest # Simple resampling method
            )

            # 4. New Transform Calculation (CRITICAL)
            # The dataset keeps its bounds; only the pixel grid gets coarser, so
            # scaling the original transform by the factor is exact. Passing the
            # source CRS as the destination CRS to `calculate_default_transform`
            # works by accident and loses the origin on a rotated grid.
            new_transform = original_transform * Affine.scale(factor, factor)

            # 5. Verification
            print("--- Downsampling Verification ---")
            print(f"Original dimensions: {original_width}x{original_height}")
            print(f"Resampled data shape (Bands, H, W): {downsampled_data.shape}")

            # Check the pixel size components (a=x resolution, e=y resolution)
            print(f"\nOriginal Transform (a, e): {original_transform.a:.4f}, {original_transform.e:.4f}")
            print(f"New Downsampled Transform (a, e): {new_transform.a:.4f}, {new_transform.e:.4f}")

            # Verify that the pixel size has increased by the factor
            if abs(new_transform.a / original_transform.a) == factor:
                print(f"Verification successful: Pixel size increased by factor of {factor}.")

            return {
                "data": downsampled_data,
                "transform": new_transform,
                "original_transform": original_transform,
                "original_shape": (original_height, original_width),
                "crs": original_crs,
            }

    except rasterio.RasterioIOError as e:
        print(f"Error opening raster file: {e}")
        return None


def main():
    path = build_scene()
    print(f"--- Wrote {path.name}: {SCENE_WIDTH} x {SCENE_HEIGHT} ---")
    result = downsample_and_retransform(path)
    return result


if __name__ == "__main__":
    main()
