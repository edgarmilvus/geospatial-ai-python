"""Harness for exercise 4 — every sparse prompt dictionary, and no KeyError.

The exercise is defensive extraction, so the harness tries all eight subsets of the
three prompt keys: each must return exactly the arguments it has data for, in the
order the predictor expects (positives before negatives, labels aligned), and the
empty dictionary must produce no arguments at all rather than an exception.
"""
import itertools
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402

from harness import Harness, load_listing  # noqa: E402

POSITIVE = [(85, 45)]
NEGATIVE = [(10, 10)]
BOX = [60, 20, 110, 70]


def main():
    h = Harness("exercise 4 (prompt router)", FILES)
    module = load_listing(FILES / "prompt_router.py", "prompt_router")
    measured = module.main()

    # --- the full dictionary ---
    full = module.process_sam_prompts({'positive_points': POSITIVE,
                                       'bounding_box': BOX,
                                       'negative_points': NEGATIVE})
    h.equal(sorted(full), ["box", "point_coords", "point_labels"],
            "all three prompt types become arguments")
    h.equal(full["point_coords"].shape, (2, 2), "two points, two coordinates each")
    h.equal(full["point_labels"].tolist(), [1, 0],
            "the positive point comes first, then the negative one")
    h.equal(str(full["point_labels"].dtype), "int64", "labels are integers, not floats")
    h.equal(full["box"].shape, (4,), "the box is a four-number array")
    h.equal(full["box"].tolist(), [60.0, 20.0, 110.0, 70.0], "and the numbers are the prompt's")

    # --- the sparse dictionary that the exercise opens with ---
    sparse = module.process_sam_prompts({'positive_points': POSITIVE})
    h.equal(sorted(sparse), ["point_coords", "point_labels"],
            "a missing box is left out of the call, not passed as None")
    h.equal(sparse["point_coords"].shape, (1, 2), "one point stays a 1 x 2 array")

    # --- a negative-only dictionary ---
    negative = module.process_sam_prompts({'negative_points': NEGATIVE})
    h.equal(negative["point_labels"].tolist(), [0], "a lone negative point is labelled 0")

    # --- the empty dictionary ---
    empty = module.process_sam_prompts({})
    h.equal(empty, {}, "no keys in, no arguments out, no exception")
    predictor, mode = module.load_predictor(module.build_patch())
    masks, _, _ = predictor.predict(**empty)
    h.check(masks.shape[0] == 1, "an empty argument set still unpacks into predict()")

    # --- every subset of the three keys ---
    keys = ["positive_points", "bounding_box", "negative_points"]
    values = {"positive_points": POSITIVE, "bounding_box": BOX,
              "negative_points": NEGATIVE}
    tried = 0
    for size in range(len(keys) + 1):
        for combination in itertools.combinations(keys, size):
            prompts = {key: values[key] for key in combination}
            args = module.process_sam_prompts(prompts)
            expected = set()
            if "positive_points" in combination or "negative_points" in combination:
                expected |= {"point_coords", "point_labels"}
            if "bounding_box" in combination:
                expected.add("box")
            h.equal(set(args), expected,
                    "the %d-key subset %s yields exactly %s"
                    % (size, combination, sorted(expected)))
            if "point_labels" in args:
                # Positives first, then negatives: the order the labels encode.
                h.equal(int(args["point_labels"].sum()), len(POSITIVE)
                        if "positive_points" in combination else 0,
                        "the label sum counts the positive points only")
            tried += 1
    h.equal(tried, 8, "all eight subsets were exercised")

    # --- a malformed value is refused, not dropped ---
    h.raises(lambda: module.process_sam_prompts({'bounding_box': [10, 10, 200]}),
             ValueError, "a three-number box raises ValueError")
    h.raises(lambda: module.process_sam_prompts({'positive_points': [(1, 2, 3)]}),
             ValueError, "a three-number point raises ValueError")
    h.raises(lambda: module.process_sam_prompts({'positive_points': [(1,)]}),
             ValueError, "a one-number point raises ValueError")

    # --- and the arguments really drive the segmenter ---
    h.equal(measured["results"]["full"]["area"], 900,
            "the full prompt set segments the 900-pixel building")
    h.equal(measured["results"]["sparse"]["area"], 900,
            "the sparse one finds the same building with the point alone")
    h.equal(measured["results"]["negative_only"]["area"], 0,
            "a negative-only prompt segments nothing")
    h.equal(measured["results"]["empty"]["keys"], [],
            "the empty case hands the predictor no arguments at all")

    h.write_json("prompt_router.json", {
        "segmenter": measured["mode"],
        "patch": {"shape": list(measured["image_shape"]), "building_pixels": 900},
        "cases": {name: {"keys": result["keys"], "area": result["area"],
                         "score": round(result["score"], 2)}
                  for name, result in measured["results"].items()},
        "subsets_exercised": tried,
        "refusals": ["box with three numbers", "point with three numbers",
                     "point with one number"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (prompt router)", FILES).crash())
