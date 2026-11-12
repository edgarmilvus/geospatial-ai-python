"""Harness for example 1 — the function, the schema and the tool must agree.

The chapter's point is that a model calls the function through the schema, so the
schema's key has to be the function's argument, the description has to be a
description and not a name, and the return value has to be something a model can
read. All three are checked here, plus the centroid arithmetic on a known polygon.
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
    h = Harness("example 1 (tool schema)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_tool_schema.py", "tool_schema")
        # The listing guards its demonstration behind __main__, so importing it
        # defines the tool and prints nothing; the harness makes the call.
        module.main()
    printed = log.getvalue()

    schema = module.CentroidInputSchema
    tool = module.centroid_tool

    h.equal(tool.name, "calculate_geometry_centroid", "the tool is named after the work it does")
    h.equal(list(schema.model_fields), ["wkt_polygon"],
            "the schema exposes the one argument the function takes")
    h.check(schema.model_fields["wkt_polygon"].description.lower().startswith("a polygon"),
            "the field carries a description, not a restatement of its name")
    h.check(len(tool.description) > 40,
            "the tool description is long enough to help a model choose it")

    # A square from -74.02 to -74.01 by 40.71 to 40.72 has its centre at -74.015.
    result = json.loads(tool.invoke({"wkt_polygon": module.TEST_WKT}))
    h.close(result["centroid_x"], -74.015, "the centroid x is the middle of the square", tol=1e-9)
    h.close(result["centroid_y"], 40.715, "the centroid y is the middle of the square", tol=1e-9)
    h.check(result["wkt_output"].startswith("POINT"),
            "the result also carries the centroid as WKT")

    # The error branch returns JSON too, so a caller parses one shape in both cases.
    broken = json.loads(tool.invoke({"wkt_polygon": "not a polygon"}))
    h.contains(broken.get("error", ""), "Failed to calculate centroid",
               "an invalid polygon returns a JSON error, not an exception")

    h.contains(printed, "Schema fields: ['wkt_polygon']",
               "the listing prints the schema it built")
    h.contains(printed, "Centroid X (longitude): -74.015000",
               "the listing prints the centroid it computed")

    h.write_json("tool_schema.json", {
        "tool": tool.name,
        "fields": list(schema.model_fields),
        "centroid": [result["centroid_x"], result["centroid_y"]],
        "wkt_out": result["wkt_output"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (tool schema)", FILES).crash())
