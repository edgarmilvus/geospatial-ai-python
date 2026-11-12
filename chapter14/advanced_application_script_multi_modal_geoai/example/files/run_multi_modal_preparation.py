"""Harness for the advanced example — both clips, measured against the ROI.

The listing prints two paragraphs; the numbers that matter are on disk. The
clipped GeoTIFF must be the 400 x 400 pixel window the 4-degree ROI covers at
0.01 degrees per pixel, and the clipped GeoJSON must hold the two infrastructure
features that touch the ROI — the third is outside and has to disappear — with
the crossing one truncated at the boundary.
"""
import contextlib
import hashlib
import io
import pathlib
import subprocess
import sys

import geopandas as gpd
import rasterio

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "advanced example (multi-modal data preparation)"
OUTPUT = FILES.parent / "output"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_multi_modal_data_preparation.py", "multi_modal")
    printed = log.getvalue()

    # -- the scene and the boundary -------------------------------------
    source = OUTPUT / "large_satellite_image.tif"
    h.check(source.is_file(), "the listing wrote the simulated scene")
    with rasterio.open(source) as src:
        h.equal(src.width, 1000, "the scene is 1000 pixels wide")
        h.equal(src.height, 1000, "the scene is 1000 pixels tall")
        h.equal(src.count, 3, "the scene carries three bands")
        h.equal(src.crs.to_string(), "EPSG:4326", "the scene is in WGS 84")
        h.close(src.transform.a, 0.01, "one pixel spans 0.01 degrees")
        h.equal(tuple(round(value, 1) for value in src.bounds), (0.0, 0.0, 10.0, 10.0),
                "the scene covers 0..10 degrees in both axes")

    roi = module.roi_boundary_gdf
    h.equal(len(roi), 1, "the ROI is one polygon")
    h.equal(roi.geometry.iloc[0].bounds, (3.0, 3.0, 7.0, 7.0),
            "the protected zone runs 3..7 in both axes")

    # -- A. the raster clip ---------------------------------------------
    clipped_raster = OUTPUT / "roi_raster_clip.tif"
    h.check(clipped_raster.is_file(), "the raster clip was written")
    with rasterio.open(clipped_raster) as clipped:
        h.equal(clipped.count, 3, "the clip keeps all three bands")
        h.equal(clipped.width, 400, "four degrees at 0.01 degrees/px is 400 columns")
        h.equal(clipped.height, 400, "four degrees at 0.01 degrees/px is 400 rows")
        h.equal(clipped.crs, module.roi_boundary_gdf.crs,
                "the clip keeps the source CRS")
        h.equal(clipped.nodata, 0, "the profile carries the explicit NoData of 0")
        h.equal(tuple(round(value, 6) for value in clipped.bounds), (3.0, 3.0, 7.0, 7.0),
                "the clipped raster sits exactly on the ROI")
        band = clipped.read(1)
        h.equal(int(band.shape[0] * band.shape[1]), 160000,
                "160 000 pixels survive the cut")

    # -- B. the vector clip ---------------------------------------------
    clipped_vector = OUTPUT / "roi_vector_clip.geojson"
    h.check(clipped_vector.is_file(), "the vector clip was written")
    infra = gpd.read_file(clipped_vector)
    h.equal(len(infra), 2, "two of the three features touch the ROI")
    h.equal(sorted(infra["id"].tolist()), [2, 3], "features 2 and 3 are the ones kept")
    h.equal(sorted(infra["type"].tolist()), ["building", "pipeline"],
            "the attributes travel with the clipped geometries")
    h.equal(infra.crs.to_string(), "EPSG:4326", "the GeoJSON keeps WGS 84")
    h.check(1 not in infra["id"].tolist(), "the feature outside the ROI is gone")

    # Feature 2 is wholly inside; feature 3 crossed the boundary and was cut.
    inside = infra[infra["id"] == 2].geometry.iloc[0]
    crossing = infra[infra["id"] == 3].geometry.iloc[0]
    h.close(inside.area, 0.25, "the wholly-inside square keeps its 0.25 square degrees")
    h.close(crossing.area, 0.25, "the crossing square is cut to 0.25 square degrees")
    h.close(crossing.bounds[2], 7.0, "its east edge was moved onto the ROI boundary")
    h.check(crossing.bounds[2] <= 7.0, "no part of it survives east of the ROI")

    # -- deterministic simulation ---------------------------------------
    def scene_checksum():
        with rasterio.open(source) as src:
            return hashlib.sha256(src.read().tobytes()).hexdigest()

    first_run = scene_checksum()
    subprocess.run([sys.executable, str(FILES / "01_multi_modal_data_preparation.py")],
                   cwd=str(FILES), check=True, capture_output=True)
    h.equal(scene_checksum(), first_run,
            "a second run writes the same scene byte for byte")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "400 x 400 px", "the listing reports the clipped window")
    h.contains(printed, "2 of 3 features kept", "the listing reports how many features survived")
    h.contains(printed, "bounds (3.0, 3.0, 7.0, 7.0)",
               "the listing prints the bounds the assertion above checks")

    h.write_json("multi_modal_clip.json", {
        "scene": {"width": 1000, "height": 1000, "bands": 3, "pixel_degrees": 0.01},
        "roi_bounds": [3.0, 3.0, 7.0, 7.0],
        "raster_clip": {"width": 400, "height": 400, "pixels": 160000, "nodata": 0},
        "vector_clip": {
            "features_in": 3,
            "features_out": int(len(infra)),
            "ids": sorted(int(value) for value in infra["id"]),
            "types": sorted(infra["type"].tolist()),
            "inside_area_deg2": round(float(inside.area), 6),
            "crossing_area_deg2": round(float(crossing.area), 6),
        },
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
