"""Harness for example 2 — the raster-to-vector bridge on a georeferenced chip.

The model is a stand-in for the trained U-Net, so what is graded is the other half:
the logits cross zero exactly where the roofs are, the mask covers the 11 900 roof
pixels, `rasterio.features.shapes` turns them into five polygons, and every ring is
in metres on the chip's own grid.
"""
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import numpy as np
    import rasterio
except ImportError:
    print("skip    example 2 (raster to vector) — pip install -r requirements-ml.txt")
    print("__VERDICT__ 0 0 example 2 (raster to vector)", file=sys.stderr)
    raise SystemExit(0)

from harness import Harness, load_listing  # noqa: E402

# The five roofs of the simulation, in square metres: pixels x (10 m)^2.
EXPECTED_AREAS = sorted([2400 * 100, 1500 * 100, 1600 * 100, 4800 * 100, 1600 * 100])


def main():
    h = Harness("example 2 (raster to vector)", FILES)
    module = load_listing(FILES / "raster_to_vector_pipeline.py",
                          "raster_to_vector_pipeline")

    tile_path = module.OUTPUT_DIR / "industrial_tile.tif"
    result = module.run_geo_inference(
        tile_path, module.OUTPUT_DIR / "detected_buildings.geojson")

    # --- the input chip ---
    h.equal(result["image_shape"], (512, 512, 3), "the chip is 512 x 512 RGB")
    h.equal(result["crs"], "EPSG:32617", "the chip is in UTM zone 17N")
    with rasterio.open(tile_path) as src:
        h.equal(src.count, 3, "the written chip carries three bands")
        h.close(src.transform.a, 10.0, "a pixel is 10 m across")
        h.close(src.transform.c, 600000.0, "the west edge is easting 600 000")
        h.close(src.transform.f, 4200000.0, "the north edge is northing 4 200 000")

    # --- the logits: a real classifier output, not a probability ---
    h.check(result["logit_min"] < -4.0,
            "background pixels sit well below zero (%.2f)" % result["logit_min"])
    h.check(result["logit_max"] > 2.0,
            "roof pixels sit above zero (%.2f)" % result["logit_max"])

    # --- the mask ---
    # 2400 + 1500 + 1600 + 4800 + 1600 roof pixels, and nothing else.
    h.equal(result["mask_pixels"], 11900, "the mask covers exactly the 11 900 roof pixels")

    # --- the vector output ---
    h.equal(result["feature_count"], 5, "five connected roofs become five polygons")
    h.close(result["total_area_m2"], 1_190_000.0,
            "1.19 km² of roof, at 100 m² per pixel", tol=1.0)

    collection = json.loads((module.OUTPUT_DIR / "detected_buildings.geojson")
                            .read_text(encoding="utf-8"))
    h.equal(collection["type"], "FeatureCollection", "the file is a FeatureCollection")
    h.equal(collection["crs"]["properties"]["name"], "EPSG:32617",
            "the collection states its CRS")
    areas = sorted(feature["properties"]["area_m2"] for feature in collection["features"])
    h.equal(areas, [float(value) for value in EXPECTED_AREAS],
            "the five areas are the five rectangle areas")
    h.equal([feature["properties"]["class"] for feature in collection["features"]],
            [1, 1, 1, 1, 1], "only the building class is written out")
    h.equal([feature["properties"]["building_id"] for feature in collection["features"]],
            [0, 1, 2, 3, 4], "the polygons are numbered in order")

    # --- the geometry is on the chip's grid, in metres ---
    min_x, min_y, max_x, max_y = 1e18, 1e18, -1e18, -1e18
    for feature in collection["features"]:
        geometry = feature["geometry"]
        h.equal(geometry["type"], "Polygon", "each feature is a polygon")
        ring = geometry["coordinates"][0]
        h.equal(ring[0], ring[-1], "each ring is closed")
        xs = [point[0] for point in ring]
        ys = [point[1] for point in ring]
        min_x, max_x = min(min_x, min(xs)), max(max_x, max(xs))
        min_y, max_y = min(min_y, min(ys)), max(max_y, max(ys))

    # Columns 20..360 and rows 20..340 of a 512-pixel chip at 10 m.
    h.close(min_x, 600000 + 20 * 10, "the leftmost roof edge is 200 m into the chip")
    h.close(max_x, 600000 + 360 * 10, "the rightmost roof edge is 3 600 m into the chip")
    h.close(max_y, 4200000 - 20 * 10, "the northern roof edge is 200 m down from the origin")
    h.close(min_y, 4200000 - 340 * 10, "the southern roof edge is 3 400 m down")

    h.check((module.OUTPUT_DIR / "detected_buildings.geojson").exists(),
            "the GeoJSON stays in output/ for inspection")

    h.write_json("raster_to_vector.json", {
        "tile": {"shape": list(result["image_shape"]), "crs": result["crs"],
                 "pixel_size_m": 10.0, "origin": [600000.0, 4200000.0]},
        "logits": {"min": round(result["logit_min"], 2),
                   "max": round(result["logit_max"], 2)},
        "mask_pixels": result["mask_pixels"],
        "features": result["feature_count"],
        "areas_m2": [round(value, 1) for value in areas],
        "total_area_m2": round(result["total_area_m2"], 1),
        "bounds": [min_x, min_y, max_x, max_y],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (raster to vector)", FILES).crash())
