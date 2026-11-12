import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import mapping, box
import numpy as np
import pathlib

def clip_raster_by_vector(input_raster_path, mask_vector_path, output_raster_path):
    """
    Clips a raster using a vector boundary, handling CRS transformation automatically.
    """
    # 1. Load the masking vector geometry
    try:
        gdf = gpd.read_file(mask_vector_path)
    except Exception as e:
        print(f"Error loading vector file: {e}")
        return

    with rasterio.open(input_raster_path) as src:
        # 2. CRS Handling: Check and reproject if necessary
        if src.crs != gdf.crs:
            print(f"Reprojecting vector from {gdf.crs} to raster CRS {src.crs}...")
            # Reproject the GeoDataFrame to match the raster's CRS
            gdf = gdf.to_crs(src.crs)

        # 3. Extract geometries (required format for rasterio.mask)
        geometries = [mapping(geom) for geom in gdf.geometry]

        # 4. Perform the mask operation
        # crop=True ensures the output bounds match the clipped area
        # filled=True ensures areas outside the mask are filled with nodata
        out_image, out_transform = mask(
            src, 
            geometries, 
            crop=True, 
            filled=True, 
            nodata=src.nodata if src.nodata is not None else 0 # Use existing nodata or default to 0
        )

        # 5. Metadata Preservation: Update the profile
        out_meta = src.profile
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": src.nodata if src.nodata is not None else 0
        })

        # 6. Write the output raster
        with rasterio.open(output_raster_path, "w", **out_meta) as dest:
            dest.write(out_image)

    print(f"Successfully clipped raster saved to: {pathlib.Path(output_raster_path).name}")

# --- Demo inputs: one 6 km UTM tile and one ROI handed over in WGS 84 ---

def build_demo_inputs(output_dir):
    """Writes a projected raster and a geographic mask, and returns their paths."""
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # A 600 x 600 pixel tile at 10 m: UTM zone 10N easting 500 000, northing 4 206 000.
    transform = rasterio.transform.from_origin(500000, 4206000, 10, 10)
    data = np.arange(600 * 600, dtype=np.int32).reshape(600, 600)
    raster_path = output_dir / "utm_tile.tif"
    with rasterio.open(
        raster_path, "w", driver="GTiff", height=600, width=600, count=1,
        dtype="int32", crs="EPSG:32610", transform=transform, nodata=-9999
    ) as dst:
        dst.write(data, 1)

    # The same 2 km x 2 km ROI, stored in WGS 84 on purpose: the function must reproject it.
    roi = gpd.GeoDataFrame(
        {"name": ["delta_roi"]},
        geometry=[box(500500, 4200500, 502500, 4202500)],
        crs="EPSG:32610",
    ).to_crs("EPSG:4326")
    mask_path = output_dir / "roi_wgs84.geojson"
    roi.to_file(mask_path, driver="GeoJSON")
    print(f"Demo raster: {raster_path.name} (600 x 600 px, EPSG:32610)")
    print(f"Demo mask: {mask_path.name} (EPSG:4326, 2 km x 2 km)")
    return raster_path, mask_path

if __name__ == "__main__":
    OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
    raster_path, mask_path = build_demo_inputs(OUTPUT_DIR)
    output_path = OUTPUT_DIR / "utm_tile_clipped.tif"

    clip_raster_by_vector(raster_path, mask_path, output_path)

    with rasterio.open(output_path) as clipped:
        print(f"Clipped raster: {clipped.count} band(s), {clipped.width} x {clipped.height} px, "
              f"CRS {clipped.crs.to_string()}, nodata {clipped.nodata}")
        print(f"Bounds: {tuple(round(value, 1) for value in clipped.bounds)}")
