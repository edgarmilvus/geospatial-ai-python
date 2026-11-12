"""Harness for exercise 1 — the executor tool as the agent's only door.

What is graded is the contract of the door: the frame exists before the model is
called, a plotting snippet produces a file, a snippet that draws nothing is
refused rather than reported as success, and a broken snippet comes back as an
observation with the traceback in it.
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
    h = Harness("exercise 1 (executor tool)", FILES)
    with contextlib.redirect_stdout(io.StringIO()):
        module = load_listing(FILES / "01_executor_tool.py", "executor_tool")

    frame = module.GDF
    h.equal(len(frame), 6, "the tool's frame holds six districts")
    h.contains(list(frame.columns), "density", "density is available to the generated code")
    h.equal(frame.crs.to_epsg(), 4326, "the frame declares its CRS")

    tool = module.geo_pandas_executor
    good = tool.invoke({"code_snippet": "gdf.plot(column='population', legend=True)"})
    h.contains(good, "created successfully", "a plotting snippet succeeds")

    produced = FILES.parent / "output" / "exercise_1_districts.png"
    h.check(produced.exists(), "the successful run wrote a map")
    if produced.exists():
        h.check(produced.stat().st_size > 2_000,
                "the map is a real file (%d bytes)" % produced.stat().st_size)

    silent = tool.invoke({"code_snippet": "total = gdf['population'].sum()"})
    h.contains(silent, "no figure", "a snippet that draws nothing is refused")

    broken = tool.invoke({"code_snippet": "gdf.plot(column='does_not_exist')"})
    h.contains(broken, "Execution failed", "a bad column returns a failure observation")
    h.contains(broken, "Traceback", "the observation carries the traceback the model needs")
    h.contains(broken, "does_not_exist", "the failing name is visible in the observation")

    h.write_json("executor_tool.json", {
        "districts": int(len(frame)),
        "columns": list(frame.columns),
        "map_bytes": produced.stat().st_size if produced.exists() else 0,
        "refused_without_plot": "no figure" in silent,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (executor tool)", FILES).crash())
