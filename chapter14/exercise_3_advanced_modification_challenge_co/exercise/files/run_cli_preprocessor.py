"""Harness for exercise 3 — the clip behind a command line.

The exercise is about the three argument paths, so the harness takes all three:
no arguments (the demo the listing runs for a reader), two arguments (the usage
message, exit 1) and a path that does not exist (the FileNotFoundError branch,
exit 1). It then checks the raster the successful run wrote.
"""
import contextlib
import io
import pathlib
import subprocess
import sys

import numpy as np
import rasterio

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 3 (command-line preprocessor)"
LISTING = FILES / "01_cli_preprocessor.py"
OUTPUT = FILES.parent / "output"


def run(*args):
    return subprocess.run([sys.executable, str(LISTING), *args],
                          cwd=str(FILES), capture_output=True, text=True)


def main():
    h = Harness(NAME, FILES)
    module = load_listing(LISTING, "cli_preprocessor")

    # -- the parse function on its own -----------------------------------
    with contextlib.redirect_stdout(io.StringIO()):
        parsed = module.parse_cli_args(["script.py", "in.tif", "mask.geojson", "out.tif"])
    h.equal(parsed, ("in.tif", "mask.geojson", "out.tif"),
            "three positional arguments are returned in order")

    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        h.raises(lambda: module.parse_cli_args(["script.py", "in.tif", "mask.geojson"]),
                 SystemExit, "two arguments end the run with SystemExit")
    usage = log.getvalue()
    h.contains(usage, "Error: Expected 3 arguments, received 2.",
               "the usage message counts what it received")
    h.contains(usage, "Usage: python script_name.py <input_raster_path>", "it prints the usage")

    # -- the three paths through __main__ ---------------------------------
    demo = run()
    h.equal(demo.returncode, 0, "no arguments runs the demo and exits 0")
    h.contains(demo.stdout, "No arguments given", "the demo branch says what it is doing")
    h.contains(demo.stdout, "SUCCESS: Raster clipped", "the demo clip reports success")

    too_few = run("only_one.tif", "only_two.geojson")
    h.equal(too_few.returncode, 1, "two arguments exit 1")
    h.contains(too_few.stdout, "Error: Expected 3 arguments, received 2.",
               "the usage message is what a reader sees")

    missing = run("/nonexistent/input.tif", "/nonexistent/mask.geojson",
                  str(OUTPUT / "never_written.tif"))
    h.equal(missing.returncode, 1, "a missing input exits 1")
    h.contains(missing.stdout, "FATAL ERROR: Input file missing.",
               "the FileNotFoundError branch names the problem")
    h.contains(missing.stdout, "Input raster not found", "and names the file")
    h.check(not (OUTPUT / "never_written.tif").exists(),
            "the failing run wrote no raster")

    # -- the raster the demo produced -------------------------------------
    clipped_path = OUTPUT / "utility_clipped.tif"
    h.check(clipped_path.is_file(), "the demo wrote a clipped raster")
    with rasterio.open(OUTPUT / "utility_input.tif") as src:
        source = src.read(1)
        h.equal((src.width, src.height), (200, 200), "the source is 200 x 200 pixels")
    with rasterio.open(clipped_path) as clipped:
        data = clipped.read(1)
        bounds = clipped.bounds
        h.equal((clipped.width, clipped.height), (80, 80),
                "the 4-degree ROI at 0.05 degrees/px is 80 x 80 pixels")
        h.equal(tuple(round(value, 6) for value in bounds), (2.0, 2.0, 6.0, 6.0),
                "the clipped raster sits on the mask")
        h.equal(clipped.nodata, -9999, "the NoData value travelled through the profile")
        h.equal(clipped.crs.to_string(), "EPSG:4326", "the clip keeps WGS 84")
    h.equal(int(data[0, 0]), int(source[80, 40]),
            "the first clipped pixel is the source pixel at (row 80, col 40)")
    h.equal(int((data == -9999).sum()), 0, "a rectangular ROI leaves no NoData")

    h.write_json("cli_preprocessor.json", {
        "usage_exit_code": too_few.returncode,
        "missing_file_exit_code": missing.returncode,
        "demo_exit_code": demo.returncode,
        "source": {"width": 200, "height": 200, "degrees_per_pixel": 0.05},
        "output": {"width": 80, "height": 80,
                   "bounds": [round(value, 2) for value in
                              (bounds.left, bounds.bottom, bounds.right, bounds.top)],
                   "nodata": -9999,
                   "first_pixel": int(data[0, 0])},
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
