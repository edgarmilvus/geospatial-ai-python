"""Harness for exercise 1 — the same four densities under two classification schemes.

The exercise is about a claim you can count: equal interval puts the three rural counties
in one class and leaves two classes empty, while quantiles gives every county its own
class. The harness checks the densities (5 000 000 / 5 is 1 000 000; 8 000 / 700 is 11.43),
then the breaks, then the class each county lands in, then the figure.
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

NAME = "exercise 1 (classification schemes)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "density_classification_bias.py", "density_bias")
    printed = log.getvalue()

    frame = module.counties_gdf
    density = frame.set_index("FIPS")["Density"]

    # Domain numbers: population / land area, county by county.
    h.equal(len(frame), 4, "four counties are simulated")
    h.check(abs(density["01001"] - 1_000_000.0) < 1e-6,
            "the urban county is 5 000 000 / 5 = 1 000 000 people per square mile")
    h.check(abs(density["01002"] - 20.0) < 1e-9, "the first rural county is 10 000 / 500 = 20")
    h.check(abs(density["01003"] - 25.0) < 1e-9, "the second is 15 000 / 600 = 25")
    h.check(abs(density["01004"] - 8_000 / 700) < 1e-9,
            "the third is 8 000 / 700 = 11.43")
    h.equal(int(frame["Density"].isna().sum()), 0, "the fillna(0) leaves nothing missing")

    # Seven classes over four counties, as the exercise asks. Mapclassify allows it and
    # leaves classes empty; that emptiness is itself the lesson.
    h.equal(module.K_CLASSES, 7, "the scheme is asked for seven classes, as required")
    h.equal(len(module.equal_interval.bins), 7, "seven classes publish seven breaks")

    # Equal interval: one width for all seven classes, so the three rural counties share
    # the bottom class and five classes stay empty.
    width = (density.max() - density.min()) / 7
    h.check(abs(module.equal_interval.bins[0] - (density.min() + width)) < 1e-3,
            "the first equal-interval break is min + range/7")
    h.equal([int(count) for count in module.equal_interval.counts],
            [3, 0, 0, 0, 0, 0, 1],
            "equal interval: three counties in the bottom class, one at the top")
    h.equal(int(sum(1 for count in module.equal_interval.counts if count == 0)), 5,
            "five of the seven equal-interval classes are empty")
    h.equal([int(value) for value in module.equal_interval.yb], [6, 0, 0, 0],
            "the urban county is the only one above the bottom class")
    h.equal(module.equal_interval.bins[-1], density.max(),
            "the top break is the maximum value")

    # Quantiles: equal count, so one county in every other class, and the class order
    # follows the values: 11.43 (01004) < 20 (01002) < 25 (01003) < 1 000 000 (01001).
    h.equal([int(count) for count in module.quantiles.counts], [1, 0, 1, 0, 1, 0, 1],
            "quantiles: one county in every other class")
    h.equal([int(value) for value in module.quantiles.yb], [6, 2, 4, 0],
            "the class each county lands in follows its density")
    h.check(module.quantiles.bins[4] > 1000 * module.quantiles.bins[3],
            "the last quantile break jumps three orders of magnitude (%.2f after %.2f)"
            % (module.quantiles.bins[4], module.quantiles.bins[3]))

    # Two maps of the same column, and the legends say what they did.
    panel_a, panel_b = module.axes
    h.equal(len(panel_a.get_legend().get_texts()), 7,
            "map A prints seven classes, five of them empty")
    h.equal(len(panel_b.get_legend().get_texts()), 7,
            "map B prints seven classes, three of them empty")
    h.contains(panel_a.get_title(), "Equal Interval", "map A names its scheme")
    h.contains(panel_b.get_title(), "Quantiles", "map B names its scheme")
    h.check(not panel_a.axison and not panel_b.axison, "both panels are maps")

    # The four fills: equal interval repeats the lightest colour three times.
    fills_a = [tuple(colour) for colour in panel_a.collections[0].get_facecolors()]
    fills_b = [tuple(colour) for colour in panel_b.collections[0].get_facecolors()]
    h.equal(len(set(fills_a)), 2, "map A draws two colours for four counties")
    h.equal(len(set(fills_b)), 4, "map B draws four colours for four counties")
    h.equal(len({value for value in module.equal_interval.yb}), 2,
            "and that is the same statement, read off the classes")
    h.equal(len({value for value in module.quantiles.yb}), 4,
            "quantiles spread the four counties over four distinct classes")

    saved = FILES.parent / "output" / "density_classification_bias.png"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    payload = saved.read_bytes()
    h.check(payload.startswith(b"\x89PNG\r\n\x1a\n"), "the file is a PNG")
    h.check(len(payload) > 10_000, "the PNG carries both panels (%d bytes)" % len(payload))

    h.contains(printed, "Counties per class: 3, 0, 0, 0, 0, 0, 1",
               "the listing reports the equal-interval counts")
    h.contains(printed, "Counties per class: 1, 0, 1, 0, 1, 0, 1",
               "the listing reports the quantile counts")
    h.contains(printed, "Class of each county: [6, 0, 0, 0]",
               "the listing reports the class of each county")
    h.contains(printed, "1,000,000.00 people per square mile",
               "the listing prints the urban density")
    h.contains(printed, "output/density_classification_bias.png",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("classification_bias.json", {
        "counties": len(frame),
        "density": {key: round(float(value), 2) for key, value in density.items()},
        "equal_interval": {
            "breaks": [round(float(value), 2) for value in module.equal_interval.bins],
            "counts": [int(value) for value in module.equal_interval.counts],
            "classes": [int(value) for value in module.equal_interval.yb],
        },
        "quantiles": {
            "breaks": [round(float(value), 2) for value in module.quantiles.bins],
            "counts": [int(value) for value in module.quantiles.counts],
            "classes": [int(value) for value in module.quantiles.yb],
        },
        "distinct_fills": {"equal_interval": len(set(fills_a)), "quantiles": len(set(fills_b))},
        "png_bytes": len(payload),
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
