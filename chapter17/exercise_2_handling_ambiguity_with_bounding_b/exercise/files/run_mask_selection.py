"""Harness for exercise 2 — one box, three hypotheses, and the rule that chooses.

The three areas are the point: 10 537, 10 881 and 13 589 pixels for the same prompt.
The confidence rule picks the first; the area floor at 12 000 disqualifies it and the
box-filling hypothesis wins instead. Then closing fills exactly the twelve one-pixel
dropouts the segmenter left, and nothing else.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402
import scipy.ndimage as ndimage  # noqa: E402

from harness import Harness, load_listing  # noqa: E402

# From this session's run: the three hypotheses for one box prompt.
EXPECTED_AREAS = [10537, 10881, 14061]
EXPECTED_SCORES = [0.94, 0.86, 0.72]


def main():
    h = Harness("exercise 2 (mask selection)", FILES)
    module = load_listing(FILES / "mask_selection.py", "mask_selection")
    measured = module.main()

    image, truth = module.build_patch()
    h.equal(image.shape, (256, 256, 3), "the patch is 256 x 256 RGB")
    h.equal(int(truth.sum()), 11209, "the land cover truth is an 11 209-pixel ellipse")

    # --- three hypotheses, three areas, three scores ---
    candidates = measured["candidates"]
    h.equal(len(candidates), 3, "one box prompt returns three hypotheses")
    h.equal([area for _, area in candidates], EXPECTED_AREAS,
            "the three hypotheses differ in area: tight, dilated, box-filled")
    h.check([round(score, 2) for score, _ in candidates] == EXPECTED_SCORES,
            "the scores come back in descending order")
    h.check(all(candidates[i][1] < candidates[i + 1][1] for i in range(2)),
            "each hypothesis is larger than the one ranked above it")

    # The three masks are nested: that is what makes the choice a scale choice.
    predictor, _ = module.load_predictor(image)
    masks, scores, _ = predictor.predict(box=np.array(module.BOX, dtype=np.float64),
                                         multimask_output=True)
    h.check(bool((masks[1] >= masks[0]).all() and (masks[2] >= masks[1]).all()),
            "the hypotheses are nested: tight inside dilated inside the box")

    # --- the confidence rule and the area floor ---
    tight = module.select_best_mask(module.to_candidates(masks, scores),
                                    module.MIN_AREA_THRESHOLD)
    h.equal(int(tight.sum()), 10537, "a 6 000-pixel floor keeps the most confident mask")

    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        large = module.select_best_mask(module.to_candidates(masks, scores), 12_000)
    h.equal(int(large.sum()), 14061,
            "a 12 000-pixel floor disqualifies the tight mask and picks the box")
    h.contains(log.getvalue(), "eligible: [14061]", "the run says which masks qualified")

    with contextlib.redirect_stdout(log):
        fallback = module.select_best_mask(module.to_candidates(masks, scores), 20_000)
    h.contains(log.getvalue(), "no mask reached 20000",
               "a floor nothing reaches is announced, not silently ignored")
    h.equal(int(fallback.sum()), 10537,
            "the fallback is still the most confident hypothesis, not the largest")

    # --- refinement ---
    h.equal(measured["selected_area"], 10537, "the selected mask is 10 537 pixels")
    h.equal(measured["refined_area"], 10549,
            "closing filled the twelve one-pixel dropouts, 10 537 -> 10 549")
    h.equal(measured["refined_area"] - measured["selected_area"], len(module.HOLES),
            "exactly one pixel per dropout, no more")
    h.check(bool((measured["refined"] >= measured["selected"]).all()),
            "closing only adds: the refined mask contains the raw one")
    h.check(int(ndimage.label(measured["refined"])[1]) == 1,
            "the refined mask is still a single object")
    h.check(bool(np.array_equal(ndimage.binary_fill_holes(measured["refined"]),
                                measured["refined"])),
            "after closing there is no hole left to fill")

    # --- against the truth ---
    h.check(0.90 < measured["iou"] < 1.0,
            "the refined mask overlaps the land cover at IoU %.4f, not perfectly"
            % measured["iou"])
    box = masks[2]
    h.check(bool((measured["refined"] & ~box).sum() == 0),
            "no refined pixel escapes the prompt box")

    # --- the artefact ---
    saved = np.load(module.OUTPUT_DIR / measured["mask_file"])
    h.equal(saved.shape, (256, 256), "the selected mask is written as one array")
    h.equal(str(saved.dtype), "bool", "and stays boolean")
    h.check(bool(np.array_equal(saved, measured["refined"])),
            "the file on disk is the refined mask, ready to plot")

    h.write_json("mask_selection.json", {
        "segmenter": measured["mode"],
        "patch": {"shape": list(measured["image_shape"]),
                  "truth_pixels": measured["truth_pixels"],
                  "box": module.BOX},
        "hypotheses": [{"rank": index, "score": round(score, 2), "area_px": area}
                       for index, (score, area) in enumerate(candidates)],
        "selection": {"floor_6000_px": 10537, "floor_12000_px": 14061,
                      "fallback_floor_20000_px": 10537},
        "refinement": {"selected_px": measured["selected_area"],
                       "refined_px": measured["refined_area"],
                       "filled_px": measured["refined_area"] - measured["selected_area"]},
        "iou_against_truth": round(measured["iou"], 4),
        "mask_file": measured["mask_file"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (mask selection)", FILES).crash())
