"""Harness for example 2 — box prompts in, georeferenced polygons out.

Two halves are graded. The masks must be tighter than the boxes they came from (that
is the refinement the box prompt buys), and the polygons must be in metres on the
tile's grid: 41 400 m² for the largest warehouse is 230 x 180 pixels at one metre,
and its corners are where the affine transform says they are.
"""
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import geopandas as gpd  # noqa: E402
import rasterio  # noqa: E402

from harness import Harness, load_listing  # noqa: E402

# Rows and columns of the four roofs the tile draws, in prompt order.
ROOFS = [(210, 440, 160, 340), (110, 290, 510, 690),
         (610, 740, 810, 940), (710, 840, 110, 240)]
EXPECTED_AREAS = [float((r1 - r0) * (c1 - c0)) for r0, r1, c0, c1 in ROOFS]


def main():
    h = Harness("example 2 (SAM to GeoJSON)", FILES)
    module = load_listing(FILES / "sam_to_geojson.py", "sam_to_geojson")
    measured = module.run_sam_geo_segmentation()

    # --- the tile ---
    h.equal(measured["image_shape"], (1000, 1000, 3), "the park is 1000 x 1000 RGB")
    h.equal(measured["crs"], "EPSG:32617", "the tile is in UTM zone 17N")
    with rasterio.open(module.IMAGE_PATH) as src:
        h.equal(src.count, 3, "three bands on disk")
        h.close(src.transform.a, 1.0, "one metre per pixel")
        h.close(src.transform.c, 500000.0, "the west edge is easting 500 000")
        h.close(src.transform.f, 4200000.0, "the north edge is northing 4 200 000")

    # --- one mask per prompt ---
    h.equal(measured["mask_shape"], (4, 1000, 1000),
            "four boxes produce four full-resolution masks")
    h.equal(measured["mask_areas"], [int(area) for area in EXPECTED_AREAS],
            "each mask covers exactly its warehouse, one pixel per square metre")

    # The refinement: a mask is smaller than the box that prompted it, and inside it.
    for index, (box, area) in enumerate(zip(module.WAREHOUSE_PROMPTS, EXPECTED_AREAS)):
        box_area = float((box[2] - box[0]) * (box[3] - box[1]))
        h.check(area < box_area,
                "mask %d is tighter than its %.0f m² box (%.0f m²)"
                % (index, box_area, area))

    # --- the polygons ---
    h.equal(measured["feature_count"], 4, "four masks vectorize to four polygons")
    h.equal([round(value, 1) for value in measured["areas_sqm"]],
            [round(value, 1) for value in EXPECTED_AREAS],
            "the polygon areas are the four roofs, in prompt order")
    h.close(measured["total_area_sqm"], 107_600.0,
            "the four roofs total 107 600 m²", tol=1.0)

    # --- the georeferencing ---
    west, south, east, north = measured["bounds"]
    h.close(west, 500000.0 + 110, "the westernmost roof starts 110 m into the tile")
    h.close(east, 500000.0 + 940, "the easternmost roof ends 940 m in")
    h.close(north, 4200000.0 - 110, "the northernmost roof starts 110 m down")
    h.close(south, 4200000.0 - 840, "the southernmost roof ends 840 m down")

    # --- the file ---
    collection = json.loads((module.OUTPUT_DIR / measured["geojson"]).read_text())
    h.equal(collection["type"], "FeatureCollection", "the output is a FeatureCollection")
    h.equal(len(collection["features"]), 4, "the file holds four features")
    h.equal(collection["crs"]["properties"]["name"], "EPSG:32617",
            "the file states its CRS")
    h.equal([feature["properties"]["prompt_id"] for feature in collection["features"]],
            [0, 1, 2, 3], "each polygon remembers the prompt that produced it")
    h.equal({feature["properties"]["type"] for feature in collection["features"]},
            {"Industrial Warehouse"}, "every feature carries the class label")

    reread = gpd.read_file(module.OUTPUT_DIR / measured["geojson"])
    h.equal(reread.crs.to_epsg(), 32617, "a GIS reading the file gets metres, not degrees")
    h.equal(sorted(round(value, 1) for value in reread.area),
            sorted(round(value, 1) for value in EXPECTED_AREAS),
            "Shapely recomputes the same areas from the written rings")
    h.check(reread.geometry.is_valid.all(), "every polygon is valid geometry")

    h.write_json("sam_to_geojson.json", {
        "segmenter": measured["mode"],
        "tile": {"shape": list(measured["image_shape"]), "crs": measured["crs"],
                 "pixel_size_m": 1.0, "origin": [500000.0, 4200000.0]},
        "prompts": module.WAREHOUSE_PROMPTS.tolist(),
        "masks": {"count": measured["mask_shape"][0],
                  "areas_px": measured["mask_areas"]},
        "features": measured["feature_count"],
        "areas_sqm": [round(value, 1) for value in measured["areas_sqm"]],
        "total_area_sqm": round(measured["total_area_sqm"], 1),
        "bounds": [round(float(value), 1) for value in measured["bounds"]],
        "geojson": measured["geojson"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (SAM to GeoJSON)", FILES).crash())
