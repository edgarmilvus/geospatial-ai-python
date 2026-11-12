"""Harness for exercise 5 — the profile inherits the grid and changes the payload.

The four changed keys are checked against the four inherited ones: count, dtype,
nodata and interleave change; width, height, CRS and transform do not. The written
GeoTIFF is re-opened, so the template is proved by a real file rather than by the
dictionary alone.
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


def main():
    h = Harness("exercise 5 (classification template)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "classification_template.py", "classification_template")
        result = module.main()
    printed = log.getvalue()

    source = result["input_profile"]
    target = result["output_profile"]
    classes = result["classes"]

    # Inherited: the grid is the input's grid.
    h.equal(source["count"], 4, "the input carries four bands")
    h.equal(source["dtype"], "uint16", "the input is uint16")
    h.equal(source.get("nodata"), 0, "the input declares nodata 0")
    h.equal(target["width"], source["width"], "the output keeps the width")
    h.equal(target["height"], source["height"], "the output keeps the height")
    h.equal(target["width"], 240, "the map is 240 columns wide")
    h.equal(target["height"], 180, "the map is 180 rows high")
    h.equal(str(target["crs"]), str(source["crs"]), "the output keeps the CRS")
    h.equal(target["transform"], source["transform"], "the output keeps the transform")
    h.equal(target["crs"].to_string(), "EPSG:32612", "the grid is UTM zone 12N")

    # Changed: the payload is a single uint8 class band.
    h.equal(target["count"], 1, "the output has one band")
    h.equal(str(target["dtype"]), "uint8", "the output is uint8")
    h.equal(target.get("nodata"), 255, "the output declares 255 as nodata")
    h.equal(target["interleave"], "band", "the output interleaves by band")
    h.equal(target["compress"], "deflate", "the output is compressed")

    # The array itself: eight classes, 255 on the top rows.
    h.equal(classes.shape, (180, 240), "the class map is 180 x 240")
    h.equal(str(classes.dtype), "uint8", "the class map is uint8")
    h.equal(sorted(np.unique(classes).tolist()), [0, 1, 2, 3, 4, 5, 6, 7, 255],
            "the map holds classes 0-7 and the 255 sentinel")
    h.equal(int((classes == 255).sum()), 20 * 240,
            "20 unclassified rows is 4 800 pixels")
    h.equal(int(classes[0, 0]), 255, "the top-left pixel is unclassified")
    h.equal(int(classes[20, 0]), 4, "the first classified row continues the pattern")

    # The written file agrees with the dictionary.
    with rasterio.open(module.OUTPUT_PATH) as written:
        h.equal(written.count, 1, "the file on disk has one band")
        h.equal(written.dtypes[0], "uint8", "the file on disk is uint8")
        h.equal(written.nodata, 255, "the file on disk declares 255")
        h.equal((written.width, written.height), (240, 180), "the file on disk keeps the grid")
        h.equal(written.crs.to_string(), "EPSG:32612", "the file on disk keeps the CRS")
        h.check(np.array_equal(written.read(1), classes),
                "the pixels read back exactly as written")

    # What the reader sees.
    h.contains(printed, "Count: 4, Dtype: uint16, Nodata: 0",
               "the listing prints the input profile")
    h.contains(printed, "Count: 1", "the listing prints the modified count")
    h.contains(printed, "Nodata: 255", "the listing prints the modified nodata")
    h.contains(printed, "Read back: count=1, dtype=uint8, nodata=255.0",
               "the listing reads its own output back")

    h.write_json("classification_template.json", {
        "input": {"count": source["count"], "dtype": source["dtype"],
                  "nodata": source.get("nodata"), "width": source["width"],
                  "height": source["height"]},
        "output": {"count": target["count"], "dtype": str(target["dtype"]),
                   "nodata": target.get("nodata"), "interleave": target["interleave"],
                   "compress": target["compress"], "width": target["width"],
                   "height": target["height"], "crs": target["crs"].to_string()},
        "classes": sorted(int(value) for value in np.unique(classes)),
        "unclassified_pixels": int((classes == 255).sum()),
        "class_0_pixels": int((classes == 0).sum()),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (classification template)", FILES).crash())
