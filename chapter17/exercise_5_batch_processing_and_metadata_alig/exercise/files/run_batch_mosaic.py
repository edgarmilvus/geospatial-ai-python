"""Harness for exercise 5 — a batch that keeps each tile's own georeference.

The mosaic is the proof: three 100 x 100 masks written with the wrong transform would
still merge, and still look plausible, and still be wrong. Here the second tile's mask
must carry easting 300 100, the third northing 4 500 100, and the merged grid must be
200 x 200 covering 300 000-300 200 by 4 500 000-4 500 200.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import rasterio  # noqa: E402

from harness import Harness, load_listing  # noqa: E402

# The three tiles of the batch, in order, with the origin each mask must carry.
EXPECTED = [
    ("mask_tile_01.tif", 300000.0, 4500200.0),
    ("mask_tile_02.tif", 300100.0, 4500200.0),
    ("mask_tile_03.tif", 300000.0, 4500100.0),
]


def main():
    h = Harness("exercise 5 (batch mosaic)", FILES)
    module = load_listing(FILES / "batch_mosaic.py", "batch_mosaic")

    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        measured = module.main()
    printed = log.getvalue()

    # --- the batch ---
    h.equal(len(measured["processed"]), 3, "three tiles were processed")
    h.equal(measured["skipped"], ["tile_404.tif"], "the missing tile was skipped, not fatal")
    h.contains(printed, "FATAL ERROR: cannot read tile_404.tif",
               "the skip is announced with the file name")

    # --- each mask carries its own tile's transform ---
    for (name, easting, northing), path in zip(EXPECTED, module.MASK_DIR.glob("mask_*")):
        with rasterio.open(module.MASK_DIR / name) as src:
            h.equal((src.height, src.width), (100, 100), "%s is 100 x 100" % name)
            h.equal(str(src.dtypes[0]), "uint8", "%s is a uint8 mask" % name)
            h.equal(src.crs.to_string(), "EPSG:32618", "%s keeps the tile's CRS" % name)
            h.close(src.transform.c, easting, "%s has the tile's easting" % name, tol=1e-6)
            h.close(src.transform.f, northing, "%s has the tile's northing" % name,
                    tol=1e-6)
            h.close(src.transform.a, 1.0, "%s keeps the 1 m pixel" % name)

    # The mistake this exercise is about: reusing one transform for every mask. Tile 2
    # would then claim tile 1's origin, and the mosaic would silently double up.
    with rasterio.open(module.MASK_DIR / "mask_tile_02.tif") as second:
        h.check(abs(second.transform.c - 300000.0) > 50,
                "tile 2's mask is not written with tile 1's transform")

    # --- the masks themselves ---
    h.equal(sorted(measured["masks"].values()), [1200, 1200, 1200],
            "each 30 x 40 roof is 1 200 pixels")

    # --- the mosaic ---
    h.equal(measured["mosaic_shape"], (1, 200, 200),
            "three 100 x 100 tiles on a clean grid merge into 200 x 200")
    h.equal(measured["mosaic_pixels"], 3600, "the mosaic holds all 3 600 building pixels")
    h.close(measured["mosaic_origin"][0], 300000.0, "the mosaic starts at the west edge")
    h.close(measured["mosaic_origin"][1], 4500200.0, "and at the northern one")
    h.close(measured["mosaic_pixel_size"], 1.0, "the mosaic keeps the 1 m grid")

    with rasterio.open(module.MOSAIC_PATH) as mosaic:
        h.equal(mosaic.crs.to_string(), "EPSG:32618", "the mosaic file carries the CRS")
        h.equal((mosaic.height, mosaic.width), (200, 200), "and the merged dimensions")
        bounds = mosaic.bounds
        h.close(bounds.left, 300000.0, "west bound is easting 300 000")
        h.close(bounds.bottom, 4500000.0, "south bound is northing 4 500 000")
        h.close(bounds.right, 300200.0, "east bound is easting 300 200")
        h.close(bounds.top, 4500200.0, "north bound is northing 4 500 200")
        h.equal(int(mosaic.read(1).sum()), 3600, "the file on disk holds the 3 600 pixels")

    h.write_json("batch_mosaic.json", {
        "segmenter": measured["mode"],
        "tiles": {"processed": measured["processed"], "skipped": measured["skipped"],
                  "grid": {"tile_px": 100, "pixel_m": 1.0}},
        "masks": measured["masks"],
        "mosaic": {"shape": list(measured["mosaic_shape"]),
                   "pixels": measured["mosaic_pixels"],
                   "origin": list(measured["mosaic_origin"]),
                   "pixel_m": measured["mosaic_pixel_size"],
                   "bounds": [300000.0, 4500000.0, 300200.0, 4500200.0],
                   "crs": "EPSG:32618",
                   "file": measured["mosaic"]},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (batch mosaic)", FILES).crash())
