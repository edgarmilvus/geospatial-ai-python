"""Harness for exercise 1 — the San Francisco contrast map.

The exercise asks for a map a reader can switch, at the same centre and zoom,
between the street map and a high-contrast one. So the harness checks the control:
two named base layers beside the default, each pointing at its own template.
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

NAME = "exercise 1 (SF contrast)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "sf_contrast_map.py", "sf_contrast")
    printed = log.getvalue()

    # The view the exercise pins: San Francisco at zoom 12.
    h.equal(module.sf_coords, [37.7749, -122.4194],
            "the map is centred on San Francisco")
    h.equal(module.zoom_level, 12, "the exercise asks for zoom 12")

    saved = FILES.parent / "output" / "sf_contrast_map.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 37.7749, "the map opens over the Peninsula")
        h.close(centre[1], -122.4194, "the map opens over the Peninsula")
    h.equal(maphtml.zoom(text), 12, "the map opens at zoom 12")

    names = [name for name, _ in maphtml.base_layers(text)]
    h.equal(len(names), 3,
            "the control holds the default and the two layers the exercise names")
    h.contains(names, "Standard Street Map", "the OSM layer is named for the reader")
    h.contains(names, "High Contrast Roads", "the Toner layer carries the required name")

    urls = maphtml.layer_urls_by_name(text)
    h.equal(urls.get("Standard Street Map"),
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "the named street layer is OpenStreetMap")
    h.contains(urls.get("High Contrast Roads", ""), "stamen_toner",
               "the contrast layer points at the Toner template")
    h.equal(urls.get("openstreetmap"), urls.get("Standard Street Map"),
            "the default layer is the same tile set as the named one")
    h.contains(text, "Stadia Maps",
               "the custom template carries its attribution into the document")

    h.equal(len(maphtml.added_to_map(text)), 3, "all three base layers are attached")
    h.contains(printed, "output/sf_contrast_map.html",
               "the listing names the file it wrote")
    h.contains(text, '"collapsed": true', "the control starts collapsed")

    h.write_json("sf_contrast.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "base_layers": names,
        "tile_urls": urls,
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
