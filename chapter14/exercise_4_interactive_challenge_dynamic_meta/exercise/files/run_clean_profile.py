"""Harness for exercise 4 — the profile filter, checked against the prompt.

The exercise publishes the expected shape of `clean_profile` and the solution
publishes the comprehension. The harness runs both: the result must hold exactly
the six target keys, the two dimensions must be `int` even though the input gives
them as floats, and the dictionary must equal the structure the prompt printed.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 4 (metadata filtering)"
TARGET = ["crs", "transform", "width", "height", "dtype", "count"]


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        solution = load_listing(FILES / "02_clean_profile.py", "clean_profile")
    printed = log.getvalue()
    prompt = load_listing(FILES / "prompt_sketch_exercise_4.py", "profile_prompt")

    clean = solution.clean_profile

    # -- the filter ------------------------------------------------------
    h.equal(sorted(clean), sorted(TARGET), "the result holds exactly the six target keys")
    h.equal(len(clean), 6, "six keys, not seven")
    for dropped in ("driver", "nodata", "is_tiled", "interleave"):
        h.check(dropped not in clean, "%r was filtered out" % dropped)

    # -- the cast --------------------------------------------------------
    h.equal(type(clean["width"]).__name__, "int", "width is a Python int")
    h.equal(type(clean["height"]).__name__, "int", "height is a Python int")
    h.check(isinstance(solution.input_profile["width"], float),
            "the input really did give width as a float")
    h.equal(clean["width"], 1024, "1024.0 becomes 1024")
    h.equal(clean["height"], 1024, "1024.0 becomes 1024")
    h.check(not isinstance(clean["count"], bool), "count is a number, not a bool")

    # -- the values that must not be touched -----------------------------
    h.equal(clean["crs"], "EPSG:32617", "the CRS survives unchanged")
    h.equal(clean["dtype"], "uint16", "the data type survives unchanged")
    h.equal(clean["count"], 4, "the band count survives unchanged")
    h.equal(tuple(clean["transform"]),
            (10.0, 0.0, 500000.0, 0.0, -10.0, 100000.0),
            "the transform survives as the six-coefficient tuple")
    h.equal(solution.TARGET_KEYS, ["crs", "transform", "width", "height", "dtype", "count"],
            "the code's target list is the list the exercise names")

    # -- the prompt's expected result and the code agree ------------------
    h.equal(sorted(prompt.clean_profile), sorted(clean),
            "the prompt's expected structure has the same six keys")
    h.equal(prompt.clean_profile["transform"], clean["transform"],
            "both declare the same transform")
    h.equal(prompt.clean_profile["width"], clean["width"],
            "the prompt's expected width is the value the code produces")
    h.equal({key: clean[key] for key in TARGET},
            {key: prompt.clean_profile[key] for key in TARGET},
            "the produced profile equals the structure the exercise published")

    # -- what the reader sees -------------------------------------------
    for key in TARGET:
        h.contains(printed, "'%s'" % key, "the listing prints %r" % key)
    h.contains(printed, "'width': 1024", "the printed width carries no decimal point")

    h.write_json("clean_profile.json", {
        "keys": list(clean.keys()),
        "width_type": type(clean["width"]).__name__,
        "height_type": type(clean["height"]).__name__,
        "dropped": ["driver", "nodata", "is_tiled", "interleave"],
        "values": {key: (list(value) if isinstance(value, tuple) else value)
                   for key, value in clean.items()},
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
