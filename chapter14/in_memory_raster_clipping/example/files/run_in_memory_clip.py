"""Harness for example 1 — the in-memory clip, checked pixel by pixel.

The listing prints the clipped array and its transform; this harness re-runs the
same `rasterio.mask.mask` call on the objects the listing built, and checks the
things the picture on the page cannot show: which sixteen pixels survived, where
the new transform put them, and how much of the source the `crop=False` variant
fills with NoData.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np
import rasterio
from affine import Affine
from rasterio.mask import mask

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "example 1 (in-memory raster clipping)"
EXPECTED = np.array([[33, 34, 35, 36],
                     [43, 44, 45, 46],
                     [53, 54, 55, 56],
                     [63, 64, 65, 66]], dtype="int16")


def open_source():
    """The 10 x 10 source raster the listing writes into a MemoryFile."""
    memfile = rasterio.io.MemoryFile()
    source = memfile.open(**{
        "driver": "GTiff", "dtype": "int16", "nodata": -9999,
        "width": 10, "height": 10, "count": 1, "crs": "EPSG:4326",
        "transform": Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0),
    })
    return memfile, source


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_in_memory_raster_clipping.py", "in_memory_clip")
    printed = log.getvalue()

    # -- the source the chapter describes -------------------------------
    h.equal(module.synthetic_data.shape, (10, 10), "the synthetic raster is 10 x 10")
    h.equal(int(module.synthetic_data[0, 0]), 0, "the first pixel holds 0")
    h.equal(int(module.synthetic_data[9, 9]), 99, "the last pixel holds 99")
    h.equal(module.NODATA_VALUE, -9999, "NoData is -9999, out of the data's range")

    # -- the clipped array ----------------------------------------------
    clipped = module.clipped_data
    h.equal(clipped.shape, (1, 4, 4), "a 4 x 4 degree ROI yields a (1, 4, 4) array")
    h.check(np.array_equal(clipped[0], EXPECTED),
            "the clip kept rows 3-6 and columns 3-6 of the source")
    h.equal(int((clipped[0] == module.NODATA_VALUE).sum()), 0,
            "a square ROI leaves no NoData inside the window")

    transform = module.clipped_transform
    h.close(transform.a, 1.0, "the clipped pixel keeps its 1 degree width")
    h.close(transform.e, -1.0, "the clipped pixel keeps its negative 1 degree height")
    h.close(transform.c, 3.0, "the clipped origin moved to the ROI's west edge")
    h.close(transform.f, 7.0, "the clipped origin moved to the ROI's north edge")
    h.close(transform.b, 0.0, "no rotation is introduced by the clip")
    h.close(transform.d, 0.0, "no skew is introduced by the clip")

    bounds = rasterio.transform.array_bounds(4, 4, transform)
    h.equal(tuple(round(value, 6) for value in bounds), (3.0, 3.0, 7.0, 7.0),
            "the clipped bounds are the polygon's own bounds")
    ring = module.roi_geometry[0]["coordinates"][0]
    h.equal([tuple(point) for point in ring],
            [(3.0, 3.0), (7.0, 3.0), (7.0, 7.0), (3.0, 7.0), (3.0, 3.0)],
            "the ROI the listing defines is the closed 3..7 square")

    # -- the same operation without cropping -----------------------------
    memfile, source = open_source()
    with source as src:
        src.write(module.synthetic_data, 1)
        full, full_transform = mask(src, module.roi_geometry, crop=False,
                                    all_touched=False, nodata=-9999)
    memfile.close()
    h.equal(full.shape, (1, 10, 10), "crop=False keeps the source's 10 x 10 window")
    h.equal(int((full[0] == -9999).sum()), 84,
            "84 of the 100 pixels are outside the 4 x 4 ROI")
    h.check(np.array_equal(full[0][3:7, 3:7], EXPECTED),
            "the 16 pixels inside the ROI are the same 16 as with crop=True")

    # -- a shape that is not a rectangle, so the mask really masks --------
    triangle = [{"type": "Polygon",
                 "coordinates": [[(3.0, 3.0), (7.0, 3.0), (3.0, 7.0), (3.0, 3.0)]]}]
    memfile, source = open_source()
    with source as src:
        src.write(module.synthetic_data, 1)
        tri, _ = mask(src, triangle, crop=True, all_touched=False, nodata=-9999)
    memfile.close()
    h.equal(tri.shape, (1, 4, 4), "the triangle is still clipped to its bounding box")
    h.equal(int((tri[0] != -9999).sum()), 10,
            "ten of the sixteen pixel centres fall inside or on the triangle")
    h.equal(int((tri[0] == -9999).sum()), 6,
            "the six centres outside the triangle carry the NoData value")
    h.equal(int(tri[0][0, 0]), 33, "the triangle keeps the corner it covers")
    h.equal(int(tri[0][0, 1]), -9999, "and fills the rest of that row with NoData")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Original Data Shape (H, W): (10, 10)",
               "the listing prints the source shape")
    h.contains(printed, "Clipped Data Shape (Bands, H, W): (1, 4, 4)",
               "the listing prints the clipped shape")
    h.contains(printed, "[[33 34 35 36]", "the listing prints the first clipped row")

    h.write_json("in_memory_clip.json", {
        "source_shape": list(module.synthetic_data.shape),
        "roi_bounds": [3.0, 3.0, 7.0, 7.0],
        "clipped_shape": list(clipped.shape),
        "clipped_values": clipped[0].tolist(),
        "transform": [transform.a, transform.b, transform.c,
                      transform.d, transform.e, transform.f],
        "clipped_bounds": [round(value, 6) for value in bounds],
        "nodata_inside_square": 0,
        "nodata_crop_false": int((full[0] == -9999).sum()),
        "triangle_pixels_kept": int((tri[0] != -9999).sum()),
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
