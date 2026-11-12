"""Harness for exercise 4 — the four-channel stack, with curvature added.

The DEM carries a hill and a hollow, so the curvature channel has an answer that can
be written before the run: at the centre of a Gaussian bump the curvature along the
fall line is A / sigma^2, which is 50/80^2 = +0.0078 per metre on the hill and
-40/60^2 = -0.0111 per metre in the hollow. The rest is the stack itself: three
standardized channels, one raw cyclical channel, and the band order on disk.
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
    h = Harness("exercise 4 (feature stack with curvature)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "feature_stack_curvature.py",
                              "feature_stack_curvature")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    source = (FILES / "feature_stack_curvature.py").read_text(encoding="utf-8")
    h.check("import richdem" not in source,
            "curvature is computed in the listing, not imported from richDEM")

    dem = module.synthetic_dem()
    stack = module.feature_stack
    h.equal(stack.shape, (4, 100, 100), "the stack is channel-first: four layers")
    h.equal(str(stack.dtype), "float32", "the stack is float32, as a model expects")

    # --- the curvature channel, against the shape it was built from --------
    curvature = module.profile_curvature(dem, module.CELL_SIZE)
    # The hill is centred at x = y = 150 m, which is cell (30, 30) on a 5 m grid;
    # the hollow at 350 m is cell (70, 70).
    hill = float(curvature[30, 30])
    hollow = float(curvature[70, 70])
    h.close(hill, 50.0 / 80.0 ** 2,
            "the hill's curvature is A/sigma^2 = +0.0078 per metre", tol=1e-4)
    h.close(hollow, -40.0 / 60.0 ** 2,
            "the hollow's curvature is -A/sigma^2 = -0.0111 per metre", tol=1e-4)
    h.check(hill > 0 > hollow, "convex ground is positive, a hollow is negative")
    h.check(float(curvature[3:-3, 3:-3].max()) > 0
            and float(curvature[3:-3, 3:-3].min()) < 0,
            "the interior of the scene holds both signs, so the layer can separate "
            "a ridge from a channel")

    # --- the standardization --------------------------------------------------
    elevation = dem.astype(np.float64)
    slope = module.slope_degrees(dem, module.CELL_SIZE)
    aspect = module.aspect_degrees(dem, module.CELL_SIZE)

    for name, channel, raw in (("elevation", stack[0], elevation),
                               ("slope", stack[1], slope),
                               ("curvature", stack[3], curvature)):
        h.close(float(channel.mean()), 0.0, "%s is standardized to mean 0" % name,
                tol=1e-5)
        h.close(float(channel.std()), 1.0,
                "%s is standardized to unit deviation" % name, tol=1e-5)
        # Standardization is affine: multiplying back must return the input.
        restored = channel * raw.std() + raw.mean()
        h.check(bool(np.allclose(restored, raw, atol=1e-4)),
                "%s can be restored from its z-score" % name)

    h.check(bool(np.array_equal(stack[2], aspect.astype(np.float32))),
            "channel 2 is the raw aspect, untouched by the scaler")
    h.check(bool(np.all(stack[2] >= 0.0)) and bool(np.all(stack[2] < 360.0)),
            "raw aspect stays a compass bearing in [0, 360)")
    h.check(abs(float(stack[2].mean()) - 180.0) < 90.0,
            "raw aspect is not standardized: its mean is near 180, not 0")

    # --- the helper on its own ------------------------------------------------
    constant = np.full((4, 4), 7.5)
    h.check(bool(np.all(module.z_score_normalize(constant) == 0.0)),
            "a constant band standardizes to zeros rather than dividing by zero")
    ramp = np.array([[1.0, 2.0], [3.0, 4.0]])
    z = module.z_score_normalize(ramp)
    h.close(float(z.mean()), 0.0, "the helper centres the band", tol=1e-12)
    h.close(float(z.std()), 1.0, "the helper scales the band", tol=1e-12)

    # --- the stack on disk ----------------------------------------------------
    path = module.OUTPUT_FILE
    h.check(path.exists(), "the stack is written to output/")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 4, "the raster holds four bands, one per feature")
            h.equal(src.dtypes[0], "float32", "the stack is float32 on disk")
            h.equal((src.width, src.height), (100, 100), "the stack keeps the DEM grid")
            h.equal(src.crs.to_epsg(), 32610, "the stack carries the DEM's CRS")
            bands = src.read()
        for index in range(4):
            h.check(bool(np.allclose(bands[index], stack[index], atol=1e-6)),
                    "band %d on disk is channel %d of the stack" % (index + 1, index + 1))

    h.contains(printed, "Stack Shape: (4, 100, 100)", "the stack shape is reported")
    h.contains(printed, "[2]: Raw Aspect (Degrees)",
               "the channel order is documented in the output")
    h.contains(printed, "Wrote 4-band stack to: output/advanced_feature_stack.tif",
               "the listing names the file it wrote")

    h.write_json("feature_stack_curvature.json", {
        "stack_shape": list(stack.shape),
        "channels": ["normalized elevation", "normalized slope",
                     "raw aspect (degrees)", "normalized profile curvature"],
        "curvature": {"hill": hill, "hill_expected": 50.0 / 80.0 ** 2,
                      "hollow": hollow, "hollow_expected": -40.0 / 60.0 ** 2,
                      "interior_range": [float(curvature[3:-3, 3:-3].min()),
                                         float(curvature[3:-3, 3:-3].max())]},
        "standardized": {"elevation": [float(stack[0].mean()), float(stack[0].std())],
                         "slope": [float(stack[1].mean()), float(stack[1].std())],
                         "curvature": [float(stack[3].mean()), float(stack[3].std())]},
        "aspect_raw_range": [float(stack[2].min()), float(stack[2].max())],
        "product": {"path": "output/advanced_feature_stack.tif", "bands": 4,
                    "dtype": "float32", "crs": "EPSG:32610"},
        "richdem_replaced_by": "Zevenbergen & Thorne 3x3 curvature stencil",
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (feature stack with curvature)", FILES).crash())
