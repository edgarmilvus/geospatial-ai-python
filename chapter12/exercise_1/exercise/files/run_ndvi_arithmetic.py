"""Harness for exercise 1 — the arithmetic core of NDVI, on a 5x5 window.

The exercise is about element-wise arithmetic, so the checks are per-pixel values
worked out on paper from the arrays the listing prints: (0,0) is 400/600, (4,2) is
500/980, the denominator at (2,2) is 940, and the whole 25-pixel window is
vegetated because NIR exceeds Red everywhere.
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
    h = Harness("exercise 1 (NDVI arithmetic core)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "ndvi_arithmetic_core.py", "ndvi_arithmetic_core")
    printed = log.getvalue()

    import numpy as np

    ndvi = module.ndvi_array
    h.equal(ndvi.shape, (5, 5), "the index has one value per input pixel")
    h.equal(str(ndvi.dtype), "float32", "float32 in, float32 out")

    # (0, 0): NIR 500 against Red 100 -> 400 / 600.
    h.close(float(ndvi[0, 0]), 400.0 / 600.0, "pixel (0,0) is 400/600", tol=1e-6)
    # (4, 2): the dimmest return in the window -> 500 / 980.
    h.close(float(ndvi[4, 2]), 500.0 / 980.0, "pixel (4,2) is 500/980", tol=1e-6)
    # (2, 2): the same numerator over the widest denominator in that row.
    h.close(float(ndvi[2, 2]), 500.0 / 940.0, "pixel (2,2) is 500/940", tol=1e-6)

    h.close(float(module.sum_bands[2, 2]), 940.0, "denominator at (2,2) is 220+720",
            tol=1e-6)
    h.close(float(module.diff_bands[0, 0]), 400.0, "numerator at (0,0) is 500-100",
            tol=1e-6)

    h.close(float(np.min(ndvi)), 500.0 / 980.0, "the minimum is the (4,2) pixel",
            tol=1e-6)
    h.close(float(np.max(ndvi)), 400.0 / 600.0, "the maximum is the (0,0) pixel",
            tol=1e-6)
    h.check(bool(np.all(ndvi >= -1.0)) and bool(np.all(ndvi <= 1.0)),
            "every value is inside the theoretical range [-1, 1]")
    h.check(bool(np.all(ndvi > 0)),
            "all 25 pixels are vegetated: NIR exceeds Red everywhere in this window")
    h.check(float(module.sum_bands.min()) > 0,
            "no denominator is zero, so this window cannot divide by zero")
    h.check(bool(np.all(module.diff_bands > 0)),
            "the numerator is positive at every pixel, which is what makes the index positive")

    # A pixel pair the exercise does not contain, as a sanity check of the formula:
    # equal bands give 0.0, water (Red above NIR) gives a negative index.
    equal = (np.float32(300) - np.float32(300)) / (np.float32(300) + np.float32(300))
    h.close(float(equal), 0.0, "equal bands give an index of exactly 0")
    water = (np.float32(20) - np.float32(100)) / (np.float32(20) + np.float32(100))
    h.check(float(water) < 0, "a water pixel gives a negative index")

    h.contains(printed, "--- Denominator Check ---", "the denominator is printed")
    h.contains(printed, "NDVI Data Type: float32", "the dtype is reported")
    h.contains(printed, "NDVI Minimum Value: 0.5102", "the minimum is reported")
    h.contains(printed, "NDVI Maximum Value: 0.6667", "the maximum is reported")
    h.contains(printed, "Values inside [-1, 1]: True", "the range check is reported")
    h.contains(printed, "Pixels computed: 25 (no explicit loop)",
               "the run states that the work was vectorised")

    h.write_json("ndvi_arithmetic.json", {
        "shape": list(ndvi.shape),
        "dtype": str(ndvi.dtype),
        "pixels": {
            "(0,0)": {"expected": 400.0 / 600.0, "ndvi": float(ndvi[0, 0])},
            "(2,2)": {"expected": 500.0 / 940.0, "ndvi": float(ndvi[2, 2])},
            "(4,2)": {"expected": 500.0 / 980.0, "ndvi": float(ndvi[4, 2])},
        },
        "denominator_2_2": float(module.sum_bands[2, 2]),
        "min": float(ndvi.min()),
        "max": float(ndvi.max()),
        "mean": float(ndvi.mean()),
        "all_positive": bool(np.all(ndvi > 0)),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (NDVI arithmetic core)", FILES).crash())
