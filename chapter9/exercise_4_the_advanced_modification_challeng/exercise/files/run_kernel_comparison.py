"""Harness for exercise 4 — the same bandwidth, two kernels, two surfaces.

The modification challenge is a claim about support, and support is countable: the
Epanechnikov surface must be exactly zero everywhere the nearest ping is farther than the
bandwidth, and the Gaussian surface must be positive everywhere. Both must still integrate
to one, which is what makes them comparable densities rather than two arbitrary rasters.
Timings are machine-dependent, so they are checked as ranges and reported as a ratio.
"""
import contextlib
import io
import pathlib
import sys
import traceback

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402
import maphtml  # noqa: E402

NAME = "exercise 4 (kernel comparison)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "kernel_comparison.py", "kernels")
        result = module.main()
    printed = log.getvalue()

    h.equal(module.N_POINTS, 3000, "three thousand pings are simulated")
    h.equal(result["raw_rows"], 3150,
            "the feed on disk carries 150 noise rows on top of the 3 000 pings")
    h.equal(result["raw_rows"] - result["points"], 120,
            "120 of those rows are rejected by the same gates as exercise 1")
    h.equal(module.GRID_RESOLUTION, 120, "the grid is 120 by 120")
    h.equal(module.FIXED_BANDWIDTH, 0.008, "both kernels use the same 0.008-degree bandwidth")
    h.check(abs(module.FIXED_BANDWIDTH * 111_320 - 890.6) < 1.0,
            "which is about 890 metres of latitude")
    h.equal(result["points"], 3030,
            "3 030 pings survive: 30 noise rows were numeric strings that parse")

    # Both surfaces are densities: summed over the grid they integrate to one.
    h.check(abs(result["mass_gaussian"] - 1.0) < 0.02,
            "the Gaussian surface integrates to %.3f" % result["mass_gaussian"])
    h.check(abs(result["mass_epanechnikov"] - 1.0) < 0.02,
            "the Epanechnikov surface integrates to %.3f" % result["mass_epanechnikov"])

    # Support. This is the difference the exercise is about, and it is an exact count.
    h.equal(result["zero_cells"]["gaussian"], 0,
            "the Gaussian surface is positive in every cell")
    h.check(result["zero_cells"]["epanechnikov"] > 5000,
            "the Epanechnikov surface is exactly zero in %d cells, because no ping is "
            "within the bandwidth there" % result["zero_cells"]["epanechnikov"])
    h.equal(14400 - result["zero_cells"]["epanechnikov"], result["epanechnikov_points"],
            "and the layer carries only the cells that have support")

    # The two peaks describe the same city: a finite-support kernel sharpens a hotspot, it
    # does not move it.
    gaussian_peak = result["peak"]["gaussian"]
    epanechnikov_peak = result["peak"]["epanechnikov"]
    h.check(abs(gaussian_peak[0] - epanechnikov_peak[0]) < 0.01,
            "both peaks are at the same latitude (%.4f, %.4f)"
            % (gaussian_peak[0], epanechnikov_peak[0]))
    h.check(abs(gaussian_peak[1] - epanechnikov_peak[1]) < 0.01,
            "and the same longitude (%.4f, %.4f)"
            % (gaussian_peak[1], epanechnikov_peak[1]))

    # Timings: ranges, not values, because a laptop is not a benchmark.
    h.check(0 < result["time_gaussian"] < 120,
            "the Gaussian run is timed (%.4f s)" % result["time_gaussian"])
    h.check(0 < result["time_epanechnikov"] < 120,
            "and so is the Epanechnikov run (%.4f s)" % result["time_epanechnikov"])

    # The document.
    saved = FILES.parent / "output" / "kernel_comparison.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.check(abs(centre[0] - module.CENTER_LAT) < 0.02, "centred on the study area")
    h.equal(maphtml.zoom(text), 12, "at zoom 12")

    layers = maphtml.heat_layers(text)
    options = maphtml.heat_layer_options(text)
    h.equal(len(layers), 2, "two heat layers, one per kernel")
    h.equal(len(options), 2, "each with its own options")
    if len(layers) == 2:
        h.equal(len(layers[0]), 14400, "the Gaussian layer draws every cell")
        h.equal(len(layers[1]), result["epanechnikov_points"],
                "the Epanechnikov layer draws only the cells with support")
        h.equal(options[0].get("radius"), options[1].get("radius"),
                "the two layers use the same radius, so the comparison is the kernel")
        gaussian_weights = [point[2] for point in layers[0]]
        h.check(abs(max(gaussian_weights) - 1.0) < 1e-9
                and abs(max(point[2] for point in layers[1]) - 1.0) < 1e-9,
                "both are normalised to their own peak, so the colours describe shape")
        h.equal(options[0].get("gradient"), {"0.4": "green", "0.8": "yellow"},
                "the Gaussian ramp is green to yellow")
        h.equal(options[1].get("gradient"), {"0.4": "purple", "0.8": "pink"},
                "the Epanechnikov ramp is purple to pink")

    overlays = [name for name, _ in maphtml.overlays(text)]
    h.equal(sorted(overlays), ["Epanechnikov KDE", "Gaussian KDE"],
            "the layer control toggles the two kernels")

    h.contains(printed, "Cells with at least one neighbour inside the bandwidth: 14400",
               "the run reports that every cell has a neighbour")
    h.contains(printed, "Gaussian:      peak", "and prints both surfaces' peaks")
    h.contains(printed, "mass 0.999", "and both masses")
    h.contains(printed, "Ratio (Gaussian / Epanechnikov)",
               "and the timing ratio, which is the performance half of the exercise")
    h.contains(printed, "output/kernel_comparison.html",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("kernel_comparison.json", {
        "points": result["points"],
        "bandwidth_degrees": module.FIXED_BANDWIDTH,
        "grid": [module.GRID_RESOLUTION, module.GRID_RESOLUTION],
        "zero_cells": result["zero_cells"],
        "mass": {"gaussian": round(result["mass_gaussian"], 4),
                 "epanechnikov": round(result["mass_epanechnikov"], 4)},
        "peak": {key: [round(value, 4) for value in pair]
                 for key, pair in result["peak"].items()},
        "seconds": {"gaussian": round(result["time_gaussian"], 4),
                    "epanechnikov": round(result["time_epanechnikov"], 4)},
        "ratio": round(result["time_gaussian"] / result["time_epanechnikov"], 2),
        "layer_points": {"gaussian": result["gaussian_points"],
                         "epanechnikov": result["epanechnikov_points"]},
        "bytes": saved.stat().st_size,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
