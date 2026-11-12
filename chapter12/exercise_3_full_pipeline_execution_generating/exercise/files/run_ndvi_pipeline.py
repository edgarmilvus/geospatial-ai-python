"""Harness for exercise 3 — the index written as a georeferenced GeoTIFF.

The exercise is about the profile, so the checks are about the profile: one band
instead of four, float32 instead of uint16, a declared nodata value, and the input's
CRS and transform carried over unchanged. The pixel values are checked against the
bands on disk, and the 4x4 patch of no signal must arrive as nodata rather than as
an index of 0.0, which would read as bare soil.
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
    h = Harness("exercise 3 (NDVI GeoTIFF pipeline)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "ndvi_geotiff_pipeline.py", "ndvi_geotiff_pipeline")
    printed = log.getvalue()

    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    # The input is a 1 km tile in 50 cells: 20 m per cell, UTM 17N.
    h.close(module.ROWS * 20.0, 1000.0,
            "the scene is 1 km across in 50 cells of 20 m")

    in_path, out_path = module.SCENE_FILE, module.OUTPUT_FILE
    h.check(in_path.exists(), "the input scene is on disk")
    h.check(out_path.exists(), "the index GeoTIFF is written")
    if not out_path.exists():
        return h.report()

    with rasterio.open(in_path) as src:
        input_profile = src.profile.copy()
        red = src.read(module.RED_BAND_INDEX).astype(np.float32)
        nir = src.read(module.NIR_BAND_INDEX).astype(np.float32)

    with rasterio.open(out_path) as out:
        h.equal(out.count, 1, "the product has one band, not the input's four")
        h.equal(out.dtypes[0], "float32", "the product is float32")
        h.equal(out.nodata, -9999.0, "the product declares nodata -9999")
        h.equal((out.width, out.height), (50, 50), "the grid is unchanged")
        h.equal(out.crs, input_profile['crs'], "the CRS is inherited, not re-guessed")
        h.equal(out.transform, input_profile['transform'],
                "the transform is inherited, so the product sits on the same ground")
        h.close(out.transform.a, 20.0, "the cell size is 20 m")
        h.equal(out.transform.c, 300000.0, "the west edge is 300 000 m easting")
        h.equal(out.transform.f, 4001000.0, "the north edge is 4 001 000 m northing")
        band = out.read(1)

    # The band the exercise warns about: a mask built from the denominator, not from 0.
    h.equal(int((band == -9999.0).sum()), 16,
            "the 4x4 patch of zero signal is written as 16 nodata pixels")
    h.check(bool(np.all(band[10:14, 10:14] == -9999.0)),
            "every cell of the shadow patch carries the nodata marker")
    h.check(bool(np.all(band[0:10, :] != -9999.0)),
            "the rest of the raster keeps a real index value")

    valid = band != -9999.0
    h.check(float(band[valid].min()) >= -1.0 and float(band[valid].max()) <= 1.0,
            "every valid index value is inside [-1, 1]")
    h.check(bool(np.all(np.isfinite(band[valid]))),
            "no NaN and no Inf reach the file")

    # One pixel worked out by hand from the input bands.
    row, col = 40, 7
    expected = (float(nir[row, col]) - float(red[row, col])) / \
               (float(nir[row, col]) + float(red[row, col]))
    h.close(float(band[row, col]), expected,
            "pixel (40,7) is (NIR-Red)/(NIR+Red) of the input bands", tol=1e-6)
    h.check(0.2 < expected < 0.9,
            "that pixel is vegetated, as the 1000-1999 / 4000-5999 DN windows imply")

    # Writing twice must produce the same file: the seed decides the scene.
    first = band.copy()
    module.build_scene(module.SCENE_FILE)
    with rasterio.open(out_path) as out:
        h.check(np.array_equal(first, out.read(1)),
                "a rebuild from the same seed gives the same index band")

    h.contains(printed, "New Dtype: float32", "the new dtype is reported")
    h.contains(printed, "New Band Count: 1", "the new band count is reported")
    h.contains(printed, "New NoData Value: -9999.0", "the nodata value is reported")
    h.contains(printed, "Successfully wrote NDVI map to: output/ndvi_map.tif",
               "the listing names the file it wrote")
    h.contains(printed, "Index pixels: 2484 of 2500 (16 nodata)",
               "the usable and nodata counts are reported")

    h.write_json("ndvi_pipeline.json", {
        "input": {
            "path": "output/scene_multiband.tif",
            "count": 4,
            "dtype": "uint16",
            "crs": "EPSG:32617",
            "cell_size_m": 20.0,
        },
        "output": {
            "path": "output/ndvi_map.tif",
            "count": 1,
            "dtype": "float32",
            "nodata": -9999.0,
            "crs": "EPSG:32617",
            "cell_size_m": 20.0,
            "nodata_pixels": int((band == -9999.0).sum()),
            "valid_pixels": int(valid.sum()),
        },
        "pixel_40_7": {"expected": expected, "written": float(band[40, 7])},
        "valid_range": [float(band[valid].min()), float(band[valid].max())],
        "valid_mean": float(band[valid].mean()),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (NDVI GeoTIFF pipeline)", FILES).crash())
