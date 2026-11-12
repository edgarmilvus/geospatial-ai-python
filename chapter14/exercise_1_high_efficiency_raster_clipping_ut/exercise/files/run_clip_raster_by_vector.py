"""Harness for exercise 1 — the clip that reprojects its own mask.

The exercise's contract has four parts: reproject the mask when its CRS differs,
keep the raster's metadata, set NoData explicitly, and cut the window the ROI
covers. The harness runs the listing's demo and checks each part against the
2 km ROI: a 200 x 200 pixel core, a one pixel NoData collar, and the source's own
values inside.
"""
import contextlib
import io
import pathlib
import sys

import geopandas as gpd
import numpy as np
import rasterio

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 1 (CRS-aware raster clipping)"
OUTPUT = FILES.parent / "output"
ROI = (500500.0, 4200500.0, 502500.0, 4202500.0)   # 2 km x 2 km, EPSG:32610


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    module = load_listing(FILES / "01_clip_raster_by_vector.py", "clip_by_vector")

    # The listing guards its demo behind __main__, so drive it the way a reader does.
    with contextlib.redirect_stdout(log):
        raster_path, mask_path = module.build_demo_inputs(OUTPUT)
        module.clip_raster_by_vector(
            raster_path, mask_path, OUTPUT / "utm_tile_clipped.tif")
    printed = log.getvalue()

    # -- the inputs are what the demo claims -----------------------------
    with rasterio.open(raster_path) as src:
        h.equal(src.crs.to_string(), "EPSG:32610", "the source raster is UTM zone 10N")
        h.equal((src.width, src.height), (600, 600), "the source is 600 x 600 pixels")
        h.close(src.transform.a, 10.0, "one source pixel is 10 metres")
        source_data = src.read(1)

    mask = gpd.read_file(mask_path)
    h.equal(mask.crs.to_string(), "EPSG:4326",
            "the mask is handed over in WGS 84, not in the raster's CRS")
    lon_span = mask.total_bounds[2] - mask.total_bounds[0]
    h.check(0.015 < lon_span < 0.030,
            "a 2 km ROI is about 0.023 degrees of longitude at this latitude "
            "(got %.4f)" % lon_span)

    # -- the branch the exercise is about --------------------------------
    h.contains(printed, "Reprojecting vector from EPSG:4326 to raster CRS EPSG:32610",
               "the function detected the mismatch and reprojected the mask")

    # -- the output raster ----------------------------------------------
    clipped_path = OUTPUT / "utm_tile_clipped.tif"
    h.check(clipped_path.is_file(), "the clip was written to the project's output/")
    with rasterio.open(clipped_path) as clipped:
        h.equal(clipped.crs.to_string(), "EPSG:32610", "the output keeps the raster's CRS")
        h.equal(clipped.count, 1, "the output keeps the band count")
        h.equal(clipped.nodata, -9999, "the output carries the source's NoData")
        h.equal(clipped.dtypes[0], "int32", "the output keeps the data type")
        h.close(clipped.transform.a, 10.0, "the output keeps the 10 m pixel")
        data = clipped.read(1)
        bounds = clipped.bounds

    # The ROI is 2 km square at 10 m: 200 x 200 pixels. The window is allowed to
    # grow by one pixel on a side, because the boundary lands on a pixel edge.
    h.check(200 <= data.shape[0] <= 202, "the window holds the ROI's 200 rows")
    h.check(200 <= data.shape[1] <= 202, "the window holds the ROI's 200 columns")
    inside = int((data != -9999).sum())
    h.equal(inside, 40000, "40 000 pixels of the 2 km ROI carry data")
    h.equal(int((data == -9999).sum()), data.size - 40000,
            "every other pixel of the window is NoData")

    for name, actual, expected in (("west", bounds.left, ROI[0]),
                                   ("south", bounds.bottom, ROI[1]),
                                   ("east", bounds.right, ROI[2]),
                                   ("north", bounds.top, ROI[3])):
        h.check(abs(actual - expected) <= 10.0,
                "the %s edge is within one pixel of the ROI (got %.1f)" % (name, actual))

    # The clip copies values, it does not resample: the data block is the source.
    row0 = int(round((4206000 - ROI[3]) / 10))
    col0 = int(round((ROI[0] - 500000) / 10))
    expected_block = source_data[row0:row0 + 200, col0:col0 + 200]
    h.check(np.array_equal(data[1:201, 1:201], expected_block),
            "the 200 x 200 core is the source array's own values, not a resampling")
    h.equal(int(data[1, 1]), int(source_data[row0, col0]),
            "the first pixel inside the ROI is the source pixel at that corner")

    h.write_json("clip_by_vector.json", {
        "source": {"crs": "EPSG:32610", "width": 600, "height": 600, "pixel_m": 10.0},
        "mask_crs": "EPSG:4326",
        "roi_bounds_utm": list(ROI),
        "output": {
            "crs": "EPSG:32610",
            "width": int(data.shape[1]),
            "height": int(data.shape[0]),
            "nodata": -9999,
            "pixels_with_data": inside,
            "pixels_nodata": int((data == -9999).sum()),
            "bounds": [round(value, 1) for value in
                       (bounds.left, bounds.bottom, bounds.right, bounds.top)],
        },
        "reprojected": "Reprojecting vector from EPSG:4326 to raster CRS EPSG:32610"
                       in printed,
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
