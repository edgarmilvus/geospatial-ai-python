import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.transform import Affine
import numpy as np
from pathlib import Path

# --- Simulation Setup (Creating a dummy input file) ---
ORIG_RES = 1.0
TARGET_RES = 10.0
WIDTH, HEIGHT = 1000, 1000
CRS = 'EPSG:32617'
DTYPE = 'float32'
SEED = 8317                      # one seed: the same terrain on every machine

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
input_path = OUTPUT_DIR / "simulated_input_dem.tif"
output_path = OUTPUT_DIR / "resampled_output_dem.tif"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create dummy data and write simulated input file: a 1 m grid sloping southward
# with a little noise, so bilinear averaging has something to smooth.
rng = np.random.default_rng(SEED)
original_dem_data = (np.indices((HEIGHT, WIDTH))[0] * 0.4
                     + rng.random((HEIGHT, WIDTH)) * 5).astype(DTYPE)
profile = {
    'driver': 'GTiff', 'width': WIDTH, 'height': HEIGHT, 'crs': CRS,
    'transform': Affine(ORIG_RES, 0.0, 100000.0, 0.0, -ORIG_RES, 500000.0),
    'count': 1, 'dtype': DTYPE, 'nodata': -9999
}
with rasterio.open(input_path, 'w', **profile) as dst:
    dst.write(original_dem_data, 1)
# ----------------------------------------------------

def calculate_new_dims(original_width, original_height, scale_factor):
    """Calculates new dimensions based on the resolution factor."""
    new_width = int(original_width / scale_factor)
    new_height = int(original_height / scale_factor)
    return new_width, new_height


def resample_and_save_dem(input_path, output_path, target_resolution):
    with rasterio.open(input_path) as src:
        # 1. Data Loading and Inspection
        print("--- Original DEM Metadata ---")
        print(f"Dimensions (W x H): {src.width} x {src.height}")
        print(f"Resolution (X, Y): {src.res}")
        print(f"CRS: {src.crs}")
        print(f"Data Type: {src.dtypes[0]}\n")

        # Calculate scale factor and new dimensions
        res_factor = target_resolution / src.res[0]
        new_width, new_height = calculate_new_dims(src.width, src.height, res_factor)

        # Calculate new geotransform (maintaining extent). The pixel size is scaled
        # by the ratio of the old grid to the new one; the origin stays put, which is
        # what keeps the two rasters covering the same ground.
        new_transform = src.transform * src.transform.scale(
            (src.width / new_width),
            (src.height / new_height)
        )

        # 2. Resampling Implementation
        resampled_data = np.empty((new_height, new_width), dtype=src.dtypes[0])

        reproject(
            source=rasterio.band(src, 1),
            destination=resampled_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=new_transform,
            dst_crs=src.crs,
            resampling=Resampling.bilinear
        )

        # 3. Statistical Verification
        original_data = src.read(1)
        print("--- Statistical Verification ---")
        print(f"Original Mean/Std: {original_data.mean():.2f} / {original_data.std():.2f}")
        print(f"Resampled Mean/Std: {resampled_data.mean():.2f} / {resampled_data.std():.2f}")
        print(f"Mean difference: {abs(original_data.mean() - resampled_data.mean()):.2f} m")

        # 4. Output TIF Generation
        new_profile = src.profile.copy()
        new_profile.update({
            'width': new_width,
            'height': new_height,
            'transform': new_transform,
        })

        with rasterio.open(output_path, 'w', **new_profile) as dst:
            dst.write(resampled_data, 1)

    print(f"\nNew grid: {new_width} x {new_height} at {target_resolution} m")
    print(f"New transform: {new_transform}")
    same_origin = (new_transform.c == src.transform.c
                   and new_transform.f == src.transform.f)
    print(f"Extent preserved: {same_origin}")
    print(f"Successfully wrote resampled DEM to {output_path.relative_to(OUTPUT_DIR.parent)}")


resample_and_save_dem(input_path, output_path, TARGET_RES)
