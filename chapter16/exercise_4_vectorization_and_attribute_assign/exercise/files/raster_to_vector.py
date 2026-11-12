import numpy as np
import rasterio
import geopandas as gpd
from pathlib import Path
from shapely.geometry import shape
from rasterio.features import shapes
from rasterio.transform import Affine

# --- Configuration: a mask that already exists as a georeferenced raster ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
MASK_PATH = OUTPUT_DIR / "building_mask.tif"
GPKG_PATH = OUTPUT_DIR / "buildings.gpkg"

ROWS, COLS = 100, 100
CELL = 1.0                                   # one metre per pixel
TRANSFORM = Affine(CELL, 0.0, 400000.0, 0.0, -CELL, 4500000.0)
CRS = "EPSG:32617"                           # UTM zone 17N: metres, so area is m²

# (row_start, row_stop, col_start, col_stop) in pixel coordinates.
BUILDINGS = [(20, 30, 20, 40), (60, 75, 50, 80)]


# --- 1. The Raster the Pipeline Starts From ---
def write_binary_mask(path=MASK_PATH, buildings=BUILDINGS):
    """Write a uint8 mask with two footprints and its georeferencing."""
    mask = np.zeros((ROWS, COLS), dtype=np.uint8)
    for row_start, row_stop, col_start, col_stop in buildings:
        mask[row_start:row_stop, col_start:col_stop] = 1

    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "height": ROWS, "width": COLS, "count": 1,
        "dtype": "uint8", "crs": CRS, "transform": TRANSFORM,
        "nodata": 0, "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(mask, 1)
    print(f"Wrote {path.name}: {ROWS} x {COLS} at {CELL:.0f} m, {CRS}")
    return path, mask


# --- 2. The Conversion ---
def raster_to_vector(binary_mask_path, output_gpkg_path=None):
    """Binary mask on disk -> GeoDataFrame with area and centroid per polygon.

    The transform comes from the file, never from the caller: that is what keeps the
    polygons on the ground where the mask was.
    """
    with rasterio.open(binary_mask_path) as src:
        image = src.read(1)
        transform = src.transform
        crs = src.crs

        if image.dtype != np.uint8:
            raise ValueError(f"expected a uint8 mask, got {image.dtype}")

        features = []
        # connectivity=8 joins pixels that touch at a corner; 4 would split a
        # staircase edge into a chain of one-pixel polygons.
        for geom, value in shapes(image, transform=transform, connectivity=8):
            if value != 1:            # only the building class becomes a feature
                continue
            polygon = shape(geom)
            if polygon.is_empty:
                continue

            centroid = polygon.centroid
            features.append({
                "geometry": polygon,
                # The CRS is projected in metres, so `.area` is square metres. In
                # EPSG:4326 the same call returns square degrees, which is not an area.
                "area_sqm": round(polygon.area, 2),
                "centroid_x": round(centroid.x, 2),
                "centroid_y": round(centroid.y, 2),
            })

        if not features:
            return gpd.GeoDataFrame({"area_sqm": [], "centroid_x": [], "centroid_y": []},
                                    geometry=[], crs=crs)

        gdf = gpd.GeoDataFrame(features, crs=crs)
        if output_gpkg_path is not None:
            gdf.to_file(output_gpkg_path, driver="GPKG")
        return gdf


# --- 3. Report ---
def main():
    path, mask = write_binary_mask()
    print(f"Mask pixels: {int(mask.sum())} of {mask.size}")

    gdf = raster_to_vector(path, GPKG_PATH)
    print(f"\n{len(gdf)} building polygons, CRS {gdf.crs.to_string()}")
    for index, row in gdf.iterrows():
        print(f"  #{index}: area {row['area_sqm']:.0f} m², "
              f"centroid ({row['centroid_x']:.1f}, {row['centroid_y']:.1f})")
    print(f"Total footprint: {gdf['area_sqm'].sum():.0f} m²")
    print(f"Union bounds: {tuple(round(float(v), 1) for v in gdf.total_bounds)}")

    # Read the file back: the CRS in the GeoPackage is the one a GIS will use.
    reread = gpd.read_file(GPKG_PATH)
    print(f"\nRe-read {GPKG_PATH.name}: {len(reread)} features, "
          f"CRS {reread.crs.to_string()}, valid geometries "
          f"{int(reread.geometry.is_valid.sum())}/{len(reread)}")
    with rasterio.open(path) as src:
        source_epsg = src.crs.to_epsg()
    print("Georeferencing integrity check: "
          f"{'PASSED' if reread.crs.to_epsg() == source_epsg else 'FAILED'}")

    return {
        "mask_pixels": int(mask.sum()),
        "mask_shape": (ROWS, COLS),
        "feature_count": len(gdf),
        "areas_sqm": sorted(float(value) for value in gdf["area_sqm"]),
        "total_area_sqm": float(gdf["area_sqm"].sum()),
        "centroids": sorted((float(x), float(y)) for x, y in
                            zip(gdf["centroid_x"], gdf["centroid_y"])),
        "bounds": tuple(float(value) for value in gdf.total_bounds),
        "crs": gdf.crs.to_string(),
        "reread_crs": reread.crs.to_string(),
        "reread_count": len(reread),
        "gpkg": GPKG_PATH.name,
        "mask_file": path.name,
    }


if __name__ == "__main__":
    main()
