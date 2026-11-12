"""Harness for chapter 2, exercise 4 — a queue of reads, not a loop of reads.

The observable the exercise asks for is a list of *tasks*: callables that hold a
function and its argument, defined but not executed. The harness checks that the
list has four partials with one bound argument each, that the argument points at
a tile that exists, and that calling a task produces exactly the tile it names.
"""
import contextlib
import functools
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("chapter 2 exercise 4 (deferred tile reads)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_async_task_list.py", "ch2_tasks")
    printed = log.getvalue()

    import geopandas as gpd

    tasks = module.async_tasks

    h.check(isinstance(tasks, list), "the queue is a list")
    h.equal(len(tasks), 4, "one task per tile")
    h.equal(sum(isinstance(task, functools.partial) for task in tasks), 4,
            "every entry is a partial, so the call is bound but not made")
    h.equal([task.func.__name__ for task in tasks], ["load_single_tile"] * 4,
            "every task points at the tile reader")
    h.equal([len(task.args) for task in tasks], [1, 1, 1, 1],
            "each task has exactly one bound argument")

    # The arguments are the four tiles the listing wrote, in order.
    h.equal([task.args[0].name for task in tasks],
            ["tile_01.geojson", "tile_02.geojson", "tile_03.geojson", "tile_04.geojson"],
            "the queue covers the four tiles")
    h.check(all(task.args[0].exists() for task in tasks),
            "every bound path exists on disk before it is used")

    # Calling a task is the read; the result is the tile it was bound to.
    results = [task() for task in tasks]
    h.check(all(isinstance(result, gpd.GeoDataFrame) for result in results),
            "each task returns a GeoDataFrame when called")
    h.equal([len(result) for result in results], [1, 1, 1, 1],
            "each tile holds one footprint")
    h.equal([int(result["tile_id"].iloc[0]) for result in results], [1, 2, 3, 4],
            "each task read the tile it was bound to")
    h.equal([result.crs.to_epsg() for result in results], [4326, 4326, 4326, 4326],
            "each tile keeps its CRS")

    h.contains(printed, "Type of generated task list: <class 'list'>",
               "the listing prints the type of the queue")
    h.contains(printed, "tasks defined: 4", "the listing counts the defined tasks")
    h.contains(printed, "   all four tasks executed: 4",
               "the listing reports that all four ran")

    h.write_json("async_tasks.json", {
        "task_count": len(tasks),
        "task_type": type(tasks).__name__,
        "bound_arguments": [task.args[0].name for task in tasks],
        "partials": sum(isinstance(task, functools.partial) for task in tasks),
        "tile_ids": [int(result["tile_id"].iloc[0]) for result in results],
        "features_per_tile": [len(result) for result in results],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 exercise 4 (deferred tile reads)", FILES).crash())
