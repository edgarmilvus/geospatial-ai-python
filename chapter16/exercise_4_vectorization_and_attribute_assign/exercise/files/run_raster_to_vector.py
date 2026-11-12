"""Harness for exercise 4 — mask to polygons, with the attributes a GIS asks for.

The two footprints are 200 m² and 450 m² at a one-metre pixel, so the areas are also
a pixel count: a conversion that returns square degrees, or forgets the transform,
cannot land on both. The centroids are checked in projected metres, and the
GeoPackage is re-opened to prove the CRS survived the write.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402
import rasterio  # noqa: E402

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 4 (vectorization)", FILES)
    module = load_listing(FILES / "raster_to_vector.py", "raster_to_vector")
    measured = module.main()

    # --- the raster the exercise starts from ---
    with rasterio.open(module.MASK_PATH) as src:
        h.equal(src.count, 1, "the mask is one band")
        h.equal(str(src.dtypes[0]), "uint8", "the mask is uint8")
        h.equal((src.height, src.width), (100, 100), "the mask is 100 x 100")
        h.equal(src.crs.to_string(), "EPSG:32617", "the mask carries its CRS")
        h.close(src.transform.a, 1.0, "a pixel is one metre")

    # --- the polygons ---
    h.equal(measured["feature_count"], 2, "two rectangles become two polygons")
    h.equal(measured["areas_sqm"], [200.0, 450.0], "the areas are 200 m² and 450 m²")
    h.close(measured["total_area_sqm"], 650.0, "the footprints total 650 m²")
    # The other half of the same fact: 650 pixels at one square metre each.
    h.equal(measured["mask_pixels"], 650, "the mask's 650 pixels are the 650 m²")
    h.close(measured["total_area_sqm"], measured["mask_pixels"] * 1.0,
            "area in m² equals pixels times the pixel's area", tol=1e-9)

    # --- the centroids, in metres ---
    h.equal(measured["centroids"],
            [(400030.0, 4499975.0), (400065.0, 4499932.5)],
            "the centroids are the rectangle centres in UTM metres")

    # --- the geometry sits on the right 60 x 55 m of ground ---
    h.equal(tuple(round(value, 1) for value in measured["bounds"]),
            (400020.0, 4499925.0, 400080.0, 4499980.0),
            "the union bounds are the two footprints' corners")

    # --- the file round trip ---
    h.equal(measured["reread_count"], 2, "the GeoPackage holds both features")
    h.equal(measured["reread_crs"], "EPSG:32617", "the GeoPackage carries the CRS back")
    h.equal(measured["crs"], measured["reread_crs"],
            "the written CRS is the one the mask carried")

    # --- an empty mask is an empty frame, not a crash ---
    empty_path = module.OUTPUT_DIR / "empty_mask.tif"
    module.write_binary_mask(empty_path, buildings=[])
    empty = module.raster_to_vector(empty_path)
    h.equal(len(empty), 0, "a mask with no building returns an empty frame")
    h.equal(empty.crs.to_string(), "EPSG:32617",
            "even an empty frame keeps the source CRS")

    h.write_json("raster_to_vector.json", {
        "mask": {"path": measured["mask_file"], "shape": [100, 100],
                 "crs": measured["crs"], "pixel_size_m": 1.0,
                 "building_pixels": measured["mask_pixels"]},
        "features": measured["feature_count"],
        "areas_sqm": measured["areas_sqm"],
        "total_area_sqm": measured["total_area_sqm"],
        "centroids": [list(pair) for pair in measured["centroids"]],
        "bounds": [round(float(value), 1) for value in measured["bounds"]],
        "geopackage": {"path": measured["gpkg"], "features": measured["reread_count"],
                       "crs": measured["reread_crs"]},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (vectorization)", FILES).crash())
