"""Harness for the chapter's first example — the Mount Fuji map.

The listing builds a `folium.Map`, saves it and prints one line. The harness keeps
the object, then reads the HTML it wrote: the centre, the zoom and the tile template
are the numbers the listing computed, and the file has to carry them.
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

NAME = "example 1 (Mount Fuji map)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "fuji_map_initialization.py", "fuji_map")
    printed = log.getvalue()

    # The constants the chapter defines, and the object built from them.
    h.equal(module.FUJI_LATITUDE, 35.3606, "the latitude is the one in the book")
    h.equal(module.FUJI_LONGITUDE, 138.7278, "the longitude is the one in the book")
    h.equal(module.INITIAL_ZOOM, 12, "the zoom is the one in the book")
    h.equal(module.basic_map.options["zoom"], 12,
            "the map object carries that zoom")
    h.equal(tuple(module.basic_map.location), (35.3606, 138.7278),
            "the map object is centred on Fuji")

    # The artefact: one HTML file, under the project's output/, created by the run.
    saved = pathlib.Path(module.OUTPUT_FILENAME)
    h.check(saved.is_file(), "the listing saved an HTML file at %s" % saved)
    h.equal(saved.parent, FILES.parent / "output",
            "the file is written to the project's output folder")
    h.equal(saved.name, "06_02_fuji_map.html", "the file keeps the chapter's name")

    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    # What the listing computed, read back out of the document as data.
    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 35.3606, "the map is centred on Fuji's latitude")
        h.close(centre[1], 138.7278, "the map is centred on Fuji's longitude")
    h.equal(maphtml.zoom(text), 12, "the map opens at zoom 12")

    urls = maphtml.tile_urls(text)
    h.equal(len(urls), 1, "an unlayered map carries exactly one tile layer")
    if urls:
        h.equal(urls[0], "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                "the base layer is OpenStreetMap")
    h.contains(text, "OpenStreetMap", "the tile attribution is in the document")
    h.equal(maphtml.base_layers(text), [],
            "with one tile layer there is no layer control to switch")

    # A document that only claims to be a map is not a map.
    h.contains(text, "L.map(", "the document initialises a Leaflet map")

    # What the reader sees.
    h.contains(printed, "output/06_02_fuji_map.html",
               "the confirmation line names the file and its folder")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("fuji_map.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
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
