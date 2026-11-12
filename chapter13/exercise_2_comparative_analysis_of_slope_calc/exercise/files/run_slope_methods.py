"""Harness for exercise 2 — two slope estimators on the same DEM.

The two columns are a central difference and Horn's 3x3 kernel. On a plane they must
agree exactly; on independent pixel noise they must not, because the central
difference reads one row of neighbours and Horn averages three. The timing is
machine-dependent and is recorded, never asserted; the disagreement is not.
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
    h = Harness("exercise 2 (slope methods)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "slope_methods.py", "slope_methods")
    printed = log.getvalue()

    import numpy as np

    source = (FILES / "slope_methods.py").read_text(encoding="utf-8")
    h.check("import richdem" not in source,
            "the richDEM column is replaced by Horn's kernel, which computes the "
            "same estimator")

    dem = module.dem_array
    slope_np = module.slope_np
    slope_horn = module.slope_horn
    rmse = module.rmse

    h.equal(dem.shape, (500, 500), "the DEM is the book's 500x500 grid")
    h.equal(dem.size, 250000, "250 000 cells are compared")
    h.close(module.CELL_SIZE, 10.0, "the cell size is 10 m")
    h.equal(slope_np.shape, slope_horn.shape, "both methods return one value per cell")
    h.check(bool(np.all(np.isfinite(slope_np))) and bool(np.all(np.isfinite(slope_horn))),
            "neither method produces NaN or Inf")

    # --- the planes, where there is one right answer --------------------------
    n = 40
    x = np.arange(n) * module.CELL_SIZE
    grade_one = np.tile(x, (n, 1)).astype(np.float64)          # 1 m rise per 1 m run
    h.close(float(module.calculate_slope_numpy(grade_one, module.CELL_SIZE)[20, 20]),
            45.0, "the central difference reads a grade-1 plane as 45 degrees",
            tol=1e-9)
    h.close(float(module.calculate_slope_horn(grade_one, module.CELL_SIZE)[20, 20]),
            45.0, "Horn's kernel reads the same plane as 45 degrees", tol=1e-9)

    grade_half = (0.5 * grade_one)
    plane_np = module.calculate_slope_numpy(grade_half, module.CELL_SIZE)
    plane_horn = module.calculate_slope_horn(grade_half, module.CELL_SIZE)
    diff_plane = float(np.max(np.abs(plane_np[1:-1, 1:-1] - plane_horn[1:-1, 1:-1])))
    h.check(diff_plane < 1e-6,
            "on a plane the two methods agree in the interior to the last decimal "
            "(max difference %.2e degrees)" % diff_plane)
    # The border is where they are allowed to differ: Horn pads with the nearest
    # cell and halves the gradient there, np.gradient falls back to a one-sided
    # difference and keeps it.
    h.check(float(np.max(np.abs(plane_np[0, :] - plane_horn[0, :]))) > 10.0,
            "at the edge the two estimators genuinely disagree, and the harness "
            "compares the interior for that reason")

    # --- the noisy DEM, where they are meant to differ ------------------------
    h.check(rmse > 0.1,
            "on independent pixel noise the two estimators do not give the same map "
            "(RMSE %.2f degrees)" % rmse)
    h.check(rmse < 5.0,
            "they still agree within a few degrees on the same terrain (RMSE %.2f)"
            % rmse)
    h.check(float(slope_np.std()) > float(slope_horn.std()),
            "the central difference is the noisier estimator: it reads one row of "
            "neighbours, Horn averages three")
    h.check(float(slope_np.std()) / float(slope_horn.std()) > 1.2,
            "that difference in spread is substantial, not a rounding effect")
    h.check(float(slope_np.mean()) > float(slope_horn.mean()),
            "averaging the neighbours lowers the mean slope on a rugged surface")

    # The ramp underneath the noise is 0.5 m per 10 m cell: 2.86 degrees.
    ramp = float(np.degrees(np.arctan(0.5 / module.CELL_SIZE)))
    h.close(ramp, 2.8624, "the underlying ramp is 2.86 degrees", tol=1e-3)
    h.check(2.0 < float(slope_horn.mean()) < 6.0,
            "the surface's mean slope sits above the bare ramp and below 6 degrees")
    h.check(float(slope_np.max()) < 90.0 and float(slope_horn.max()) < 90.0,
            "no cell reaches a vertical face")

    # --- the timings, recorded but not asserted ------------------------------
    h.check(module.time_np > 0 and module.time_horn > 0,
            "both timings were measured with a wall clock")
    h.equal(module.REPEATS, 3, "each method is timed best-of-three")

    h.contains(printed, "--- Performance Comparison (Grid Size: (500, 500)) ---",
               "the benchmark reports the grid it timed")
    h.contains(printed, "Root Mean Square Error (RMSE) between methods: 1.4418",
               "the RMSE is reported")
    h.contains(printed, "Cells: 250000", "the cell count is reported")

    h.write_json("slope_methods.json", {
        "grid": [500, 500],
        "cells": int(dem.size),
        "cell_size_m": module.CELL_SIZE,
        "central_difference": {"mean": float(slope_np.mean()),
                               "std": float(slope_np.std()),
                               "max": float(slope_np.max())},
        "horn": {"mean": float(slope_horn.mean()),
                 "std": float(slope_horn.std()),
                 "max": float(slope_horn.max())},
        "rmse_degrees": float(rmse),
        "max_abs_difference_degrees": float(np.abs(slope_np - slope_horn).max()),
        "plane_agreement_degrees": diff_plane,
        "timing_s": {"central_difference": module.time_np, "horn": module.time_horn},
        "timing_note": "machine-dependent; recorded, not asserted",
        "richdem_replaced_by": "Horn 3x3 kernel via scipy.ndimage.correlate",
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (slope methods)", FILES).crash())
