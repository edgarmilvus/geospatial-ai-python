"""Harness for exercise 2 — a diverging margin map that pivots on zero.

The exercise is a classification claim: nine classes, symmetric about zero, red for
Republican and blue for Democrat, a district with no votes drawn as missing. The harness
recomputes the margin from the votes, rebuilds the class of every district with `bisect`,
and then reads the fills out of the two collections geopandas drew - the coloured one and
the grey one - to check that the neutral colour really lands on zero.
"""
import bisect
import contextlib
import io
import pathlib
import re
import sys
import traceback
import warnings

# The plane is unitless on purpose, so geopandas' geographic-area warning is not a bug.
warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 2 (electoral margin)"


def luminance(rgba):
    red, green, blue = rgba[:3]
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "electoral_margin_jenks.py", "electoral_margin")
    printed = log.getvalue()

    frame = module.district_gdf
    edges = [float(value) for value in module.classifier.bins]

    # The arithmetic. Twenty districts in, twenty rows out, unit squares, one district
    # with no votes at all.
    h.equal(len(frame), 20, "twenty districts are simulated")
    h.check((frame.geometry.area.round(9) == 1.0).all(),
            "every district is a unit square in the plane")
    vacant = frame[frame["Total_Votes"] == 0]
    h.equal(len(vacant), 1, "exactly one district cast no votes")
    h.check(vacant["Margin"].isna().all(),
            "that district's margin is missing, not zero, so it cannot be mis-coloured")
    votes = frame.dropna(subset=["Margin"])
    expected = (votes["Votes_A"] - votes["Votes_B"]) / votes["Total_Votes"]
    h.check((votes["Margin"] - expected).abs().max() < 1e-12,
            "every margin is (A - B) / (A + B)")
    h.check(votes["Margin"].abs().lt(1.0).all(),
            "every margin is a signed share strictly inside (-1, 1)")

    # The breaks: Jenks on the distance from zero, mirrored into nine edges.
    h.equal(module.K_PER_SIDE, 4, "Jenks is asked for four breaks per side")
    h.equal(len(edges), 9, "nine edges make nine classes")
    h.equal(edges[4], 0.0, "the fifth edge is exactly zero")
    h.check(all(abs(edges[i] + edges[8 - i]) < 1e-12 for i in range(9)),
            "the edges are symmetric about zero")
    h.check(all(b > a for a, b in zip(edges, edges[1:])), "the edges strictly ascend")
    h.equal(module.ZERO_EDGE, 4, "the listing knows which edge is zero")

    # Each district's class, rebuilt from the edges rather than trusted.
    rebuilt = [bisect.bisect_left(edges, value) for value in votes["Margin"]]
    h.equal([int(value) for value in votes["Margin_Class"]],
            [min(value, 8) for value in rebuilt],
            "every district's class follows from the margin and the edges")
    h.equal(int(sum(module.classifier.counts)), 19,
            "the class counts add up to the districts that have a margin")
    h.equal(len(module.classifier.counts), 9, "all nine classes are counted")

    # The fills. Two collections: the classified districts and the missing one.
    collections = module.ax.collections
    h.equal(len(collections), 2, "one collection for data, one for the missing district")
    filled = collections[0].get_facecolors()
    missing = collections[1].get_facecolors()
    h.equal(len(filled), 19, "nineteen districts are coloured")
    h.equal(len(missing), 1, "the district with no votes is drawn separately")
    h.check(abs(missing[0][0] - 0.827) < 0.02 and abs(missing[0][1] - 0.827) < 0.02,
            "and it is light grey, the colour missing_kwds names")

    # Map class -> colour, using the first district that carries each class.
    colours = {}
    for value, colour in zip(votes["Margin_Class"], filled):
        colours.setdefault(int(value), tuple(colour))
    h.equal(len(colours), 9, "all nine classes are on the map")

    h.check(luminance(colours[0]) < 0.35,
            "'RdBu' starts dark: class 0 has luminance %.3f" % luminance(colours[0]))
    h.check(luminance(colours[8]) < luminance(colours[4]),
            "and class 8 is darker than the neutral one")
    for index in range(4):
        h.check(colours[index][0] > colours[index][2],
                "class %d is red (r > b), the Republican side" % index)
    for index in range(5, 9):
        h.check(colours[index][2] > colours[index][0],
                "class %d is blue (b > r), the Democrat side" % index)

    # The centering claim: the two classes either side of zero are the two lightest and
    # are equally far from white.
    lightest = sorted(colours, key=lambda index: -luminance(colours[index]))[:2]
    h.equal(sorted(lightest), [4, 5], "the two lightest classes are the ones beside zero")
    h.check(abs(luminance(colours[4]) - luminance(colours[5])) < 0.05,
            "they are equally light: %.3f and %.3f"
            % (luminance(colours[4]), luminance(colours[5])))
    h.check(colours[4][0] > colours[4][2] and colours[5][2] > colours[5][0],
            "the warm one is below zero and the cool one above it")

    # The legend states the breaks and the missing-data case.
    labels = [text.get_text() for text in module.ax.get_legend().get_texts()]
    h.equal(len(labels), 10, "nine classes and the missing-data entry")
    h.contains(labels[-1], "No votes cast", "the legend names the missing district")
    printed_edges = [[float(value) for value in re.findall(r"-?\d+\.\d+", label)]
                     for label in labels[:9]]
    h.check(all(abs(numbers[-1] - edges[index]) < 0.011
                for index, numbers in enumerate(printed_edges)),
            "the nine legend entries print the nine edges, in order")

    h.contains(module.ax.get_title(), "k=9", "the title states the class count")
    h.contains(module.ax.get_title(), "centred on zero", "and the centering")
    h.check(not module.ax.axison, "the axes are switched off")

    saved = FILES.parent / "output" / "electoral_margin_jenks.png"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    payload = saved.read_bytes()
    h.check(payload.startswith(b"\x89PNG\r\n\x1a\n"), "the file is a PNG")
    h.check(len(payload) > 10_000, "the PNG carries a drawn map (%d bytes)" % len(payload))

    h.contains(printed, "Zero is edge 4: True", "the listing proves zero is an edge")
    h.contains(printed, "edges are symmetric: True", "and that the edges are symmetric")
    h.contains(printed, "1 (margin left missing, drawn grey)",
               "the listing reports the missing district")
    h.contains(printed, "output/electoral_margin_jenks.png",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("electoral_margin.json", {
        "districts": len(frame),
        "with_margin": len(votes),
        "missing": len(vacant),
        "margin_range": [round(float(votes["Margin"].min()), 3),
                         round(float(votes["Margin"].max()), 3)],
        "edges": [round(value, 3) for value in edges],
        "counts": [int(value) for value in module.classifier.counts],
        "class_colours": {str(key): [round(channel, 3) for channel in value]
                          for key, value in sorted(colours.items())},
        "luminance": {str(key): round(luminance(value), 3)
                      for key, value in sorted(colours.items())},
        "missing_colour": [round(channel, 3) for channel in missing[0][:3]],
        "legend": labels,
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
