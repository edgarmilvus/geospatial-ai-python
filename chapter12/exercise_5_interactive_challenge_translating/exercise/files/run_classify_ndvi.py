"""Harness for exercise 5 — turning the index into four classes.

The exercise is a threshold table, so the checks are the table itself: seven index
values placed on the boundaries and the class each one must get, the two forced
blocks, and the distribution the uniform draw implies — about 20% of the scene
below zero and about 30% above 0.5.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 5 (NDVI classification)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "classify_ndvi.py", "classify_ndvi")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    classes = module.vegetation_class_map
    h.equal(classes.shape, (100, 100), "the class map covers the 100x100 scene")
    h.equal(str(classes.dtype), "int8", "the class map stores small integers")

    # The class codes are the exercise's table, and nothing else.
    present = sorted(int(v) for v in np.unique(classes))
    h.equal(present, [0, 1, 2, 3], "all four classes appear, and no fifth code does")

    # Every boundary, placed by hand.
    probe = np.array([[-0.01, 0.0, 0.199, 0.2, 0.499, 0.5, 1.0]], dtype=np.float32)
    got = [int(v) for v in module.classify_ndvi(probe)[0]]
    h.equal(got, [0, 1, 1, 2, 2, 3, 3],
            "the boundaries fall where the table says: <0, 0-0.2, 0.2-0.5, >=0.5")
    h.equal(int(module.classify_ndvi(np.array([[-0.5]]) )[0, 0]), 0,
            "a negative index is class 0, water or cloud")
    h.equal(int(module.classify_ndvi(np.array([[0.7]]) )[0, 0]), 3,
            "0.7 is dense vegetation")
    # The function must classify the array it is handed, not the module's own map.
    other = np.full((2, 2), 0.6, dtype=np.float32)
    h.check(bool(np.all(module.classify_ndvi(other) == 3)),
            "classify_ndvi works on any map, not only on the module's own")

    # The two forced blocks.
    h.check(bool(np.all(classes[0:10, 0:10] == 0)),
            "the forced -0.5 block lands in class 0")
    h.check(bool(np.all(classes[90:100, 90:100] == 3)),
            "the forced 0.7 block lands in class 3")

    # The draw was uniform on [-0.2, 0.8): 20% of it is below zero, 30% is above 0.5.
    counts = np.bincount(classes.ravel(), minlength=4)
    h.equal(int(counts.sum()), 10000, "every pixel is classified")
    h.check(1900 <= int(counts[0]) <= 2100,
            "about a fifth of the scene is class 0 (got %d)" % counts[0])
    h.check(2880 <= int(counts[3]) <= 3120,
            "about three tenths of the scene is class 3 (got %d)" % counts[3])
    h.check(int(counts[1]) + int(counts[2]) > 0, "the middle classes are populated too")

    path = module.OUTPUT_FILE
    h.check(path.exists(), "the class map is written to output/vegetation_classes.tif")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 1, "the class map is one band")
            h.equal(src.dtypes[0], "uint8", "the class map is written as bytes")
            h.equal(src.nodata, 255, "255 is reserved for 'not classified'")
            band = src.read(1)
        h.check(bool(np.array_equal(band, classes.astype('uint8'))),
                "the bytes on disk are the class codes that were computed")
        h.check(255 not in np.unique(band), "no pixel falls through to the nodata code")

    h.contains(printed, "Class map data type: int8", "the dtype is reported")
    h.contains(printed, "Class 0 (Water/Cloud/No Data: Count: 2,100",
               "the class table is printed with counts")
    h.contains(printed, "Wrote class map to: output/vegetation_classes.tif",
               "the listing names the file it wrote")
    h.contains(printed, "Interpretation: Class", "the interpretation is printed")

    h.write_json("ndvi_classes.json", {
        "shape": list(classes.shape),
        "dtype": str(classes.dtype),
        "thresholds": {"0": "ndvi < 0.0", "1": "0.0 <= ndvi < 0.2",
                       "2": "0.2 <= ndvi < 0.5", "3": "ndvi >= 0.5"},
        "counts": {str(i): int(c) for i, c in enumerate(counts)},
        "percent": {str(i): float(c) / 10000 * 100 for i, c in enumerate(counts)},
        "boundary_classes": got,
        "class_raster": {"count": 1, "dtype": "uint8", "nodata": 255},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (NDVI classification)", FILES).crash())
