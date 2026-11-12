"""Harness for exercise 1 — the five properties and the POLA warning.

Two scenes are read: a three-band one that passes the check and a single-band one
that must print the warning with its own band count. A third call points at a path
that does not exist, which must come back as `None` after a readable message
rather than a traceback.
"""
import contextlib
import io
import pathlib
import sys

import rasterio

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 1 (metadata deep dive)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "metadata_deep_dive.py", "metadata_deep_dive")
        full, thin, missing = module.main()
    printed = log.getvalue()

    # The three-band scene: every property the exercise names.
    h.equal(full["crs"], "EPSG:32633", "the CRS resolves to EPSG:32633")
    h.equal(full["count"], 3, "the scene reports three bands")
    h.equal(full["width"], 120, "the scene is 120 columns wide")
    h.equal(full["height"], 90, "the scene is 90 rows high")
    h.equal(full["dtype"], "uint16", "the pixels are uint16")
    h.close(full["transform"][0], 30.0, "a pixel is 30 m across")
    h.close(full["transform"][4], -30.0, "a pixel is 30 m down")
    h.close(full["transform"][2], 300000.0, "the west edge is easting 300 000")
    h.close(full["transform"][5], 5000000.0, "the north edge is northing 5 000 000")
    h.equal(full["warned"], False, "three bands pass the POLA check")

    # The thin scene: same geometry, one band, warning.
    h.equal(thin["count"], 1, "the second scene reports one band")
    h.equal(thin["warned"], True, "one band trips the POLA check")
    h.contains(printed, "WARNING: Band count (1) is insufficient",
               "the warning states the actual band count")
    h.contains(printed, "Verification successful: Raster has 3 or more bands.",
               "the healthy scene is reported as successful")

    # The missing file: a message, not a traceback.
    h.equal(missing, None, "a missing path returns None")
    h.contains(printed, "Error opening raster file at",
               "a missing path prints a readable error")

    # The pixel values are inside the band the generator promised.
    with rasterio.open(module.MULTI_BAND_PATH) as src:
        band = src.read(1)
        h.equal(band.shape, (90, 120), "the band reads back as 90 x 120")
        h.check(int(band.min()) >= 100 and int(band.max()) < 900,
                "the generated values stay inside 100-899")
        h.equal(src.crs.to_string(), "EPSG:32633", "the written file carries the CRS")
        h.equal(src.count, 3, "the written file carries three bands")

    h.check(module.MULTI_BAND_PATH.exists() and module.SINGLE_BAND_PATH.exists(),
            "both scenes stay in output/ for inspection")

    h.write_json("metadata_deep_dive.json", {
        "scene": {"crs": full["crs"], "bands": full["count"],
                  "width": full["width"], "height": full["height"],
                  "dtype": full["dtype"]},
        "transform": [round(value, 3) for value in full["transform"]],
        "warning_scene_bands": thin["count"],
        "warning_raised": thin["warned"],
        "missing_file_returns": missing,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (metadata deep dive)", FILES).crash())
