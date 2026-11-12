"""Harness for exercise 3 — one fourth the pixels, four times the pixel size.

The invariant is the one the exercise calls critical: the coarse grid must cover
the same ground as the fine one. So the bounds are compared with the original, the
origin is compared with the original, and the pixel size is compared with four
times the original — not with itself.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np
import rasterio

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 3 (downsampling)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "downsample_retransform.py", "downsample")
        result = module.main()
    printed = log.getvalue()

    data = result["data"]
    original = result["original_transform"]
    coarse = result["transform"]

    h.equal(result["original_shape"], (720, 960), "the source is 720 rows by 960 columns")
    h.equal(data.shape, (3, 180, 240), "a factor of four leaves 180 by 240 pixels")
    h.equal(str(data.dtype), "uint16", "resampling keeps the source dtype")

    # The pixel size grows by exactly four, and the origin does not move.
    h.close(original.a, 10.0, "the source pixel is 10 m across")
    h.close(coarse.a, 40.0, "the coarse pixel is 40 m across")
    h.close(coarse.a / original.a, 4.0, "the width ratio is exactly four")
    h.close(coarse.e, -40.0, "the coarse pixel is 40 m down")
    h.close(coarse.e / original.e, 4.0, "the height ratio is exactly four")
    h.close(coarse.c, original.c, "the west edge does not move")
    h.close(coarse.f, original.f, "the north edge does not move")

    # Same ground: read both bounds back and compare.
    with rasterio.open(module.SCENE_PATH) as src:
        source_bounds = tuple(float(value) for value in src.bounds)
        source_mean = float(src.read(1).mean())
        source_min = int(src.read(1).min())
        source_max = int(src.read(1).max())
    coarse_bounds = tuple(rasterio.transform.array_bounds(180, 240, coarse))
    h.equal([round(value, 6) for value in coarse_bounds],
            [round(value, 6) for value in source_bounds],
            "the coarse grid covers exactly the source's bounds")

    # Values: a nearest-neighbour subset of the source, so inside its range and
    # near its mean, but with far fewer samples.
    h.check(int(data.min()) >= source_min, "no coarse pixel is below the source's minimum")
    h.check(int(data.max()) <= source_max, "no coarse pixel is above the source's maximum")
    h.check(abs(float(data.mean()) - source_mean) / source_mean < 0.02,
            "the coarse mean stays within 2 % of the source mean")
    h.equal(int(np.prod(data.shape)), int(np.prod((3, 180, 240))),
            "the coarse array holds 129 600 pixels per plane")

    # A second factor shows the transform rule is general, not a hard-coded 40.
    half = module.downsample_and_retransform(module.SCENE_PATH, factor=2)
    h.equal(half["data"].shape, (3, 360, 480), "a factor of two halves both sides")
    h.close(half["transform"].a, 20.0, "a factor of two doubles the pixel size")

    # What the reader sees.
    h.contains(printed, "Resampled data shape (Bands, H, W): (3, 180, 240)",
               "the listing prints the coarse shape")
    h.contains(printed, "Verification successful: Pixel size increased by factor of 4.",
               "the listing prints its own verification")

    h.write_json("downsample.json", {
        "original": {"shape": [720, 960],
                     "transform": [round(float(value), 3) for value in original[:6]]},
        "downsampled": {"shape": list(data.shape),
                        "transform": [round(float(value), 3) for value in coarse[:6]],
                        "ratio": round(coarse.a / original.a, 3)},
        "bounds": [round(value, 3) for value in source_bounds],
        "source_mean": round(source_mean, 3),
        "downsampled_mean": round(float(data.mean()), 3),
        "value_range": [int(data.min()), int(data.max())],
        "factor_two_pixel_size": round(float(half["transform"].a), 3),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (downsampling)", FILES).crash())
