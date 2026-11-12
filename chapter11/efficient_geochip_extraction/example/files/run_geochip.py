"""Harness for example 2 — a 256-pixel chip read through a window.

The chip's numbers are checked against the source: the harness re-opens the scene
and reads the same window, so the assertion is that the listing's windowed read
returned exactly those pixels, in the order the band list asked for, with the
transform shifted by the window's offset.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np
import rasterio
from rasterio.windows import Window

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 2 (windowed GeoChip)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "geochip_extraction.py", "geochip")
        if module.DUMMY_FILENAME.exists():
            module.DUMMY_FILENAME.unlink()
        module.create_dummy_geotiff(module.DUMMY_FILENAME)
        result = module.extract_geo_chip(
            module.DUMMY_FILENAME, module.CHIP_SIZE, module.TARGET_BANDS)
        module.create_dummy_geotiff(module.DUMMY_FILENAME)  # second call must skip
    printed = log.getvalue()

    with rasterio.open(module.DUMMY_FILENAME) as src:
        h.equal(src.width, 1024, "the scene is 1024 columns wide")
        h.equal(src.height, 1024, "the scene is 1024 rows high")
        h.equal(src.count, 4, "the scene carries four bands")
        h.equal(src.dtypes[0], "uint16", "the scene is uint16")
        h.equal(src.crs.to_string(), "EPSG:32617", "the scene is in UTM zone 17N")
        h.close(src.transform.a, 10.0, "a pixel is 10 m across")
        h.close(src.transform.e, -10.0, "a pixel is 10 m down, north up")
        h.close(src.transform.c, 500000.0, "the west edge is easting 500 000")
        h.close(src.transform.f, 4500000.0, "the north edge is northing 4 500 000")

        window = Window(col_off=384, row_off=384, width=256, height=256)
        expected = src.read(indexes=[3, 2, 1], window=window)

    chip = result["data"]
    h.equal(chip.shape, (3, 256, 256), "the chip arrives as three 256x256 planes")
    h.equal(str(chip.dtype), "uint16", "the chip keeps the source dtype")
    h.check(np.array_equal(chip, expected),
            "the chip is exactly the source pixels under the centred window")
    h.equal(int(result["window"].col_off), 384, "the window starts 384 columns in")
    h.equal(int(result["window"].row_off), 384, "the window starts 384 rows down")
    h.equal(int(result["window"].width), 256, "the window is 256 columns wide")
    h.equal(int(result["window"].height), 256, "the window is 256 rows high")

    # The chip's own transform: the source origin moved by the window offset.
    chip_transform = result["transform"]
    h.close(chip_transform.c, 503840.0, "the chip's west edge is 3 840 m east")
    h.close(chip_transform.f, 4496160.0, "the chip's north edge is 3 840 m down")
    h.close(chip_transform.a, 10.0, "the chip keeps the 10 m pixel size")
    h.equal(result["crs"].to_string(), "EPSG:32617", "the chip carries the source CRS")

    # Band order: red first, then green, then blue, each its own numbers.
    h.close(float(chip[0].mean()), float(expected[0].mean()),
            "the first plane holds band 3", tol=1e-9)
    h.check(float(chip[0].mean()) != float(chip[1].mean()),
            "the three planes are different bands, not one band three times")

    # What the run printed and left behind.
    h.contains(printed, "Chip Shape: (3, 256, 256)", "the listing prints the chip shape")
    h.contains(printed, "Defined Extraction Window:", "the listing prints the window")
    h.contains(printed, "Skipping creation: large_satellite_scene.tif already exists",
               "a second run reuses the scene instead of rewriting it")
    h.check(module.DUMMY_FILENAME.exists(), "the scene stays in output/ for the next stage")

    h.write_json("geochip.json", {
        "scene": {"width": 1024, "height": 1024, "bands": 4, "crs": "EPSG:32617",
                  "pixel_size": [10.0, -10.0], "origin": [500000.0, 4500000.0]},
        "window": {"col_off": 384, "row_off": 384, "width": 256, "height": 256},
        "chip": {"shape": list(chip.shape), "dtype": str(chip.dtype),
                 "mean": round(float(chip.mean()), 4),
                 "band_means": [round(float(band.mean()), 4) for band in chip]},
        "chip_transform": [round(float(value), 3) for value in chip_transform[:6]],
        "band_order": [3, 2, 1],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (windowed GeoChip)", FILES).crash())
