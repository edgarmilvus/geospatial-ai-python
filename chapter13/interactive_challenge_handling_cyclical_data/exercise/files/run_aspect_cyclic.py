"""Harness for the interactive challenge — aspect as a sine/cosine pair.

The claim the exercise makes is a distance claim: 359 degrees and 1 degree are 358
apart on the raw scale and 2*sin(1) = 0.0349 apart once the direction becomes a point
on the unit circle. The harness checks that distance, the four cardinal directions,
the unit-circle identity, and that the transformed field has no discontinuity where
the raw one has its wrap.
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
    h = Harness("interactive challenge (cyclical aspect)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "aspect_cyclic.py", "aspect_cyclic")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    sine = module.aspect_sine
    cosine = module.aspect_cosine
    aspect = module.aspect_degrees_array

    h.equal(aspect.shape, (50, 50), "the aspect grid is 50x50")
    h.check(bool(np.all(aspect >= 0.0)) and bool(np.all(aspect < 360.0)),
            "the raw aspect is a compass bearing in [0, 360)")

    # --- the four cardinal directions, on the unit circle --------------------
    def pair(degrees):
        s, c = module.transform_cyclical_aspect(np.array([float(degrees)]))
        return float(s[0]), float(c[0])

    h.close(pair(0)[0], 0.0, "north has sine 0", tol=1e-12)
    h.close(pair(0)[1], 1.0, "north has cosine 1", tol=1e-12)
    h.close(pair(90)[0], 1.0, "east has sine 1", tol=1e-12)
    h.close(pair(90)[1], 0.0, "east has cosine 0", tol=1e-12)
    h.close(pair(180)[1], -1.0, "south has cosine -1", tol=1e-12)
    h.close(pair(270)[0], -1.0, "west has sine -1", tol=1e-12)

    # --- the claim: the wrap is a small move in the pair ---------------------
    sin_w, cos_w = pair(359)
    sin_e, cos_e = pair(1)
    distance = float(np.hypot(sin_w - sin_e, cos_w - cos_e))
    h.close(distance, 2 * np.sin(np.radians(1.0)),
            "359 and 1 degrees are 2*sin(1) = 0.0349 apart as points", tol=1e-9)
    h.check(abs(359 - 1) > 300 and distance < 0.05,
            "the same two cells are 358 apart in degrees and 0.035 apart as pairs")

    # --- the transforms are bounded and on the unit circle -------------------
    h.check(float(sine.min()) >= -1.0 and float(sine.max()) <= 1.0,
            "sine stays inside [-1, 1]")
    h.check(float(cosine.min()) >= -1.0 and float(cosine.max()) <= 1.0,
            "cosine stays inside [-1, 1]")
    h.check(bool(np.allclose(sine ** 2 + cosine ** 2, 1.0, atol=1e-12)),
            "every cell lands on the unit circle")

    # A field that turns through north has no jump: the largest step between
    # neighbours is one turn of the ramp (2.4 degrees) whether it crosses north or
    # not, and 2.4 degrees is 0.042 on the sine channel. A raw degree channel would
    # show the wrap as a step of 358.
    step = float(np.abs(np.diff(sine, axis=0)).max())
    h.check(step < 0.05,
            "neighbouring cells differ by less than 0.05 in sine across the whole "
            "field (max step %.5f)" % step)
    h.check(step < 0.5 * float(np.abs(np.diff(aspect, axis=0)).max()),
            "the sine channel's largest step is a small fraction of the raw aspect's")
    h.check(float(aspect.max() - aspect.min()) > 300.0,
            "the raw field itself spans most of the circle, so a linear model would "
            "read that span as one enormous distance")

    # --- the stack ------------------------------------------------------------
    stack = module.new_stack
    h.equal(stack.shape, (4, 50, 50), "the stack grew from three channels to four")
    h.check(bool(np.array_equal(stack[2], sine)),
            "channel 2 is the sine of aspect")
    h.check(bool(np.array_equal(stack[3], cosine)),
            "channel 3 is the cosine of aspect")
    h.close(float(stack[0].mean()), 0.0, "the elevation channel is still standardized",
            tol=1e-9)

    path = module.OUTPUT_FILE
    h.check(path.exists(), "the two new channels are written to output/")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 2, "the raster holds the sine and the cosine")
            h.equal(src.dtypes[0], "float32", "the raster is float32")
            bands = src.read()
        h.check(bool(np.allclose(bands[0], sine, atol=1e-6)),
                "band 1 is the sine of aspect")
        h.check(bool(np.allclose(bands[1], cosine, atol=1e-6)),
                "band 2 is the cosine of aspect")

    h.contains(printed, "New Feature Stack Shape (Channels, H, W): (4, 50, 50)",
               "the new stack shape is reported")
    h.contains(printed, "as (sin, cos) pairs: 0.0349",
               "the pair distance is reported next to the 358 degrees")
    h.contains(printed, "Unit circle preserved: True",
               "the unit-circle check is reported")

    h.write_json("aspect_cyclic.json", {
        "grid": [50, 50],
        "aspect_range_degrees": [float(aspect.min()), float(aspect.max())],
        "cardinal": {str(d): dict(zip(("sin", "cos"), pair(d)))
                     for d in (0, 90, 180, 270)},
        "wrap_distance": {"degree_gap": 358, "pair_distance": distance,
                          "closed_form_2sin1": 2 * float(np.sin(np.radians(1.0)))},
        "sine_range": [float(sine.min()), float(sine.max())],
        "cosine_range": [float(cosine.min()), float(cosine.max())],
        "max_neighbour_step_sine": step,
        "stack_shape": list(stack.shape),
        "product": {"path": "output/aspect_cyclical.tif", "bands": 2},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("interactive challenge (cyclical aspect)", FILES).crash())
