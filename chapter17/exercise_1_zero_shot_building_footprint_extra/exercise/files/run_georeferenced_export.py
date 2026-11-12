"""Harness for exercise 1 — a point prompt, a mask, and a georeferenced GeoPackage.

The exercise is about metadata integrity, so the checks are geographic: 100 prompt
pixels become 100 m², the polygon sits at easting 300 045 and northing 4 499 955, and
the GeoPackage reports the same CRS the GeoTIFF did. A mask with nothing in it must
export nothing, not an empty file with a CRS.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 1 (georeferenced export)", FILES)
    module = load_listing(FILES / "georeferenced_export.py", "georeferenced_export")
    measured = module.main()

    # --- the source image ---
    with rasterio.open(module.INPUT_IMAGE_PATH) as src:
        h.equal((src.height, src.width), (100, 100), "the patch is 100 x 100")
        h.equal(src.count, 3, "three bands")
        h.equal(src.crs.to_string(), "EPSG:32618", "the patch is in UTM zone 18N")
        h.close(src.transform.a, 1.0, "one metre per pixel")
        h.close(src.transform.c, 300000.0, "the west edge is easting 300 000")
        h.close(src.transform.f, 4500000.0, "the north edge is northing 4 500 000")

    # --- the mask ---
    h.equal(measured["mask_shape"], (100, 100), "the mask is at the image's resolution")
    h.equal(measured["mask_pixels"], 100, "a 10 x 10 building is 100 pixels")

    # --- the vector output ---
    h.equal(measured["feature_count"], 1, "one building becomes one feature")
    h.close(measured["area_sqm"], 100.0, "100 pixels at one metre square is 100 m²")
    h.equal(measured["input_crs"], "EPSG:32618", "the input CRS is 32618")
    h.equal(measured["output_crs"], measured["input_crs"],
            "the exported vectors carry the input CRS")
    h.equal(tuple(round(value, 1) for value in measured["bounds"]),
            (300045.0, 4499945.0, 300055.0, 4499955.0),
            "the ring is the building's 10 m square, in UTM metres")

    reread = gpd.read_file(module.OUTPUT_VECTOR_PATH)
    h.equal(reread.crs.to_epsg(), 32618, "the GeoPackage on disk says 32618")
    h.check(reread.geometry.is_valid.all(), "the written polygon is valid")
    h.equal(reread["class"].tolist(), ["building"], "the feature carries its class")

    # --- an empty mask exports nothing, and does not clobber the good file ---
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        nothing = module.export_to_geopackage(
            np.zeros((100, 100), dtype=bool), module.INPUT_IMAGE_PATH,
            module.OUTPUT_DIR / "should_not_exist.gpkg")
    h.equal(nothing, None, "a mask with no foreground returns None")
    h.contains(log.getvalue(), "No features found to export.",
               "and says so in a sentence")
    h.check(not (module.OUTPUT_DIR / "should_not_exist.gpkg").exists(),
            "no empty file is left behind")

    # --- a mask of the wrong size is refused, not silently georeferenced ---
    h.raises(lambda: module.export_to_geopackage(
        np.ones((64, 64), dtype=bool), module.INPUT_IMAGE_PATH,
        module.OUTPUT_DIR / "wrong.gpkg"), ValueError,
        "a 64 x 64 mask against a 100 x 100 image raises ValueError")

    h.write_json("georeferenced_export.json", {
        "segmenter": measured["mode"],
        "mask": {"shape": list(measured["mask_shape"]),
                 "pixels": measured["mask_pixels"]},
        "vector": {"features": measured["feature_count"],
                   "area_sqm": measured["area_sqm"],
                   "bounds": [round(float(value), 1) for value in measured["bounds"]],
                   "crs": measured["output_crs"]},
        "crs_match": measured["output_crs"] == measured["input_crs"],
        "empty_mask_features": 0,
        "geopackage": measured["gpkg"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (georeferenced export)", FILES).crash())
