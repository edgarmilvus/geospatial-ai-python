"""Harness for the advanced script — three terrain features, standardized, stacked.

richDEM is replaced by Horn's 3x3 kernel and the Zevenbergen & Thorne curvature
stencil, so the harness can check the estimators themselves: the compass convention
of aspect on four planes, the 45 degree answer of a grade-1 plane, curvature sign on
a dome and on a bowl, and the analytic bound on a sine surface whose steepest
possible slope is atan(hypot(50/300 + 0.02, 50/250)) = 15.31 degrees.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def plane(n, cell, grade_x, grade_y):
    """A tilted plane: z = grade_x * x + grade_y * y, with y growing southward."""
    import numpy as np
    x = np.arange(n) * cell
    y = np.arange(n) * cell
    return (grade_x * x[None, :] + grade_y * y[:, None]).astype(np.float32)


def main():
    h = Harness("example 2 (terrain feature stack)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "terrain_feature_stack.py", "terrain_feature_stack")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    # richDEM has no wheel here. The listing must compute the layers itself, and
    # the harness is where that decision is held to account.
    source = (FILES / "terrain_feature_stack.py").read_text(encoding="utf-8")
    h.check("import richdem" not in source,
            "the listing does not import richDEM, which has no installable wheel")

    dem = module.synthetic_dem()
    cell = module.RESOLUTION
    h.equal(dem.shape, (128, 128), "the DEM is a 128x128 grid")
    h.close(cell, 10.0, "one cell is 10 m")
    h.check(50.0 < float(dem.min()) and float(dem.max()) < 180.0,
            "elevation stays in the 50-180 m band the surface was built for")

    # --- the estimators, on surfaces whose answer is known -------------------
    n = 21
    h.close(float(module.slope_degrees(plane(n, cell, 1.0, 0.0), cell)[10, 10]),
            45.0, "Horn's kernel reads a grade-1 plane as exactly 45 degrees", tol=1e-6)

    # Aspect: 0 north, 90 east, 180 south, 270 west, measured clockwise.
    h.close(float(module.aspect_degrees(plane(n, cell, 1.0, 0.0), cell)[10, 10]),
            270.0, "ground rising eastward faces west: aspect 270", tol=1e-6)
    h.close(float(module.aspect_degrees(plane(n, cell, -1.0, 0.0), cell)[10, 10]),
            90.0, "ground rising westward faces east: aspect 90", tol=1e-6)
    h.close(float(module.aspect_degrees(plane(n, cell, 0.0, 1.0), cell)[10, 10]),
            0.0, "ground rising southward faces north: aspect 0", tol=1e-6)
    h.close(float(module.aspect_degrees(plane(n, cell, 0.0, -1.0), cell)[10, 10]),
            180.0, "ground rising northward faces south: aspect 180", tol=1e-6)
    h.close(float(module.aspect_degrees(plane(n, cell, 1.0, -1.0), cell)[10, 10]),
            225.0, "ground rising north-east faces south-west: aspect 225", tol=1e-6)
    h.close(float(module.aspect_degrees(plane(n, cell, 0.0, 0.0), cell)[10, 10]),
            0.0, "a flat cell has no aspect and reads 0")

    # Curvature: convex ground positive, hollow ground negative, a plane zero.
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    r2 = ((xx - 10) * cell) ** 2 + ((yy - 10) * cell) ** 2
    dome = (500.0 - 0.01 * r2).astype(np.float32)
    bowl = (0.01 * r2).astype(np.float32)
    h.check(float(np.median(module.profile_curvature(dome, cell)[5:16, 5:16])) > 0,
            "a dome has positive profile curvature (flow diverges, accelerates)")
    h.check(float(np.median(module.profile_curvature(bowl, cell)[5:16, 5:16])) < 0,
            "a bowl has negative profile curvature (flow converges)")
    h.close(float(np.abs(module.profile_curvature(plane(n, cell, 0.5, 0.3), cell)[10, 10])),
            0.0, "a plane has no curvature", tol=1e-9)

    # --- the example's own layers -------------------------------------------
    slope = module.slope_degrees(dem, cell)
    aspect = module.aspect_degrees(dem, cell)
    curvature = module.profile_curvature(dem, cell)

    # The steepest slope the surface can have: |dZ/dx| <= 50/300 + 0.02 and
    # |dZ/dy| <= 50/250, so anything above atan(hypot(0.18667, 0.2)) is a bug.
    bound = float(np.degrees(np.arctan(np.hypot(50.0 / 300.0 + 0.02, 50.0 / 250.0))))
    h.check(float(slope.max()) < bound,
            "no slope exceeds the surface's analytic maximum of %.2f degrees" % bound)
    h.check(float(slope.max()) > 5.0, "the surface is not flat: slopes pass 5 degrees")
    h.check(float(slope.min()) >= 0.0, "slope is never negative")
    h.check(bool(np.all(aspect >= 0.0)) and bool(np.all(aspect < 360.0)),
            "aspect is a compass bearing in [0, 360)")
    h.check(bool(np.all(np.isfinite(curvature))), "curvature is finite everywhere")

    # --- standardization -----------------------------------------------------
    h.equal(len(module.feature_list), 3, "three features are stacked")
    for name, band in zip(("slope", "aspect", "p_curvature"), module.feature_list):
        h.equal(band.shape, (128, 128), "%s keeps the grid" % name)
        h.close(float(band.mean()), 0.0, "%s is standardized to mean 0" % name, tol=1e-6)
        h.close(float(band.std()), 1.0, "%s is standardized to unit deviation" % name,
                tol=1e-6)

    # --- the stack on disk ---------------------------------------------------
    path = module.FEATURE_STACK_FILE
    h.check(path.exists(), "the feature stack is written to output/")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 3, "the stack holds three bands, one per feature")
            h.equal(src.dtypes[0], "float32", "the stack is float32")
            h.equal((src.width, src.height), (128, 128), "the stack keeps the DEM grid")
            h.equal(src.crs.to_epsg(), 32610, "the stack carries the DEM's CRS")
            bands = src.read()
        for index, band in enumerate(module.feature_list):
            h.check(bool(np.allclose(bands[index], band, atol=1e-6)),
                    "band %d on disk is feature %d of the stack" % (index + 1, index + 1))

    # --- hillshade -----------------------------------------------------------
    flat = np.full((n, n), 250.0, dtype=np.float32)
    h.close(float(module.hillshade(flat, cell)[10, 10]), 180.3122,
            "a flat surface under a 45 degree sun reads 255*cos(45) = 180.31", tol=0.01)
    north_facing = module.hillshade(plane(n, cell, 0.0, 0.3), cell)[10, 10]
    south_facing = module.hillshade(plane(n, cell, 0.0, -0.3), cell)[10, 10]
    h.check(float(north_facing) > float(south_facing),
            "with the sun in the north-west, a north-facing slope is the brighter one")
    shade = module.hillshade(dem, cell)
    h.check(float(shade.min()) >= 0.0 and float(shade.max()) <= 255.0,
            "hillshade is an 8-bit grey range, 0 to 255")
    h.check(module.HILLSHADE_FILE.exists(), "the relief check is written to output/")
    h.check((module.OUTPUT_DIR / "terrain_overview.png").exists(),
            "the overview figure is written to output/")

    h.contains(printed, "Bands: 3", "the stack's band count is reported")
    h.contains(printed, "Stack shape (channels, rows, cols): (3, 128, 128)",
               "the stack's channel-first shape is reported")
    h.contains(printed, "-> Standardized slope. Shape: (128, 128)",
               "each standardized feature is announced")
    h.contains(printed, "Slope: 0.10° to 11.36°", "the slope range is reported")

    h.write_json("terrain_feature_stack.json", {
        "dem": {"shape": [128, 128], "cell_size_m": 10.0,
                "elevation_m": [float(dem.min()), float(dem.max())]},
        "layers": {
            "slope_degrees": [float(slope.min()), float(slope.max())],
            "aspect_degrees": [float(aspect.min()), float(aspect.max())],
            "profile_curvature_per_m": [float(curvature.min()), float(curvature.max())],
        },
        "analytic_slope_bound_degrees": bound,
        "standardized": {name: {"mean": float(band.mean()), "std": float(band.std())}
                         for name, band in zip(("slope", "aspect", "p_curvature"),
                                               module.feature_list)},
        "stack": {"path": "output/terrain_feature_stack.tif", "bands": 3,
                  "dtype": "float32", "shape": [3, 128, 128]},
        "hillshade": {"flat_value": float(255.0 * np.cos(np.radians(45.0))),
                      "north_facing": float(north_facing),
                      "south_facing": float(south_facing)},
        "richdem_replaced_by": "Horn 3x3 gradient + Zevenbergen & Thorne curvature",
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (terrain feature stack)", FILES).crash())
