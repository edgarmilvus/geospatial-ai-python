"""Harness for example 1 — a GeoTIFF written, read and described by its three pillars.

The numbers are the scene's geometry, not the run's: a one-degree box cut into 100
columns is 0.01 degrees per pixel, the north edge is 0.8, and the pixel the chapter
calls (row 0, column 0) maps to that corner.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 1 (GeoTIFF metadata)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "read_scene_metadata.py", "read_scene")
        metadata, band = module.main()
    printed = log.getvalue()

    # Shape and dtype: 100 columns, 80 rows, one unsigned 16-bit band.
    h.equal(band.shape, (80, 100), "the band arrives as 80 rows by 100 columns")
    h.equal(str(band.dtype), "uint16", "the band is unsigned 16-bit")
    h.equal(metadata["width"], 100, "the dataset reports 100 columns")
    h.equal(metadata["height"], 80, "the dataset reports 80 rows")
    h.equal(metadata["count"], 1, "the dataset holds one band")
    h.equal(metadata["dtype"], "uint16", "the dataset reports a uint16 pixel type")

    # The CRS and the transform: the three pillars the chapter names.
    h.equal(metadata["crs"], "EPSG:4326", "the CRS resolves to EPSG:4326")
    transform = metadata["transform"]
    h.close(transform[0], 0.01, "one column spans 0.01 degrees of longitude")
    h.close(transform[1], 0.0, "the grid is not rotated east-west")
    h.close(transform[2], 0.0, "the west edge sits at longitude 0")
    h.close(transform[3], 0.0, "the grid is not sheared north-south")
    h.close(transform[4], -0.01, "one row spans 0.01 degrees of latitude, north up")
    h.close(transform[5], 0.8, "the north edge sits at latitude 0.8")

    # Bounds follow from the transform: the whole one-degree box.
    west, south, east, north = metadata["bounds"]
    h.close(west, 0.0, "the west bound is 0")
    h.close(south, 0.0, "the south bound is 0")
    h.close(east, 1.0, "the east bound is 1 degree")
    h.close(north, 0.8, "the north bound is 0.8 degrees")
    h.equal(metadata["nodata"], 0, "nodata is declared as 0")

    # The pixel data itself: constant 500 across the whole band.
    h.equal(int(band.min()), 500, "the smallest pixel is 500")
    h.equal(int(band.max()), 500, "the largest pixel is 500")
    h.equal(int(band.sum()), 500 * 80 * 100, "all 8 000 pixels carry 500")

    # Georeferencing in both directions, the operation the chapter builds toward.
    x, y = module.AFFINE_TRANSFORM * (0.5, 0.5)
    h.close(x, 0.005, "the centre of the first pixel is half a pixel east of the corner")
    h.close(y, 0.795, "the centre of the first pixel is half a pixel south of the north edge")
    column, row = ~module.AFFINE_TRANSFORM * (0.005, 0.795)
    h.close(column, 0.5, "inverse georeferencing returns the column")
    h.close(row, 0.5, "inverse georeferencing returns the row")

    # The reader sees the properties in the terminal.
    h.contains(printed, "1. Coordinate System (CRS):\nEPSG:4326",
               "the listing prints the CRS string")
    h.contains(printed, "   Width (Columns): 100", "the listing prints the width")
    h.contains(printed, "   Data shape read (H, W): (80, 100)",
               "the listing prints the array shape")
    h.contains(printed, "--- 3. Cleanup: Removed basic_rasterio_scene.tif ---",
               "the listing removes the file it wrote")

    # The listing cleaned up after itself, so output/ holds no GeoTIFF.
    h.check(not (module.OUTPUT_DIR / module.OUTPUT_FILENAME).exists(),
            "the generated GeoTIFF does not survive the run")

    h.write_json("scene_metadata.json", {
        "shape": list(band.shape),
        "dtype": metadata["dtype"],
        "count": metadata["count"],
        "crs": metadata["crs"],
        "transform": [round(value, 6) for value in metadata["transform"]],
        "bounds": [round(value, 6) for value in metadata["bounds"]],
        "nodata": metadata["nodata"],
        "pixel_min": int(band.min()),
        "pixel_max": int(band.max()),
        "pixel_centre": [0.005, 0.795],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (GeoTIFF metadata)", FILES).crash())
