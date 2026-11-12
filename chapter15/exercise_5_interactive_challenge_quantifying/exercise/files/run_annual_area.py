"""Harness for exercise 5 — hectares per year, and the plot that shows them.

The exercise's arithmetic is fixed: one pixel is 100 m2, so 100 pixels are one
hectare and the 500 x 500 scene is 2 500 hectares. The harness checks the three
annual totals against the 1 %, 2 % and 3 % the simulation draws, checks that the
cumulative line is the running sum, and checks that the figure reached disk and
was closed rather than left to a window.
"""
import contextlib
import io
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")

import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 5 (annual deforestation area)"
OUTPUT = FILES.parent / "output"
RATES = [0.01, 0.02, 0.03]


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "02_annual_area_plot.py", "annual_area")
    printed = log.getvalue()

    stack = module.annual_deforestation_stack
    years = module.years

    # -- the stack --------------------------------------------------------
    h.equal(tuple(stack.dims), ("time", "y", "x"), "one boolean map per year")
    h.equal(stack.shape, (3, 500, 500), "three years of a 500 x 500 scene")
    h.equal(years, [2020, 2021, 2022], "the years are 2020, 2021 and 2022")
    h.equal(int(stack.size), 750000, "three maps of 250 000 pixels")
    h.equal(stack.dtype, np.dtype("bool"), "the maps are boolean, not counts")

    # -- the conversion ----------------------------------------------------
    one_hectare = np.ones((10, 10), dtype=bool)
    h.close(module.calculate_area_hectares(one_hectare), 1.0,
            "one hundred 10 m pixels are exactly one hectare")
    h.close(module.calculate_area_hectares(np.zeros((10, 10), dtype=bool)), 0.0,
            "an empty map is zero hectares")

    # -- the annual totals -------------------------------------------------
    annual = module.annual_loss
    cumulative = module.cumulative_loss
    h.equal(len(annual), 3, "one total per year")

    for index, rate in enumerate(RATES):
        count = int(stack.isel(time=index).sum())
        h.close(annual[index], count * 100 / 10000,
                "%d's total is its pixel count times 100 m2 over 10 000" % years[index],
                tol=1e-12)
        h.check(abs(annual[index] - rate * 2500) <= 3.0,
                "%d is about the %d %% the simulation draws (%.2f ha)"
                % (years[index], rate * 100, annual[index]))

    h.check(annual[0] < annual[1] < annual[2],
            "loss grows year on year, as the three draws ask")
    h.check(np.allclose(cumulative, np.cumsum(annual)),
            "the cumulative line is the running sum of the three totals")
    h.close(cumulative[-1], sum(annual), "the last point is the four-year total")
    h.check(140.0 <= cumulative[-1] <= 165.0,
            "roughly 150 hectares are lost across the three years (%.2f)"
            % cumulative[-1])

    # -- the figure --------------------------------------------------------
    png = OUTPUT / "annual_deforestation.png"
    h.check(png.is_file(), "the plot was written to output/")
    if png.is_file():
        h.check(png.stat().st_size > 10000,
                "the PNG carries a real figure, not an empty canvas (%d bytes)"
                % png.stat().st_size)
    h.equal(plt.get_fignums(), [], "the plotting function closed its figure")

    # -- what the reader sees -------------------------------------------
    for index, year in enumerate(years):
        h.contains(printed, "Deforestation detected in %d: %.2f Hectares"
                   % (year, annual[index]),
                   "the listing prints %d's total" % year)
    h.contains(printed, "Cumulative loss after 2022: %.2f Hectares" % cumulative[-1],
               "the listing prints the cumulative total")
    h.contains(printed, "Total pixels analysed: 250000",
               "the listing states the scene size the conversion depends on")

    h.write_json("annual_area.json", {
        "years": years,
        "pixels_total_per_year": int(stack.isel(time=0).size),
        "counts": [int(stack.isel(time=index).sum()) for index in range(3)],
        "annual_hectares": [round(float(value), 2) for value in annual],
        "cumulative_hectares": [round(float(value), 2) for value in cumulative],
        "pixel_area_m2": 100,
        "plot": png.name,
        "plot_bytes": png.stat().st_size if png.is_file() else None,
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
