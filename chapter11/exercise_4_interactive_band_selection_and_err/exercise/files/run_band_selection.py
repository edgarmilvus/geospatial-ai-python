"""Harness for exercise 4 — one good band, two bad answers, one default.

The band values are built so a mix-up is visible: band 2 lives between 200 and 599.
The harness reads band 2 and compares against the source, then feeds the two error
branches and the no-terminal branch.
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
    h = Harness("exercise 4 (band selection)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "band_selection_reader.py", "band_selection")
        valid, text, outside, default = module.main()
    printed = log.getvalue()

    with rasterio.open(module.SCENE_PATH) as src:
        band2 = src.read(2)
        band1 = src.read(1)
        h.equal(src.count, 4, "the scene carries four bands")
        h.equal(src.width, 200, "the scene is 200 columns wide")
        h.equal(src.height, 150, "the scene is 150 rows high")
        h.equal(src.crs.to_string(), "EPSG:32611", "the scene is in UTM zone 11N")

    # The good answer.
    h.equal(valid["band"], 2, "band 2 is the band that was read")
    h.equal(valid["shape"], (150, 200), "one band arrives as 150 x 200, no band axis")
    h.equal(valid["min"], int(band2.min()), "the minimum is band 2's minimum")
    h.equal(valid["max"], int(band2.max()), "the maximum is band 2's maximum")
    h.check(valid["min"] >= 200, "band 2 starts at 200, not at band 1's 100")
    h.equal(valid["error"], None, "a valid band reports no error")

    # Text instead of a number.
    h.equal(text["band"], None, "text reads no band")
    h.contains(text["error"], "Invalid input format",
               "text is refused as a format error")
    h.contains(text["error"], "whole number", "the message says what to type")

    # A number outside 1..4.
    h.equal(outside["band"], None, "an out-of-range band reads nothing")
    h.contains(outside["error"], "Band number 9 is out of range",
               "the message repeats the offending number")
    h.contains(outside["error"], "between 1 and 4",
               "the message states the valid range")

    # The no-terminal default: band 1, and the reader says so.
    h.equal(default["band"], 1, "without a terminal the reader falls back to band 1")
    h.equal(default["min"], int(band1.min()), "the default band is band 1's data")
    h.contains(printed, "No terminal attached: reading band 1.",
               "the fallback is announced, not silent")

    # The parser on its own, both edges.
    h.equal(module.parse_band_choice(0, 4), (None, module.parse_band_choice(0, 4)[1]),
            "zero is rejected")
    h.contains(module.parse_band_choice(0, 4)[1], "out of range", "zero is out of range")
    h.equal(module.parse_band_choice(4, 4), (4, None), "the last band is accepted")
    h.equal(module.parse_band_choice("five", 4), (None, module.parse_band_choice("five", 4)[1]),
            "a word is rejected")

    h.write_json("band_selection.json", {
        "scene": {"width": 200, "height": 150, "bands": 4, "crs": "EPSG:32611"},
        "valid": valid,
        "text_error": text["error"],
        "range_error": outside["error"],
        "default_band": default["band"],
        "band2_range": [int(band2.min()), int(band2.max())],
        "band1_range": [int(band1.min()), int(band1.max())],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (band selection)", FILES).crash())
