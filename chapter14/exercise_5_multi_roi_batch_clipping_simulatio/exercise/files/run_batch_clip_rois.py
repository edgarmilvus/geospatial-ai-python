"""Harness for exercise 5 — one raster, three ROIs, three named tiles.

The batch workflow has three promises: every ROI produces its own file named
after its id, each tile is the window that ROI covers (not the whole scene), and
the source is read once and reused. The harness checks the first two on disk and
the third by the pixel values: each tile holds the source's own window for that
ROI, so nothing was re-read and nothing was resampled.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np
import rasterio

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 5 (multi-ROI batch clip)"
OUTPUT = FILES.parent / "output"
TILES = OUTPUT / "clipped_tiles"
EXPECTED = {
    "A001": {"bounds": (1.0, 1.0, 5.0, 5.0), "pixels": 1600, "shape": (40, 40)},
    "B002": {"bounds": (10.0, 10.0, 15.0, 15.0), "pixels": 2500, "shape": (50, 50)},
    "C003": {"bounds": (20.0, 20.0, 25.0, 25.0), "pixels": 2500, "shape": (50, 50)},
}


def main():
    h = Harness(NAME, FILES)
    module = load_listing(FILES / "01_batch_clip_rois.py", "batch_clip")

    with contextlib.redirect_stdout(io.StringIO()):
        module.build_demo_raster(module.INPUT_RASTER_PATH)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        written = module.batch_clip_rois(module.INPUT_RASTER_PATH, module.rois_gdf, TILES)
    printed = log.getvalue()

    # -- the batch itself ------------------------------------------------
    h.equal(len(module.rois_gdf), 3, "the vector file describes three ROIs")
    h.equal([row["id"] for _i, row in module.rois_gdf.iterrows()],
            ["A001", "B002", "C003"], "the ids are the ones the filenames must carry")
    h.equal(len(written), 3, "all three ROIs were clipped")
    h.equal(sum(height * width for _id, height, width in written), 6600,
            "the three tiles hold 6 600 pixels between them")

    # -- the files -------------------------------------------------------
    for roi_id, expected in EXPECTED.items():
        path = TILES / ("clipped_tile_%s.tif" % roi_id)
        h.check(path.is_file(), "%s was written with its id in the name" % path.name)
        if not path.is_file():
            continue
        with rasterio.open(path) as tile:
            h.equal((tile.width, tile.height), expected["shape"],
                    "%s is %d x %d pixels" % ((roi_id,) + expected["shape"]))
            h.equal(tile.width * tile.height, expected["pixels"],
                    "%s holds %d pixels" % (roi_id, expected["pixels"]))
            h.equal(tuple(round(value, 6) for value in tile.bounds), expected["bounds"],
                    "%s sits on its ROI" % roi_id)
            h.equal(tile.crs.to_string(), "EPSG:4326", "%s keeps WGS 84" % roi_id)
            h.equal(tile.nodata, -1, "%s inherits the scene's NoData" % roi_id)

    # 6 600 pixels across three tiles is fewer than the 62 500 pixel scene.
    with rasterio.open(module.INPUT_RASTER_PATH) as scene:
        h.equal(scene.width * scene.height, 62500, "the input scene is 250 x 250 pixels")
        source = scene.read(1)

    # -- the values are the source's, not a copy of the scene ------------
    with rasterio.open(TILES / "clipped_tile_A001.tif") as tile:
        a001 = tile.read(1)
    # The scene's origin is (0, 25) with 0.1 degrees per pixel; A001 starts at
    # northing 5 (row 200) and easting 1 (column 10).
    h.equal(int(a001[0, 0]), int(source[200, 10]),
            "A001's first pixel is the scene's pixel at that corner")
    h.check(np.array_equal(a001, source[200:240, 10:50]),
            "A001 is the scene's own 40 x 40 window")

    with rasterio.open(TILES / "clipped_tile_C003.tif") as tile:
        c003 = tile.read(1)
    h.check(np.array_equal(c003, source[0:50, 200:250]),
            "C003 is the scene's north-east 50 x 50 window")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Processing ROI ID: A001", "each ROI is announced before it is cut")
    h.contains(printed, "SUCCESS: Tile saved as", "each success is logged")
    h.contains(printed, "clipped_tile_B002.tif", "the log names the file it wrote")
    h.contains(log.getvalue(), "  -> SUCCESS", "the log is indented under the ROI")

    h.write_json("batch_clip_rois.json", {
        "scene": {"width": 250, "height": 250, "pixels": 62500, "degrees_per_pixel": 0.1},
        "rois": len(module.rois_gdf),
        "tiles": {
            roi_id: {
                "file": "clipped_tile_%s.tif" % roi_id,
                "width": expected["shape"][1],
                "height": expected["shape"][0],
                "pixels": expected["pixels"],
                "bounds": list(expected["bounds"]),
            }
            for roi_id, expected in EXPECTED.items()
        },
        "pixels_total": sum(height * width for _id, height, width in written),
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
