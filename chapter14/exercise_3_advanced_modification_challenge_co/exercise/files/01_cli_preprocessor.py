import sys
import os
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import mapping, box
import numpy as np
import pathlib

# Core clipping function (simplified from Exercise 1)
def core_clip_logic(input_raster, mask_vector, output_raster):
    """
    Performs the actual raster clipping operation.
    """
    with rasterio.open(input_raster) as src:
        gdf = gpd.read_file(mask_vector)
        
        # Ensure CRS match
        if src.crs != gdf.crs:
            gdf = gdf.to_crs(src.crs)

        geometries = [mapping(geom) for geom in gdf.geometry]
        
        out_image, out_transform = mask(src, geometries, crop=True, nodata=src.nodata)

        out_meta = src.profile
        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        })

        with rasterio.open(output_raster, "w", **out_meta) as dest:
            dest.write(out_image)

        # Report what was cut, not just that something was written.
        print(f"SUCCESS: Raster clipped and saved to {pathlib.Path(output_raster).name}")
        print(f"  {src.width} x {src.height} px -> {out_image.shape[2]} x {out_image.shape[1]} px")
        bounds = rasterio.transform.array_bounds(out_image.shape[1], out_image.shape[2], out_transform)
        print(f"  bounds {tuple(round(value, 2) for value in bounds)}")

def parse_cli_args(argv):
    """
    Returns the three positional paths, or prints the usage and exits 1.
    """
    if len(argv) != 4:
        print("--- GeoAI Clipping Utility ---")
        print(f"Error: Expected 3 arguments, received {len(argv) - 1}.")
        print("Usage: python script_name.py <input_raster_path> <mask_vector_path> <output_raster_path>")
        sys.exit(1)
    return argv[1], argv[2], argv[3]

def build_demo_inputs(output_dir):
    """
    Writes the raster and the mask the utility is demonstrated on, and returns their paths.
    """
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 200 x 200 pixels over 10 x 10 degrees: 0.05 degrees per pixel.
    transform = rasterio.transform.from_bounds(
        west=0, south=0, east=10, north=10, width=200, height=200
    )
    data = np.arange(200 * 200, dtype=np.int32).reshape(200, 200)
    raster_path = output_dir / "utility_input.tif"
    with rasterio.open(
        raster_path, "w", driver="GTiff", height=200, width=200, count=1,
        dtype="int32", crs="EPSG:4326", transform=transform, nodata=-9999
    ) as dst:
        dst.write(data, 1)

    mask_path = output_dir / "utility_mask.geojson"
    gpd.GeoDataFrame(
        {"id": [1]}, geometry=[box(2, 2, 6, 6)], crs="EPSG:4326"
    ).to_file(mask_path, driver="GeoJSON")
    return raster_path, mask_path

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments: demonstrate the utility on a pair it generates itself.
        OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
        INPUT_RASTER, MASK_VECTOR = build_demo_inputs(OUTPUT_DIR)
        OUTPUT_RASTER = OUTPUT_DIR / "utility_clipped.tif"
        print("No arguments given; running the utility on the demo pair under output/.")
    else:
        # 1 & 2. Argument Parsing and Validation
        INPUT_RASTER, MASK_VECTOR, OUTPUT_RASTER = parse_cli_args(sys.argv)

    # 3. File Existence Check
    try:
        if not os.path.exists(INPUT_RASTER):
            raise FileNotFoundError(f"Input raster not found: {INPUT_RASTER}")
        if not os.path.exists(MASK_VECTOR):
            raise FileNotFoundError(f"Masking vector not found: {MASK_VECTOR}")
            
        # 4. Execution Flow (Diagram step) & 5. Error Handling Integration
        print(f"Processing {pathlib.Path(INPUT_RASTER).name} using mask {pathlib.Path(MASK_VECTOR).name}...")
        core_clip_logic(INPUT_RASTER, MASK_VECTOR, OUTPUT_RASTER)

    except FileNotFoundError as fnf_err:
        print(f"FATAL ERROR: Input file missing. {fnf_err}")
        sys.exit(1)
    except rasterio.RasterioIOError as rio_err:
        print(f"FATAL ERROR: Raster I/O issue (e.g., corrupted file or projection mismatch). Details: {rio_err}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        sys.exit(1)
