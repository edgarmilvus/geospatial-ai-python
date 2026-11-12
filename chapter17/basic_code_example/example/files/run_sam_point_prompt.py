"""Harness for example 1 — a point prompt, from coordinates to a mask.

With the stand-in, the numbers are exact: the 30 x 40 building is 1 200 pixels, the
mask's bounding box is rows 50-80 and columns 100-140, and a prompt given in the
wrong order selects nothing. With the real package and weights installed the numbers
move, so the exactness is asserted only for the stand-in and the interface is
asserted for both.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 1 (SAM point prompt)", FILES)
    module = load_listing(FILES / "sam_point_prompt.py", "sam_point_prompt")
    measured = module.main()

    image = measured["image"]
    h.equal(image.shape, (256, 256, 3), "the patch is 256 x 256 RGB")
    h.equal(str(image.dtype), "uint8", "the patch is 8-bit, the only input SAM accepts")

    # --- the interface both the stand-in and the real model share ---
    h.equal(measured["masks_shape"], (3, 256, 256),
            "multimask_output returns three masks at the image's resolution")
    h.equal(measured["logits_shape"], (3, 64, 64),
            "the logits are the decoder's coarse 64 x 64 output")
    scores = measured["scores"]
    h.equal(len(scores), 3, "one score per mask")
    h.check(all(0.0 < value < 1.0 for value in scores),
            "every score is a confidence in (0, 1)")
    h.check(scores[0] > scores[1] > scores[2], "the masks come back best first")
    h.equal(measured["best_index"], 0, "argmax picks the first, highest-scoring mask")
    h.close(measured["best_score"], scores[0], "the chosen score is the maximum")
    h.check(measured["prompt_inside"], "the prompted pixel is inside the returned mask")

    stand_in = measured["mode"] == "stand-in"

    # --- the prompt was read as (x, y) ---
    predictor = measured["predictor"]
    # Same patch, the prompt swapped into (row, column) order: x=65, y=120 is bare
    # ground, so a predictor that swapped the axes would still return the building.
    swapped, swapped_scores, _ = predictor.predict(
        point_coords=np.array([[65, 120]]), point_labels=np.array([1]),
        multimask_output=True)
    h.equal(int(swapped[0].sum()), 0,
            "a prompt at (x=65, y=120) is background, so nothing is segmented")
    h.check(float(swapped_scores[0]) < 0.5, "an empty prediction carries a low score")

    # --- the object, when segmentation is the stand-in ---
    if stand_in:
        best = predictor.predict(point_coords=np.array([[120, 65]]),
                                 point_labels=np.array([1]),
                                 multimask_output=True)[0][0]
        h.equal(int(best.sum()), 1200, "30 rows by 40 columns is 1 200 pixels")
        rows = np.where(best.any(axis=1))[0]
        cols = np.where(best.any(axis=0))[0]
        h.equal((int(rows.min()), int(rows.max())), (50, 79),
                "the mask starts at row 50 and ends at row 79")
        h.equal((int(cols.min()), int(cols.max())), (100, 139),
                "the mask starts at column 100 and ends at column 139")
        h.equal(int(best[50:80, 100:140].sum()), 1200,
                "every segmented pixel is inside the building rectangle")
        h.check(not best[49, 120] and not best[80, 120],
                "the rows just outside the roof are background")
        h.check(not best[65, 99] and not best[65, 140],
                "the columns just outside the roof are background")

    # --- single-mask mode and a negative prompt ---
    single, single_scores, single_logits = predictor.predict(
        point_coords=np.array([[120, 65]]), point_labels=np.array([1]),
        multimask_output=False)
    h.equal(tuple(single.shape), (1, 256, 256),
            "multimask_output=False returns exactly one mask")
    h.equal(tuple(single_logits.shape), (1, 64, 64), "and one logit map")
    h.equal(len(single_scores), 1, "and one score")

    negative = predictor.predict(point_coords=np.array([[120, 65]]),
                                 point_labels=np.array([0]))[0]
    h.equal(int(negative[0].sum()), 0,
            "a label of 0 says 'not this object', so no mask is returned")

    # --- the errors a caller will make ---
    h.raises(lambda: module.ThresholdSamPredictor().predict(
        point_coords=np.array([[1, 1]])), RuntimeError,
        "predict before set_image raises instead of guessing the image size")
    h.raises(lambda: module.ThresholdSamPredictor().set_image(
        np.zeros((32, 32), dtype=np.uint8)), ValueError,
        "a two-dimensional image is refused with its own message")

    h.write_json("sam_point_prompt.json", {
        "segmenter": measured["mode"],
        "optional_dependency": "segment_anything (pip install git+https://github.com/"
                               "facebookresearch/segment-anything.git)",
        "image": {"shape": list(measured["image_shape"]), "dtype": "uint8",
                  "building": {"rows": [50, 80], "cols": [100, 140]}},
        "prompt": {"point": [120, 65], "order": "x, y", "label": 1},
        "output": {"masks": list(measured["masks_shape"]),
                   "logits": list(measured["logits_shape"]),
                   "scores": [round(value, 2) for value in scores],
                   "best_index": measured["best_index"],
                   "segmented_pixels": measured["segmented_pixels"]},
        "swapped_prompt_pixels": int(swapped[0].sum()),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (SAM point prompt)", FILES).crash())
