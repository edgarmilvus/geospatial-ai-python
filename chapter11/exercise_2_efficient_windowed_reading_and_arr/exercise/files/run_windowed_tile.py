"""Harness for exercise 2 — the centred window and the boundary refusal.

The window is arithmetic: (800 - 512) // 2 = 144 columns in and (600 - 512) // 2 =
44 rows down. The harness re-reads those pixels from the same file and compares
them, then asks for a 700-pixel tile that cannot fit and expects `None`.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np
import rasterio
from rasterio.windows import Window

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 2 (windowed tile)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "windowed_tile_read.py", "windowed_tile")
        tile, too_big = module.main()
    printed = log.getvalue()

    data = tile["data"]
    h.equal(data.shape, (3, 512, 512), "the tile arrives as three 512x512 planes")
    h.equal(str(data.dtype), "float32", "the tile is cast to float32 for the model")
    h.equal(tile["source_dtype"], "uint16", "the source stays uint16")
    h.equal(tile["source_count"], 4, "the source has a fourth band that is not read")
    h.equal(int(tile["window"].col_off), 144, "the window starts 144 columns in")
    h.equal(int(tile["window"].row_off), 44, "the window starts 44 rows down")
    h.equal(int(tile["window"].width), 512, "the window is 512 columns wide")
    h.equal(int(tile["window"].height), 512, "the window is 512 rows high")

    with rasterio.open(module.SCENE_PATH) as src:
        expected = src.read(indexes=(1, 2, 3),
                            window=Window(144, 44, 512, 512)).astype(np.float32)
        h.check(np.array_equal(data, expected),
                "the tile is exactly bands 1-3 under the centred window")
        h.equal(src.width, 800, "the scene is 800 columns wide")
        h.equal(src.height, 600, "the scene is 600 rows high")
        h.equal(src.count, 4, "the scene carries four bands")

    # The window's transform: origin shifted by 144 x 20 m and 44 x 20 m.
    transform = tile["transform"]
    h.close(transform.c, 402880.0, "the tile's west edge is 2 880 m east")
    h.close(transform.f, 4599120.0, "the tile's north edge is 880 m down")
    h.close(transform.a, 20.0, "the tile keeps the 20 m pixel size")

    # The cast really is a cast: the values are not rescaled.
    h.close(float(data.max()), float(expected.max()),
            "casting leaves the largest value alone", tol=0.5)
    h.close(float(data.min()), float(expected.min()),
            "casting leaves the smallest value alone", tol=0.5)
    h.check(float(data.min()) >= 200 and float(data.max()) < 1200,
            "the tile's values stay inside the generator's range")

    # The boundary: 700 > 600, so the function refuses and says why.
    h.equal(too_big, None, "a tile larger than the image returns None")
    h.contains(printed, "are too small for the requested tile size (700)",
               "the refusal names the requested size")
    h.contains(printed, "Resulting NumPy array shape (Bands, H, W): (3, 512, 512)",
               "the listing prints the tile shape")

    h.write_json("windowed_tile.json", {
        "scene": {"width": 800, "height": 600, "bands": 4, "dtype": "uint16"},
        "window": {"col_off": 144, "row_off": 44, "width": 512, "height": 512},
        "tile": {"shape": list(data.shape), "dtype": str(data.dtype),
                 "min": float(data.min()), "max": float(data.max())},
        "tile_transform": [round(float(value), 3) for value in transform[:6]],
        "boundary_refused": too_big is None,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (windowed tile)", FILES).crash())
