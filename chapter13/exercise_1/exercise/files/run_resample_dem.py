"""Harness for exercise 1 — 1 m DEM to 10 m, extent unchanged.

The mean is the number that matters: the input is a southward ramp of 0.4 m per row
plus noise, so its mean is 0.4 * 499.5 + 2.5 = 202.3 m and a bilinear resample has
to return it. The harness also checks the geometry the exercise is really about: the
same ground, ten times the cell, one tenth the cells.
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
    h = Harness("exercise 1 (DEM resampling)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "resample_dem.py", "resample_dem")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    # The dimension helper on its own.
    h.equal(module.calculate_new_dims(1000, 1000, 10.0), (100, 100),
            "a 10x coarser grid has a tenth of the cells on each side")
    h.equal(module.calculate_new_dims(1000, 1000, 2.5), (400, 400),
            "a 2.5x coarser grid has 400 cells on each side")

    in_path, out_path = module.input_path, module.output_path
    h.check(in_path.exists(), "the 1 m DEM is on disk")
    h.check(out_path.exists(), "the 10 m DEM is written")
    if not (in_path.exists() and out_path.exists()):
        return h.report()

    with rasterio.open(in_path) as src:
        h.equal((src.width, src.height), (1000, 1000), "the input is 1000x1000 cells")
        h.close(src.res[0], 1.0, "the input cell is 1 m")
        h.equal(src.crs.to_epsg(), 32617, "the input is in UTM 17N")
        h.equal(src.dtypes[0], "float32", "the input is float32")
        in_bounds = src.bounds
        original = src.read(1)

    with rasterio.open(out_path) as dst:
        h.equal((dst.width, dst.height), (100, 100), "the output is 100x100 cells")
        h.close(dst.res[0], 10.0, "the output cell is 10 m")
        h.close(dst.res[1], 10.0, "the output cell is 10 m north-south too")
        h.equal(dst.crs, src.crs, "the output keeps the input CRS")
        h.equal(dst.dtypes[0], "float32", "the output keeps the input dtype")
        h.close(dst.transform.c, 100000.0, "the output starts at the same easting")
        h.close(dst.transform.f, 500000.0, "the output starts at the same northing")
        out_bounds = dst.bounds
        resampled = dst.read(1)

    # The whole point of a correct new transform: the footprint does not move.
    for name, left, right in zip(("west", "south", "east", "north"),
                                 in_bounds, out_bounds):
        h.close(right, left, "the %s edge is preserved to the micrometre" % name,
                tol=1e-6)

    h.equal(resampled.shape, (100, 100), "the resampled array is 100x100")
    h.check(bool(np.all(np.isfinite(resampled))), "resampling introduced no NaN")

    # 0.4 m per row over 1000 rows plus noise of mean 2.5 m.
    expected_mean = 0.4 * 999 / 2 + 2.5
    h.close(float(original.mean()), expected_mean,
            "the 1 m DEM's mean is 0.4*499.5 + 2.5 = %.2f m" % expected_mean, tol=1.0)
    h.close(float(resampled.mean()), float(original.mean()),
            "bilinear resampling preserves the mean of a linear ramp", tol=0.05)
    ratio = float(resampled.std() / original.std())
    h.check(0.99 < ratio <= 1.01,
            "the standard deviation survives the resample (ratio %.4f)" % ratio)
    h.check(float(resampled.max()) <= float(original.max()) + 1e-3,
            "no resampled cell rises above the highest input cell")

    h.contains(printed, "Dimensions (W x H): 1000 x 1000",
               "the input dimensions are reported")
    h.contains(printed, "Resolution (X, Y): (1.0, 1.0)",
               "the input resolution is reported")
    h.contains(printed, "Original Mean/Std: 202.30 / 115.48",
               "the input statistics are reported")
    h.contains(printed, "New grid: 100 x 100 at 10.0 m", "the new grid is reported")
    h.contains(printed, "Extent preserved: True", "the extent check is reported")
    h.contains(printed, "Successfully wrote resampled DEM to output/resampled_output_dem.tif",
               "the listing names the file it wrote")

    h.write_json("dem_resampling.json", {
        "input": {"shape": [1000, 1000], "cell_size_m": 1.0, "crs": "EPSG:32617",
                  "mean_m": float(original.mean()), "std_m": float(original.std())},
        "output": {"shape": [100, 100], "cell_size_m": 10.0, "crs": "EPSG:32617",
                   "mean_m": float(resampled.mean()), "std_m": float(resampled.std())},
        "mean_difference_m": abs(float(original.mean()) - float(resampled.mean())),
        "std_ratio": ratio,
        "expected_mean_m": expected_mean,
        "bounds_preserved": [list(in_bounds), list(out_bounds)],
        "resampling": "bilinear",
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (DEM resampling)", FILES).crash())
