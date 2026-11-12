"""Harness for the basic example — NDVI from two reflectance bands, and the GeoTIFF.

The example is arithmetic, so the checks are arithmetic: two pixels whose index can
be worked out on paper before the run (a healthy corn pixel at 0.10/0.55 and a mixed
pixel at 0.35/0.45), the index range, the absence of a zero denominator in this
window, and the georeferenced product the listing writes.
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
    h = Harness("example 1 (NDVI band math)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "ndvi_band_math.py", "ndvi_band_math")
        module.main()
    printed = log.getvalue()

    import numpy as np
    import rasterio

    ndvi, numerator, denominator = module.calculate_ndvi(
        module.red_band_data, module.nir_band_data)

    # The index of two pixels that can be computed by hand: NDVI = (NIR-Red)/(NIR+Red).
    # (0, 0) is a healthy corn pixel, red 0.10 and NIR 0.55 -> 0.45 / 0.65.
    # float32 reflectance carries about seven digits, so the tolerance is 1e-6, not 1e-9.
    h.close(float(ndvi[0, 0]), 0.45 / 0.65,
            "healthy pixel (0,0): (NIR-Red)/(NIR+Red)", tol=1e-6)
    # (1, 2) is the mixed/bare-soil pixel, red 0.35 against NIR 0.45 -> 0.10 / 0.80.
    h.close(float(ndvi[1, 2]), 0.10 / 0.80, "mixed pixel (1,2): 0.10 / 0.80 = 0.125",
            tol=1e-6)
    # (1, 0) is the stressed pixel: red 0.25 nearly balances NIR 0.30 -> 0.05 / 0.55.
    h.close(float(ndvi[1, 0]), 0.05 / 0.55, "stressed pixel (1,0): 0.05 / 0.55",
            tol=1e-6)

    h.equal(ndvi.shape, (3, 3), "the index keeps the shape of the input bands")
    h.equal(str(ndvi.dtype), "float32", "the index is float32, as reflectance math needs")
    h.check(float(np.min(ndvi)) >= -1.0 and float(np.max(ndvi)) <= 1.0,
            "every index value falls in the theoretical range [-1, 1]")
    h.close(float(np.max(ndvi)), 0.45 / 0.65, "the maximum is the healthy corner", tol=1e-6)
    h.close(float(np.min(ndvi)), 0.05 / 0.55, "the minimum is the stressed pixel", tol=1e-6)

    h.check(float(denominator.min()) > 0,
            "no denominator is zero in this window, so no division warning is due")
    h.close(float(numerator[0, 0]), 0.45, "numerator at (0,0) is NIR - Red", tol=1e-6)
    h.close(float(denominator[0, 0]), 0.65, "denominator at (0,0) is NIR + Red", tol=1e-6)

    # A water pixel: red 0.10, NIR 0.02. Water absorbs NIR, so the index is negative.
    water, _, _ = module.calculate_ndvi(
        np.array([[0.10]], dtype=np.float32), np.array([[0.02]], dtype=np.float32))
    h.check(float(water[0, 0]) < 0,
            "a water pixel (Red 0.10 > NIR 0.02) gets a negative index")

    # --- the GeoTIFF the listing writes -------------------------------------
    path = module.OUTPUT_FILE
    h.check(path.exists(), "the listing writes output/ndvi_basic.tif")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 1, "the product is a single band, not a band stack")
            h.equal(src.dtypes[0], "float32", "the product stores float32")
            h.equal(src.nodata, -9999.0, "the product declares its nodata value")
            h.equal((src.width, src.height), (3, 3), "the product keeps the 3x3 grid")
            h.equal(src.crs.to_epsg(), 32610, "the product is georeferenced in UTM 10N")
            h.close(src.res[0], 10.0, "the product keeps the 10 m cell size")
            band = src.read(1)
        h.check(np.allclose(band, ndvi, atol=1e-6),
                "the band on disk is the index that was computed")

    # Strings last: what the reader sees.
    h.contains(printed, "--- Final NDVI Map", "the listing prints the index map")
    h.contains(printed, "Max NDVI recorded: 0.6923", "the listing reports the maximum")
    h.contains(printed, "Min NDVI recorded: 0.0909", "the listing reports the minimum")
    h.contains(printed, "File: output/ndvi_basic.tif", "the listing names what it wrote")
    h.contains(printed, "cell size: 10.0 m", "the listing states the resolution")

    h.write_json("ndvi_band_math.json", {
        "pixel_0_0": {"red": 0.10, "nir": 0.55, "ndvi": float(ndvi[0, 0])},
        "pixel_1_2": {"red": 0.35, "nir": 0.45, "ndvi": float(ndvi[1, 2])},
        "pixel_1_0": {"red": 0.25, "nir": 0.30, "ndvi": float(ndvi[1, 0])},
        "min": float(ndvi.min()),
        "max": float(ndvi.max()),
        "mean": float(ndvi.mean()),
        "dtype": str(ndvi.dtype),
        "geotiff": {
            "path": "output/ndvi_basic.tif",
            "count": 1,
            "dtype": "float32",
            "nodata": -9999.0,
            "crs": "EPSG:32610",
            "cell_size_m": 10.0,
            "shape": list(ndvi.shape),
        },
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (NDVI band math)", FILES).crash())
