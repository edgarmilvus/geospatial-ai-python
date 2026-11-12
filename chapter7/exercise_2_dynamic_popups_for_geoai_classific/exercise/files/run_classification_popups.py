"""Harness for exercise 2 — classification popups built from the attribute table.

The requirement is formatting, not decoration: a confidence of 0.985 must reach the
reader as 98.5%, inside a structured HTML block, coloured by the 80% threshold. The
harness decodes every popup and checks the strings a reader would see.
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

NAME = "exercise 2 (classification popups)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "classification_popups.py", "classification_popups")
    printed = log.getvalue()

    frame = module.df
    h.equal(len(frame), 5, "the sample holds five classified points")
    h.equal(sorted(frame["classification"]),
            ["Agriculture", "Barren Land", "Forest", "Urban", "Water"],
            "the five land-cover classes the exercise defines are all present")
    h.check(frame["confidence_score"].between(0.0, 1.0).all(),
            "every confidence is a probability, not a percentage already")

    # The formatting rule: multiply by 100 and keep one decimal.
    percentages = [f"{score * 100:.1f}%" for score in frame["confidence_score"]]
    h.equal(percentages, ["98.5%", "72.1%", "85.0%", "99.9%", "65.5%"],
            "the scores format to the percentages the popups must show")

    saved = FILES.parent / "output" / "exercise2_dynamic_popups.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 34.05, "the map opens over the sample area")
        h.close(centre[1], -118.25, "the map opens over the sample area")
    h.equal(maphtml.zoom(text), 14, "the map opens at zoom 14")

    h.equal(maphtml.count(text, "L.marker("), 5, "every point becomes a marker")

    popups = maphtml.iframe_documents(text)
    h.equal(len(popups), 5, "every marker carries an iframe popup")
    for popup, (_, row) in zip(popups, frame.iterrows()):
        h.contains(popup, "<h3", "the popup is structured HTML, not one long string")
        h.contains(popup, row["classification"], "the popup names its class")
        h.contains(popup, f"{row['confidence_score'] * 100:.1f}%",
                   "the popup shows %s as a percentage" % row["classification"])
        h.contains(popup, row["analysis_date"], "the popup shows the analysis date")

    # The 80% rule, read back from the colour the popup puts around the number.
    green = sum("color: green" in popup for popup in popups)
    red = sum("color: red" in popup for popup in popups)
    h.equal(green, int((frame["confidence_score"] > 0.8).sum()),
            "confidences above 80% are painted green")
    h.equal(red, int((frame["confidence_score"] <= 0.8).sum()),
            "confidences at or below 80% are painted red")
    h.equal(green + red, 5, "every confidence is coloured, none is left plain")

    for classification in frame["classification"]:
        h.contains(text, classification, "the %s marker is hoverable by name" % classification)

    h.contains(printed, "exercise2_dynamic_popups.html",
               "the listing names the file it wrote")

    h.write_json("classification_popups.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "points": len(frame),
        "percentages": percentages,
        "green": green,
        "red": red,
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
