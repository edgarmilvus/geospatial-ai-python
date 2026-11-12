"""Harness for the chapter's basic example — one marker, one popup.

The example makes three claims worth measuring: the map is centred *north* of the
point so the controls do not cover it, the marker sits exactly on the point, and the
popup carries the model's sentence. The harness reads all three out of the file.
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

NAME = "example 1 (marker and popup)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "marker_with_popup.py", "marker_popup")
    printed = log.getvalue()

    h.equal(module.LATITUDE, 48.8584, "the marker latitude is the Eiffel Tower's")
    h.equal(module.LONGITUDE, 2.2945, "the marker longitude is the Eiffel Tower's")
    h.equal(module.initial_location, [48.8584 + 0.005, 2.2945],
            "the map centre is offset 0.005 degrees north, as the comment says")
    h.check(module.initial_location[0] > module.LATITUDE,
            "the offset puts the marker below the centre of the screen")
    h.equal(module.popup_object.options["max_width"], 350,
            "the popup is given the Sizing Constraint the text explains")
    h.contains(module.POPUP_CONTENT, "Confidence: 98.5%",
               "the popup text carries the model's confidence")

    saved = FILES.parent / "output" / "basic_marker_map.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        # 48.8584 + 0.005 in binary floating point is not exactly 48.8634.
        h.check(abs(centre[0] - 48.8634) < 1e-9,
                "the map is centred at 48.8634 N (%r)" % (centre[0],))
        h.check(abs(centre[1] - 2.2945) < 1e-9,
                "the map is centred at 2.2945 E (%r)" % (centre[1],))
    h.equal(maphtml.zoom(text), 15, "the map opens at zoom 15")

    # The marker is on the point, not on the centre: order of the two coordinates is
    # the chapter's pitfall, so the assertion checks both numbers and their order.
    h.contains(text, "[48.8584, 2.2945]", "the marker is placed on the point itself")
    h.equal(maphtml.count(text, "L.marker("), 1, "the document holds exactly one marker")
    h.contains(text, module.POPUP_CONTENT, "the popup sentence is in the document")
    h.contains(text, "Click for GeoAI Details", "the tooltip is in the document")

    urls = maphtml.tile_urls(text)
    h.check(urls and "cartocdn.com/light_all" in urls[0],
            "the base map is the neutral CartoDB Positron layer")
    h.contains(printed, "output/basic_marker_map.html",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("marker_popup.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "marker": [module.LATITUDE, module.LONGITUDE],
        "popup": module.POPUP_CONTENT,
        "tile_url": urls[0] if urls else None,
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
