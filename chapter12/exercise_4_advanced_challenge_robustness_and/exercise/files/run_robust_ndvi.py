"""Harness for exercise 4 — the zero denominator, and the difference between 0 and nodata.

The exercise's failure mode is quiet: 0/0 becomes NaN, X/0 becomes Inf, and the map
still looks like an array. The harness checks that the 10x10 forced-zero block comes
back as -9999 rather than 0.0, that nothing non-finite survives, and that the two
methods the book compares agree pixel for pixel.
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
    h = Harness("exercise 4 (robust NDVI)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "robust_ndvi.py", "robust_ndvi")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    robust = module.ndvi_robust
    alternative = module.ndvi_alternative
    nodata = module.NODATA_VALUE

    h.equal(robust.shape, (256, 256), "the map covers the 256x256 grid")
    h.equal(str(robust.dtype), "float32", "the masked map is float32")

    # The forced block: 10x10 pixels of no signal, and no other pixel has one.
    h.equal(int((robust == nodata).sum()), 100,
            "exactly the 100 forced-zero pixels are marked nodata")
    h.check(bool(np.all(robust[100:110, 100:110] == nodata)),
            "every cell of the 10x10 block is nodata")
    h.close(float(robust[105, 105]), nodata,
            "the pixel at [105,105] is nodata, not an index of 0.0")
    h.check(robust[105, 105] != 0.0,
            "nodata is not confused with the bare-soil index of 0.0")

    h.equal(int(np.isnan(robust).sum()), 0, "no NaN survives the masked division")
    h.equal(int(np.isinf(robust).sum()), 0, "no Inf survives the masked division")
    h.equal(int(np.isnan(alternative).sum()), 0, "the nan_to_num path leaves no NaN")
    h.equal(int(np.isinf(alternative).sum()), 0, "the nan_to_num path leaves no Inf")
    h.check(bool(np.array_equal(robust, alternative)),
            "np.where and nan_to_num give the same array, pixel for pixel")

    valid = robust != nodata
    h.equal(int(valid.sum()), 256 * 256 - 100,
            "65436 pixels keep a real index value")
    h.check(float(robust[valid].min()) >= -1.0 and float(robust[valid].max()) <= 1.0,
            "every valid value is inside [-1, 1]")
    h.check(float(robust[valid].min()) < 0 < float(robust[valid].max()),
            "the scene holds both water and vegetation, so the index spans zero")
    # A pixel pair recomputed from the input bands: the division is the formula.
    row, col = 200, 30
    expected = (float(module.nir_noisy[row, col]) - float(module.red_noisy[row, col])) / \
               (float(module.nir_noisy[row, col]) + float(module.red_noisy[row, col]))
    h.close(float(robust[row, col]), expected,
            "pixel (200,30) is (NIR-Red)/(NIR+Red) of the input bands", tol=1e-6)

    # The rebuild is deterministic: the seed decides which pixels are noisy.
    rng = np.random.default_rng(module.SEED)
    nir = rng.integers(50, 800, size=(256, 256)).astype(np.float32)
    red = rng.integers(30, 700, size=(256, 256)).astype(np.float32)
    nir[100:110, 100:110] = 0.0
    red[100:110, 100:110] = 0.0
    h.check(np.array_equal(nir, module.nir_noisy) and np.array_equal(red, module.red_noisy),
            "the seed alone rebuilds the noisy scene")

    path = module.OUTPUT_FILE
    h.check(path.exists(), "the masked index is written to output/ndvi_robust.tif")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 1, "the product is one band")
            h.equal(src.dtypes[0], "float32", "the product is float32")
            h.equal(src.nodata, -9999.0, "the product declares -9999 as nodata")
            band = src.read(1)
        h.equal(int((band == -9999.0).sum()), 100,
                "the 100 nodata pixels survive the write")

    h.contains(printed, "NDVI value at forced zero sum area [105, 105]: -9999.0",
               "the listing shows the nodata assignment")
    h.contains(printed, "Both methods agree pixel for pixel: True",
               "the listing states the two methods agree")
    h.contains(printed, "NaN values left in the map: 0", "the NaN count is reported")
    h.contains(printed, "Pixels assigned NODATA: 100", "the nodata count is reported")

    h.write_json("robust_ndvi.json", {
        "grid": [256, 256],
        "nodata_value": nodata,
        "epsilon": module.EPSILON,
        "nodata_pixels": int((robust == nodata).sum()),
        "valid_pixels": int(valid.sum()),
        "nan_count": int(np.isnan(robust).sum()),
        "inf_count": int(np.isinf(robust).sum()),
        "methods_agree": bool(np.array_equal(robust, alternative)),
        "valid_range": [float(robust[valid].min()), float(robust[valid].max())],
        "valid_mean": float(robust[valid].mean()),
        "pixel_105_105": float(robust[105, 105]),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (robust NDVI)", FILES).crash())
