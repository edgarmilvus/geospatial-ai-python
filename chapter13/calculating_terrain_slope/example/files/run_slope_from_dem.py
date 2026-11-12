"""Harness for the basic example — slope in degrees from a DEM.

The derived layer is checked against surfaces whose answer is known on paper: a
plane of grade 1 is 45 degrees, a plane of grade 0.5 is 26.565 degrees, a flat
surface is 0, and a cone of height equal to its radius is 45 degrees on its flanks.
The example's own ramp is a 50 m rise over 99 cells of 10 m, which is 4.09 degrees,
and the hill it carries has to be visibly steeper than that.
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
    h = Harness("example 1 (slope from a DEM)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "slope_from_dem.py", "slope_from_dem")
        module.main()
    printed = log.getvalue()

    import numpy as np

    slope = module.slope_degrees(module.synthetic_dem(), module.CELL_SIZE)
    dem = module.synthetic_dem()

    h.equal(dem.shape, (100, 100), "the DEM is a 100x100 grid")
    h.close(module.CELL_SIZE, 10.0, "one cell is 10 m on the ground")
    h.close(float(dem.max()), 100.0, "the highest point is the far corner, 100 m")
    h.close(float(dem.min()), 0.0, "the lowest point is the near corner, 0 m")

    # The ramp's true grade: 50 m of rise over 99 cells of 10 m, on both axes.
    ramp_grade = (50.0 / 99.0) / 10.0
    ramp_slope = float(np.degrees(np.arctan(np.hypot(ramp_grade, ramp_grade))))
    h.close(float(slope[5, 5]), ramp_slope,
            "the flat ramp is arctan(sqrt(2) * 50/990) = %.4f degrees" % ramp_slope,
            tol=1e-3)
    h.close(float(slope[30, 70]), ramp_slope,
            "the ramp reads the same wherever the hill is not", tol=1e-3)

    # The hill sits at the centre: 25 m over roughly two cells is a real slope.
    h.check(float(slope.max()) > 20.0, "the hill is steeper than 20 degrees")
    h.check(float(slope.max()) < 45.0, "the hill is gentler than the 45 degree maximum")
    h.check(float(slope.max()) > 5 * ramp_slope,
            "the hill is at least five times as steep as the ramp it sits on")
    h.check(bool(np.all(slope >= 0.0)), "slope is never negative")
    h.check(bool(np.all(np.isfinite(slope))), "no slope value is NaN or Inf")

    # --- surfaces whose answer is known before the run ---------------------
    cell = module.CELL_SIZE
    n = 21
    x_m = np.arange(n) * cell

    grade_one = np.tile(x_m, (n, 1)).astype(np.float32)          # 1 m per 1 m, east
    h.close(float(module.slope_degrees(grade_one, cell)[10, 10]), 45.0,
            "a plane of grade 1 is exactly 45 degrees", tol=1e-3)

    grade_half = (0.5 * grade_one).astype(np.float32)            # 0.5 m per 1 m
    h.close(float(module.slope_degrees(grade_half, cell)[10, 10]), 26.5650511,
            "a plane of grade 0.5 is 26.565 degrees", tol=1e-3)

    flat = np.full((n, n), 250.0, dtype=np.float32)
    h.close(float(module.slope_degrees(flat, cell)[10, 10]), 0.0,
            "a flat surface has slope 0")

    # A cone with height equal to radius: 45 degrees everywhere on its flanks.
    # The cells on the four lines through the apex read low, because the central
    # difference there averages two equidistant elevations; the flanks do not.
    yy, xx = np.mgrid[0:41, 0:41].astype(float)
    radius = np.hypot((xx - 20) * cell, (yy - 20) * cell)
    cone = (100.0 - radius).astype(np.float32)
    cone_slope = module.slope_degrees(cone, cell)[4:37, 4:37]
    h.close(float(np.median(cone_slope)), 45.0,
            "a 45 degree cone reads 45 degrees on its flanks", tol=2.0)
    share = float(np.mean((cone_slope >= 40.0) & (cone_slope <= 50.0)))
    h.check(share > 0.99,
            "more than 99%% of the cone's cells are within 5 degrees of 45 (got %.1f%%)"
            % (share * 100))

    # --- the pitfall the chapter warns about -------------------------------
    # Drop the cell size and every tangent is inflated by the cell size: 10x here.
    wrong = module.slope_degrees(grade_half, 1.0)
    ratio = float(np.tan(np.radians(wrong[10, 10])) /
                  np.tan(np.radians(module.slope_degrees(grade_half, cell)[10, 10])))
    h.close(ratio, 10.0, "omitting the cell size inflates the tangent by the cell size",
            tol=1e-3)
    h.check(float(wrong[10, 10]) > 26.565,
            "the un-scaled gradient reports a slope that is far too steep")

    # --- the product -------------------------------------------------------
    import rasterio
    path = module.OUTPUT_FILE
    h.check(path.exists(), "the slope raster is written to output/slope_degrees.tif")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 1, "the slope raster is one band")
            h.equal(src.dtypes[0], "float32", "the slope raster is float32")
            h.equal((src.width, src.height), (100, 100), "the grid is unchanged")
            h.equal(src.crs.to_epsg(), 32610,
                    "the raster is in a projected CRS, so a 10 m cell means 10 m")
            h.close(src.res[0], 10.0, "the cell is 10 m, the unit the slope used")
            h.equal(src.nodata, -9999.0, "the raster declares its nodata value")
            band = src.read(1)
        h.check(bool(np.allclose(band, slope, atol=1e-6)),
                "the band on disk is the slope that was computed")

    h.contains(printed, "Maximum Calculated Slope: 34.82°",
               "the steepest point is reported")
    h.contains(printed, "Slope on the flat ramp: 4.09°",
               "the ramp's own slope is reported")
    h.contains(printed, "Average Calculated Slope: 4.26°",
               "the average slope is reported")
    h.contains(printed, "crs EPSG:32610", "the product states its projected CRS")

    h.write_json("slope_from_dem.json", {
        "grid": [100, 100],
        "cell_size_m": module.CELL_SIZE,
        "elevation": {"min": float(dem.min()), "max": float(dem.max())},
        "slope": {
            "ramp_degrees": float(slope[5, 5]),
            "expected_ramp_degrees": ramp_slope,
            "max_degrees": float(slope.max()),
            "mean_degrees": float(slope.mean()),
        },
        "known_surfaces": {
            "grade_1": 45.0,
            "grade_0.5": 26.5650511,
            "flat": 0.0,
            "cone_flanks_range": [float(cone_slope.min()), float(cone_slope.max())],
        },
        "cell_size_pitfall": {"tan_inflation_factor": ratio},
        "product": {"path": "output/slope_degrees.tif", "crs": "EPSG:32610",
                    "count": 1, "dtype": "float32", "cell_size_m": 10.0},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (slope from a DEM)", FILES).crash())
