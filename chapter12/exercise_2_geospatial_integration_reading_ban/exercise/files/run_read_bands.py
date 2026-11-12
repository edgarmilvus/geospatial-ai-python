"""Harness for exercise 2 — opening a four-band tile and taking bands 3 and 4.

The trap in this exercise is the 1-based band index, so the harness checks that band
3 is the Red the listing asked for and not band 1; it also checks the metadata the
next exercise needs to write a georeferenced product: a 0.02 degree cell over
10°W-9°W and 40°N-41°N.
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
    h = Harness("exercise 2 (reading bands with rasterio)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "read_bands_rasterio.py", "read_bands_rasterio")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    # The exercise's contract: rasterio counts bands from 1, Red is 3 and NIR is 4.
    h.equal(module.RED_BAND_INDEX, 3, "the Red band is index 3, not 2")
    h.equal(module.NIR_BAND_INDEX, 4, "the NIR band is index 4")

    red, nir = module.red_array, module.nir_array
    h.equal(red.shape, (50, 50), "the Red band is 50x50")
    h.equal(nir.shape, red.shape, "both bands have the same shape, so band math is legal")
    h.equal(str(red.dtype), "float32", "the bands are cast to float32 on the way in")
    h.equal(str(nir.dtype), "float32", "the NIR band is float32 too")

    path = module.SCENE_FILE
    h.check(path.exists(), "the four-band scene is on disk under output/")
    with rasterio.open(path) as src:
        h.equal(src.count, 4, "the file really holds four bands")
        h.equal(src.dtypes[0], "uint16", "the file holds 16-bit digital numbers")
        h.equal((src.width, src.height), (50, 50), "the scene is 50x50 pixels")
        h.equal(src.crs.to_epsg(), 4326, "the scene is in WGS 84")
        h.close(src.res[0], 0.02, "one degree across 50 cells is a 0.02 degree cell")
        west, south, east, north = src.bounds
        h.close(west, -10.0, "the west edge is 10 degrees west")
        h.close(south, 40.0, "the south edge is 40 degrees north")
        h.close(east, -9.0, "the east edge is 9 degrees west")
        h.close(north, 41.0, "the north edge is 41 degrees north")

        # The band the exercise warns about: reading index 1 returns Blue.
        band_3 = src.read(3)
        band_1 = src.read(1)
        h.check(not np.array_equal(band_1, band_3),
                "band 1 is not band 3: the 1-based index decides what you get")
        h.check(np.array_equal(red, band_3.astype(np.float32)),
                "the Red array is the file's band 3, unchanged")

        # NIR has to sit well above Red on a vegetated scene, or the index is noise.
        h.check(int(src.read(4).min()) >= 4000 and int(src.read(4).max()) <= 5999,
                "the NIR band stays in the 4000-5999 DN window")

    h.check(1000 <= float(red.min()) and float(red.max()) <= 1999,
            "the Red band stays in the 1000-1999 DN window")
    h.check(float(nir.mean()) > float(red.mean()) + 2000,
            "NIR is several thousand DN above Red on this scene")
    h.check(float(red.mean()) / float(nir.mean()) < 0.5,
            "Red reflects less than half of what NIR does here, as vegetation behaves")

    h.contains(printed, "Red Array Shape: (50, 50)", "the Red shape is printed")
    h.contains(printed, "Aligned for band math: True", "the alignment check is printed")
    h.contains(printed, "Band Count: 4", "the band count is printed")
    h.contains(printed, "Coordinate Reference System (CRS): EPSG:4326",
               "the CRS is printed")
    h.contains(printed, "Geospatial Transform Matrix", "the transform is printed")

    h.write_json("bands_read.json", {
        "scene": "output/image_001.tif",
        "band_indices_1_based": {"red": module.RED_BAND_INDEX,
                                 "nir": module.NIR_BAND_INDEX},
        "shape": list(red.shape),
        "dtype_in_memory": str(red.dtype),
        "scene_profile": {
            "count": 4,
            "dtype": "uint16",
            "crs": "EPSG:4326",
            "cell_size_degrees": 0.02,
            "bounds": [-10.0, 40.0, -9.0, 41.0],
        },
        "red_dn": [float(red.min()), float(red.max())],
        "nir_dn": [float(nir.min()), float(nir.max())],
        "nir_over_red_mean_ratio": float(nir.mean()) / float(red.mean()),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (reading bands with rasterio)", FILES).crash())
