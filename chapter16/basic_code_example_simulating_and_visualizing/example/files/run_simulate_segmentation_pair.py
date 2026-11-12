"""Harness for example 1 — the simulated image/mask pair and its tensor form.

The pair is what a segmentation model is fed, so the checks are about the grid: the
mask is on the image's grid, the roof is painted under the label, brightness alone
does not define the class, and the HWC -> CHW transpose moves axes without moving
pixels.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import numpy as np
    import torch
except ImportError:  # the deep-learning stack is an optional extra
    print("skip    example 1 (segmentation data pair) — "
          "pip install -r requirements-ml.txt")
    print("__VERDICT__ 0 0 example 1 (segmentation data pair)", file=sys.stderr)
    raise SystemExit(0)

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 1 (segmentation data pair)", FILES)
    module = load_listing(FILES / "simulate_segmentation_pair.py",
                          "simulate_segmentation_pair")
    image, mask = module.build_pair()
    measured = module.main()

    # --- the array a raster reader hands over: HWC, 8-bit ---
    h.equal(image.shape, (128, 128, 3), "the image is 128 x 128 with three channels")
    h.equal(str(image.dtype), "uint8", "the image is 8-bit, as imagery is stored")
    h.equal(mask.shape, (128, 128), "the mask carries one label per pixel, no channel")
    h.equal(str(mask.dtype), "uint8", "the mask is integer class indices")
    h.equal(sorted(np.unique(mask).tolist()), [0, 1], "the mask has exactly two classes")
    h.equal(int(mask.sum()), 900, "30 rows by 30 columns of building: 900 pixels")

    # --- the pair is spatially consistent ---
    roof = float(image[mask == 1].mean())
    background = float(image[mask == 0].mean())
    h.check(roof > background + 50,
            "the roof is at least 50 DN brighter than the background (%.1f vs %.1f)"
            % (roof, background))

    # Brightness alone is not the class: the road in the middle is at 255 and unlabelled.
    h.equal(int(image[64, 64, 0]), 255, "the road patch is painted at full intensity")
    h.equal(int(mask[64, 64]), 0, "the road is background, not a building")
    h.check(image[50, 50, 0] < 190, "the pixel outside the road and the roof is not roof-bright")

    # The label covers exactly the slice the simulation names.
    h.equal(int(mask[30:60, 80:110].sum()), 900, "every labelled pixel is inside the footprint")
    h.equal(int(mask[0:30, :].sum()), 0, "nothing above the footprint is labelled")

    # --- the tensor form ---
    image_tensor, mask_tensor = module.to_tensors(image, mask)
    h.equal(tuple(image_tensor.shape), (3, 128, 128), "the image tensor is CHW")
    h.equal(tuple(mask_tensor.shape), (1, 128, 128), "the mask tensor gains a channel axis")
    h.equal(str(image_tensor.dtype), "torch.float32", "the image tensor is float32")
    h.close(float(image_tensor.max()), 1.0, "dividing by 255 keeps the top at 1.0")
    h.check(float(image_tensor.min()) >= 0.0, "no pixel is negative after the division")
    h.equal(sorted(set(mask_tensor.unique().tolist())), [0.0, 1.0],
            "the mask tensor still holds the two classes")

    # The transpose moves axes, not pixels: channel 0 at (10, 100) is the red band there.
    red_at = float(image_tensor[0, 10, 100])
    h.close(red_at * 255.0, float(image[10, 100, 0]), "the transpose preserves the pixel", tol=0.01)

    # --- what the run printed and wrote ---
    h.equal(measured["building_pixels"], 900, "the listing reports the 900 building pixels")
    h.equal(measured["tensor_shape"], (3, 128, 128), "the listing reports the CHW shape")
    figure = module.OUTPUT_DIR / measured["figure"]
    h.check(figure.exists() and figure.stat().st_size > 10_000,
            "the figure is written to output/ and is not empty")

    h.write_json("segmentation_pair.json", {
        "image_shape": list(measured["image_shape"]),
        "mask_shape": list(measured["mask_shape"]),
        "classes": sorted(np.unique(mask).tolist()),
        "building_pixels": measured["building_pixels"],
        "building_fraction": round(measured["building_pixels"] / mask.size, 4),
        "roof_mean": round(roof, 1),
        "background_mean": round(background, 1),
        "tensor_shape": list(measured["tensor_shape"]),
        "figure": measured["figure"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (segmentation data pair)", FILES).crash())
