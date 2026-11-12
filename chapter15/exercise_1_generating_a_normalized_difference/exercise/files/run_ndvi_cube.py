"""Harness for exercise 1 — a 4D band cube reduced to a 3D NDVI cube.

The exercise's four requirements are shape, formula, division-by-zero handling
and the three global statistics. The harness checks the cube's axis order before
the formula, because a band axis read as a time axis still produces numbers — the
wrong ones — and only the shape and the selected band give it away.
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

NAME = "exercise 1 (NDVI cube)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_ndvi_cube.py", "ndvi_cube")
    printed = log.getvalue()

    raw = module.raw_data_stack
    ndvi = module.ndvi_time_series

    # -- the cube --------------------------------------------------------
    h.equal(tuple(raw.dims), ("time", "y", "x", "band"),
            "the bands-last cube is (time, y, x, band)")
    h.equal(raw.shape, (5, 100, 100, 2), "five dates, 100 x 100 pixels, two bands")
    h.equal(raw.sizes["band"], 2, "the band axis carries red and nir")
    h.equal(sorted(raw.band.values.tolist()), ["nir", "red"],
            "the two bands are labelled, not numbered")

    # -- the reduction ---------------------------------------------------
    h.equal(tuple(ndvi.dims), ("time", "y", "x"),
            "NDVI drops the band axis and keeps time, y, x")
    h.equal(ndvi.shape, (5, 100, 100), "one 100 x 100 map per date")
    h.check("band" not in ndvi.coords, "the band coordinate does not survive the reduction")
    h.equal(ndvi.name, "NDVI", "the result is named for the index it holds")

    # -- the formula, on one pixel ----------------------------------------
    pick = dict(time=raw.time.values[2], y=17, x=42)
    nir = float(raw.sel(band="nir", **pick))
    red = float(raw.sel(band="red", **pick))
    h.close(float(ndvi.sel(**pick)), (nir - red) / (nir + red),
            "pixel (17, 42) on the third date is (NIR - Red) / (NIR + Red)", tol=1e-9)
    h.check(float(ndvi.sel(**pick)) > 0.0,
            "a simulated vegetation pixel yields a positive index")

    # -- the statistics the exercise prints -------------------------------
    minimum = float(ndvi.min())
    maximum = float(ndvi.max())
    mean = float(ndvi.mean())
    h.check(-1.0 <= minimum <= 1.0, "the minimum is inside -1..1")
    h.check(-1.0 <= maximum <= 1.0, "the maximum is inside -1..1")
    h.check(0.05 <= minimum <= 0.15, "the minimum is near 0.11 (%.4f)" % minimum)
    h.check(0.75 <= maximum <= 0.80, "the maximum is near 0.80 (%.4f)" % maximum)
    h.check(0.45 <= mean <= 0.50, "the mean is near 0.48 (%.4f)" % mean)
    h.equal(int(np.isnan(ndvi.values).sum()), 0,
            "no pixel divided by zero, because both bands are always positive")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Minimum NDVI:", "the listing prints the minimum")
    h.contains(printed, "Maximum NDVI:", "the listing prints the maximum")
    h.contains(printed, "Mean NDVI:", "the listing prints the mean")
    h.contains(printed, "Final NDVI Stack Dimensions: ('time', 'y', 'x')",
               "the listing prints the dimensions the assertions check")

    h.write_json("ndvi_cube.json", {
        "cube_shape": list(raw.shape),
        "cube_dims": list(raw.dims),
        "ndvi_shape": list(ndvi.shape),
        "ndvi_dims": list(ndvi.dims),
        "dates": [str(value)[:10] for value in raw.time.values],
        "minimum": round(minimum, 4),
        "maximum": round(maximum, 4),
        "mean": round(mean, 4),
        "nan_pixels": int(np.isnan(ndvi.values).sum()),
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
