"""Harness for chapter 20, exercise 1 — the three ways out of a file operation.

A context-manager exercise is graded on the paths that are not the happy one: the
missing input, the corrupt input, and the boundary of the filter. The assertions
below check all three, plus the fact that the output file is only written when the
read succeeded.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 1 (GeoJSON subsetter)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_geojson_subsetter.py", "geojson_subsetter")
        count = module.main()
    printed = log.getvalue()

    subset = FILES.parent / "output" / "subset.geojson"
    written = json.loads(subset.read_text())

    h.equal(count, 3, "three of the four features fall inside the bounding box")
    h.equal(len(written["features"]), 3, "the output file holds exactly those three")
    h.equal(written["type"], "FeatureCollection", "the output is a FeatureCollection")
    names = [feature["properties"]["name"] for feature in written["features"]]
    h.check(all("inside" in name or "edge" in name for name in names),
            "the far-away feature was filtered out")
    h.check("on the edge" in names,
            "a point exactly on maxx/maxy is inside, not outside: the bounds are inclusive")
    h.equal(written["features"][0]["properties"]["id"], 1,
            "the surviving features keep their properties, not just their geometry")

    # --- the missing file ---
    missing = module.safe_geojson_subsetter(
        str(module.MISSING_FILE), str(FILES.parent / "output" / "error.geojson"),
        module.BARRIER_BBOX)
    h.equal(missing, 0, "a missing input returns zero rather than raising")
    h.check(not (FILES.parent / "output" / "error.geojson").exists(),
            "no output file is created when the input is missing")

    # --- the corrupt file ---
    def corrupt():
        return module.safe_geojson_subsetter(
            str(module.CORRUPT_FILE), str(FILES.parent / "output" / "error.geojson"),
            module.BARRIER_BBOX)

    h.raises(corrupt, module.DataProcessingError,
             "a corrupt file raises the custom exception, not json.JSONDecodeError")
    h.check(not (FILES.parent / "output" / "error.geojson").exists(),
            "no output file is created when the content cannot be parsed")
    h.check(issubclass(module.DataProcessingError, Exception),
            "DataProcessingError is an Exception subclass the caller can catch")

    # --- the same call twice must not append ---
    with contextlib.redirect_stdout(io.StringIO()):
        module.safe_geojson_subsetter(str(module.INPUT_FILE), str(subset),
                                      module.BARRIER_BBOX)
    again = json.loads(subset.read_text())
    h.equal(len(again["features"]), 3,
            "re-running rewrites the file instead of appending to it")

    # --- an empty result is still a valid FeatureCollection ---
    empty_path = FILES.parent / "output" / "empty.geojson"
    with contextlib.redirect_stdout(io.StringIO()):
        empty = module.safe_geojson_subsetter(str(module.INPUT_FILE), str(empty_path),
                                              (50.0, 50.0, 60.0, 60.0))
    h.equal(empty, 0, "a bounding box over the ocean keeps nothing")
    h.equal(json.loads(empty_path.read_text())["features"], [],
            "the empty result is written as an empty feature list, not as null")

    # --- what the reader sees ---
    h.contains(printed, "wrote 3 of 4 features", "the run reports the kept count")
    h.contains(printed, "[Test 2 Handled] returned 0", "the run reports the missing-file path")
    h.contains(printed, "[Test 3 Handled] DataProcessingError",
               "the run reports the corrupt-file path")

    h.write_json("geojson_subsetter.json", {
        "kept": count,
        "total_features": 4,
        "kept_names": names,
        "missing_returned": missing,
        "corrupt_raises": "DataProcessingError",
        "empty_result": empty,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (GeoJSON subsetter)", FILES).crash())
