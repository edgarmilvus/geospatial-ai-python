"""Harness for exercise 1 — the tiled dataset, driven tile by tile.

The graded facts are the grid arithmetic (10 000 / 256 is 40 tiles a side, 1 600 in
all), the window (tile 41 starts at 256, 256 and reads 65 536 pixels, not 100 M), the
edge case (tile 1599 is a 16 x 16 read padded back to 256), the normalisation (the
published statistics invert exactly), and the augmentation (image and mask come out
of the same rotation, which is checked by undoing it).
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import numpy as np
    import torch
except ImportError:
    print("skip    exercise 1 (tiled dataset) — pip install -r requirements-ml.txt")
    print("__VERDICT__ 0 0 exercise 1 (tiled dataset)", file=sys.stderr)
    raise SystemExit(0)

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 1 (tiled dataset)", FILES)
    module = load_listing(FILES / "tiled_dataset.py", "tiled_dataset")
    module.main()

    dataset = module.BuildingSegmentationDataset("scene_image.tif", "scene_mask.tif")

    # --- the grid ---
    h.equal(dataset.width, 10_000, "the scene is 10 000 columns wide")
    h.equal(dataset.n_cols, 40, "10 000 / 256 rounds up to 40 tiles across")
    h.equal(dataset.n_rows, 40, "and 40 down")
    h.equal(len(dataset), 1600, "40 x 40 is 1 600 tiles")

    # --- an interior tile: the window, the shapes, the dtype ---
    image, mask = dataset[41]
    h.equal(dataset.last_window, (256, 256, 256, 256),
            "tile 41 starts at column 256 and row 256, a full 256-pixel window")
    h.equal(tuple(image.shape), (3, 256, 256), "the image tile is CHW")
    h.equal(tuple(mask.shape), (1, 256, 256), "the mask tile gains a channel axis")
    h.equal(str(image.dtype), "torch.float32", "the image tile is float32")
    h.equal(str(mask.dtype), "torch.float32", "the mask tile is float32")
    h.equal(sorted(set(float(value) for value in mask.unique())), [0.0, 1.0],
            "the mask holds the two classes")
    h.equal(dataset.last_read_pixels, 256 * 256,
            "one tile costs 65 536 pixels of reading, not the whole scene")

    # --- the augmentation is synchronized ---
    turns = dataset.last_rotation
    h.check(turns in (0, 1, 2, 3), "the tile was rotated by a quarter turn (%d)" % turns)
    # Undo the rotation on both, then compare with the reader at the same window.
    plain_image = np.rot90(image.numpy(), k=-turns, axes=(1, 2)).copy()
    plain_mask = np.rot90(mask.numpy(), k=-turns, axes=(1, 2)).copy()
    with module.mock_rasterio_open("scene_mask.tif") as src:
        expected_mask = src.read(window=module.Window(256, 256, 256, 256))[0]
    h.check(bool(np.array_equal(plain_mask[0], expected_mask)),
            "the label is the mask raster's own values, rotated with the image")
    h.equal(int(plain_mask.sum()), 15000,
            "a full tile holds 15 000 roof pixels: 100 x 150")

    # The image under the label is the bright roof: the two are on the same grid.
    background = plain_mask[0] == 0
    roof_mean = float(plain_image[:, ~background].mean())
    ground_mean = float(plain_image[:, background].mean())
    h.check(roof_mean > ground_mean + 4.0,
            "roof pixels are far brighter than ground after normalisation (%.2f vs %.2f)"
            % (roof_mean, ground_mean))

    # --- normalisation, checked by inverting it ---
    raw = plain_image * np.array(module.STD_STATS)[:, None, None] \
        + np.array(module.MEAN_STATS)[:, None, None]
    with module.mock_rasterio_open("scene_image.tif") as src:
        expected_raw = src.read(window=module.Window(256, 256, 256, 256))
    h.check(bool(np.allclose(raw, expected_raw, atol=1e-5)),
            "tile * std + mean gives the scene's own value back, pixel for pixel")
    h.check(abs(ground_mean) < 0.05,
            "background pixels normalize to a mean of zero (%.3f)" % ground_mean)
    h.check(roof_mean > 5.0,
            "roof pixels sit far above zero, because 0.90 is 5.9 deviations from 0.298")

    # --- the edge tile is padded, not short ---
    edge_image, edge_mask = dataset[1599]
    h.equal(dataset.last_window, (9984, 9984, 16, 16),
            "tile 1599 is the last 16 x 16 corner of the scene")
    h.equal(tuple(edge_image.shape), (3, 256, 256), "the edge tile is padded to 256 x 256")
    h.equal(int(edge_mask[0, 16:, :].sum()) + int(edge_mask[0, :, 16:].sum()), 0,
            "the padding carries no invented label")
    h.check(float(edge_image[:, 16:, :].std()) > 0,
            "the image padding is reflected scene, not a flat zero")

    # --- determinism and the bounds check ---
    again, _ = dataset[41]
    h.check(bool(torch.equal(image, again)),
            "the same index returns the same tile on a second read")
    h.raises(lambda: dataset[1600], IndexError,
             "an index past the grid raises IndexError instead of wrapping")

    h.write_json("tiled_dataset.json", {
        "scene": {"width": dataset.width, "height": dataset.height,
                  "pixels": dataset.width * dataset.height},
        "grid": {"tile_size": dataset.tile_size, "columns": dataset.n_cols,
                 "rows": dataset.n_rows, "tiles": len(dataset)},
        "interior_tile": {"index": 41, "window": list(dataset.last_window),
                          "image_shape": list(image.shape),
                          "mask_shape": list(mask.shape),
                          "roof_pixels": int(plain_mask.sum()),
                          "rotation_degrees": 90 * turns,
                          "pixels_read": dataset.last_read_pixels},
        "edge_tile": {"index": 1599, "window": [9984, 9984, 16, 16],
                      "padded_to": [3, 256, 256]},
        "normalisation": {"mean_stats": module.MEAN_STATS,
                          "std_stats": module.STD_STATS,
                          "background_mean": round(ground_mean, 3),
                          "roof_mean": round(roof_mean, 3)},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (tiled dataset)", FILES).crash())
