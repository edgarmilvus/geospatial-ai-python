"""Harness for the interactive challenge — the projection selector.

The challenge is a decision table: three goals, three kinds of projection, plus the
"outside the contiguous US" branch that makes the answer location-dependent. The
harness drives every branch, including the one the listing's two test cases never
reach, and checks that an unknown goal is refused rather than guessed.
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
    h = Harness("interactive challenge (projection selector)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_projection_selector.py", "projection_selector")
    printed = log.getvalue()

    recommend = module.recommend_crs

    # Distance: the local UTM zone, derived from the coordinates.
    calls = io.StringIO()
    with contextlib.redirect_stdout(calls):
        chicago = recommend(latitude=41.88, longitude=-87.63, goal="DISTANCE")
        southern = recommend(latitude=-15.78, longitude=-47.93, goal="DISTANCE")
        mapping = recommend(latitude=41.88, longitude=-87.63, goal="MAPPING")
        brazil_area = recommend(latitude=-15.78, longitude=-47.93, goal="AREA")
        us_area = recommend(latitude=41.88, longitude=-87.63, goal="AREA")
        refused = recommend(latitude=41.88, longitude=-87.63, goal="ELEVATION")

    h.equal(chicago, 32616, "Chicago sits in UTM zone 16N")
    h.equal(southern, 32723, "a Brazilian point gets the southern UTM series")
    h.equal(mapping, 3857, "a web map always asks for Web Mercator")
    h.equal(us_area, 5070, "inside the contiguous US, area asks for Conus Albers")
    h.equal(brazil_area, 6933, "outside it, area falls back to the global equal-area")
    h.equal(refused, None, "an unknown goal returns None instead of a guess")
    h.contains(calls.getvalue(), "Error: Invalid goal specified.",
               "the listing reports the refused goal")

    # The goal is case-insensitive, which is the one input-robustness the
    # challenge asks for.
    with contextlib.redirect_stdout(io.StringIO()):
        h.equal(recommend(latitude=41.88, longitude=-87.63, goal="distance"), 32616,
                "a lower-case goal is accepted")

    h.contains(printed, "Recommended EPSG Code: 6933",
               "the listing prints the recommendation for the area test case")
    h.contains(printed, "15.78°S, 47.93°W",
               "the hemisphere letters follow the sign of the coordinate")

    h.write_json("projection_choices.json", {
        "DISTANCE": {"chicago": chicago, "southern_hemisphere": southern},
        "AREA": {"conus": us_area, "global": brazil_area},
        "MAPPING": mapping,
        "unknown": refused,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("interactive challenge (projection selector)", FILES).crash())
