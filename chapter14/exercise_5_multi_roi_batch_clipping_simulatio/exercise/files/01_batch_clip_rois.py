import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import mapping, Polygon
import numpy as np
import os
import pathlib

# --- Setup: Simulate input raster and multi-geometry vector ---
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
TILE_DIR = OUTPUT_DIR / "clipped_tiles"
INPUT_RASTER_PATH = OUTPUT_DIR / "large_satellite_image.tif"

# Create a mock GeoDataFrame with multiple ROIs and unique IDs
mock_data = {
    'id': ['A001', 'B002', 'C003'],
    'geometry': [
        Polygon([(1, 1), (1, 5), (5, 5), (5, 1)]),
        Polygon([(10, 10), (10, 15), (15, 15), (15, 10)]),
        Polygon([(20, 20), (20, 25), (25, 25), (25, 20)])
    ]
}
rois_gdf = gpd.GeoDataFrame(mock_data, crs="EPSG:4326")

# Create output directory
os.makedirs(TILE_DIR, exist_ok=True)

def build_demo_raster(path):
    """Writes the 25 x 25 degree scene the three ROIs are cut out of."""
    # 250 x 250 pixels at 0.1 degrees: one raster covering every ROI in mock_data.
    transform = rasterio.transform.from_bounds(
        west=0, south=0, east=25, north=25, width=250, height=250
    )
    data = np.arange(250 * 250, dtype=np.int32).reshape(250, 250)
    with rasterio.open(
        path, "w", driver="GTiff", height=250, width=250, count=1,
        dtype="int32", crs="EPSG:4326", transform=transform, nodata=-1
    ) as dst:
        dst.write(data, 1)
    print(f"Input scene: {path.name} (250 x 250 px, 0-25 degrees)")
    return path

def batch_clip_rois(input_raster_path, rois_gdf, output_directory):
    """
    Iteratively clips a raster against multiple ROIs in a GeoDataFrame.
    """
    written = []
    try:
        # 3. Memory Management: Open the input raster ONCE outside the loop
        with rasterio.open(input_raster_path) as src:
            src_profile = src.profile
            
            # Reproject ROIs if needed (assuming src.crs is the target)
            if src.crs != rois_gdf.crs:
                rois_gdf = rois_gdf.to_crs(src.crs)

            # 1. Iterative Masking
            for index, row in rois_gdf.iterrows():
                roi_id = row['id']
                geometry = [mapping(row.geometry)]
                
                # 4. Error Logging
                print(f"\nProcessing ROI ID: {roi_id}...")
                
                try:
                    # Perform the mask operation for the single geometry
                    out_image, out_transform = mask(
                        src, 
                        geometry, 
                        crop=True, 
                        nodata=src_profile['nodata']
                    )

                    # Update profile for the new tile dimensions
                    out_meta = src_profile.copy()
                    out_meta.update({
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform
                    })

                    # 2. Dynamic Naming
                    output_filename = os.path.join(output_directory, f"clipped_tile_{roi_id}.tif")

                    # Write the output tile
                    with rasterio.open(output_filename, "w", **out_meta) as dest:
                        dest.write(out_image)

                    written.append((roi_id, out_image.shape[1], out_image.shape[2]))
                    print(f"  -> SUCCESS: Tile saved as {os.path.basename(output_filename)} "
                          f"({out_image.shape[2]} x {out_image.shape[1]} px)")

                except Exception as e:
                    print(f"  -> ERROR: Failed to clip ROI {roi_id}. Reason: {e}")

    except rasterio.RasterioIOError:
        print(f"FATAL ERROR: Could not open input raster at {input_raster_path}. Simulation stopped.")
    except Exception as e:
        print(f"FATAL ERROR: An unexpected error occurred: {e}")
    return written

if __name__ == "__main__":
    build_demo_raster(INPUT_RASTER_PATH)
    tiles = batch_clip_rois(INPUT_RASTER_PATH, rois_gdf, TILE_DIR)
    total_pixels = sum(height * width for _roi, height, width in tiles)
    print(f"\nBatch complete: {len(tiles)} of {len(rois_gdf)} ROIs clipped, "
          f"{total_pixels} pixels across the tiles.")
