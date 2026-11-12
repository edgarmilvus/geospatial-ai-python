"""Harness for the basic example — the 4D stack reduced to a 3D NDVI cube.

The listing simulates (Time, Height, Width, Bands) and iterates the time axis.
The harness checks the two things that iteration can get wrong: the band index
(Red is 0, NIR is 1) and the division by zero that `np.where` is there to stop.
It also checks that the simulated stress really is a drop, not a rise.
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

NAME = "example 1 (NDVI time series stack)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_ndvi_time_series_stack.py", "ndvi_stack")
    printed = log.getvalue()

    stack = module.final_ndvi_stack
    cube = module.data_stack

    # -- the shapes ------------------------------------------------------
    h.equal(cube.shape, (3, 10, 10, 2),
            "the cube is three dates of ten by ten pixels with two bands")
    h.equal(stack.shape, (3, 10, 10), "the NDVI stack drops the band axis")
    h.equal(module.NUM_TIMESTEPS, 3, "three observations are simulated")

    # -- the bands are not swapped ---------------------------------------
    # Red is band 0 and NIR is band 1; NDVI must be positive for a healthy pixel.
    t1 = stack[0]
    h.check(float(t1.min()) > 0.3, "every T1 pixel reads as vegetation")
    manual = ((cube[0, 0, 0, 1] - cube[0, 0, 0, 0]) /
              (cube[0, 0, 0, 1] + cube[0, 0, 0, 0]))
    h.close(float(t1[0, 0]), float(manual),
            "pixel (0, 0) is (NIR - Red) / (NIR + Red) with NIR at index 1")

    # Swapping the two bands inverts the sign of every pixel; that is the pitfall.
    inverted = module.calculate_ndvi(cube[0, :, :, 1], cube[0, :, :, 0])
    h.check(float(inverted.mean()) < -0.3,
            "reading Red as NIR would report bare earth for a healthy forest")

    # -- the simulated stress --------------------------------------------
    means = [float(layer.mean()) for layer in stack]
    h.check(0.65 <= means[0] <= 0.80, "T1 mean NDVI is about 0.7 (got %.4f)" % means[0])
    h.check(0.30 <= means[1] <= 0.45, "T2 mean NDVI is about 0.4 (got %.4f)" % means[1])
    h.check(-0.40 <= means[2] <= -0.20, "T3 mean NDVI is negative (got %.4f)" % means[2])
    h.check(means[0] > means[1] > means[2], "the three means fall month after month")
    h.check(means[0] - means[2] > 0.9,
            "the drop from T1 to T3 is larger than 0.9 NDVI units")

    h.check(float(stack.min()) >= -1.0 and float(stack.max()) <= 1.0,
            "every value stays inside NDVI's -1..1 range")

    # -- the guard the chapter highlights ---------------------------------
    # `np.where` computes both branches before it chooses, so 0 / 0 still raises
    # a RuntimeWarning even though the chosen value is 0.0. The harness silences
    # the warning and asserts the value, which is what reaches the stack.
    zeros = np.zeros((3, 3), dtype=np.float32)
    with np.errstate(invalid="ignore", divide="ignore"):
        guarded = module.calculate_ndvi(zeros, zeros)
    h.equal(float(guarded.sum()), 0.0,
            "a zero denominator yields 0.0 instead of NaN")
    h.check(not np.isnan(guarded).any(),
            "no NaN reaches the stack from a black pixel")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Time Step T1:", "the listing labels each time step")
    h.contains(printed, "Final NDVI stack shape: (3, 10, 10)",
               "the listing prints the shape the assertion above checks")
    h.contains(printed, "Change detected: T1 Mean NDVI", "the listing reports the change")

    h.write_json("ndvi_stack.json", {
        "cube_shape": list(cube.shape),
        "ndvi_shape": list(stack.shape),
        "mean_ndvi_per_step": [round(value, 4) for value in means],
        "drop_t1_to_t3": round(means[0] - means[2], 4),
        "min": round(float(stack.min()), 4),
        "max": round(float(stack.max()), 4),
        "zero_denominator_result": 0.0,
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
