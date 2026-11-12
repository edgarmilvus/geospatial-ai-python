"""Harness for exercise 4 — the London map with a hidden, attributed second layer.

The exercise is about the two `TileLayer` parameters a professional map needs:
`show=False` decides whether a base layer is drawn on load, and `attr` decides what
the map claims about the tiles it is showing. The harness checks both in the
document: the Toner layer must be in the control and attached to nothing.
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

NAME = "exercise 4 (London tiles)"
REQUIRED_NOTICE = "Data provided by Stamen Design. Project Copyright 2024 GeoAI."


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "london_custom_tiles.py", "london_tiles")
    printed = log.getvalue()

    h.equal(module.london_coords, [51.5074, 0.1278],
            "the map is centred on London")
    h.equal(module.custom_attribution, REQUIRED_NOTICE,
            "the attribution is the exact string the exercise requires")

    saved = FILES.parent / "output" / "london_custom_tiles.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 51.5074, "the map opens over London")
        h.close(centre[1], 0.1278, "the map opens over London")
    h.equal(maphtml.zoom(text), 10, "the map opens at zoom 10")

    layers = dict(maphtml.base_layers(text))
    h.equal(len(layers), 3,
            "the control holds the default, the named OSM base and the Toner layer")
    for required in ("Project OSM Base", "Toner for Data Overlay"):
        h.contains(list(layers), required, "the control lists %r" % required)

    # The trap of the exercise: a layer can be in the control and not on the map.
    added = maphtml.added_to_map(text)
    h.check(layers.get("Toner for Data Overlay") not in added,
            "the Toner layer is not drawn when the map loads (show=False)")
    h.check(layers.get("Project OSM Base") in added,
            "the named OSM layer is the one drawn (it is the default)")
    h.check(layers.get("openstreetmap") in added,
            "the map's own base layer is still attached")

    # The attribution, read from the Toner layer's own options in the document.
    variables = maphtml.tile_layers(text)
    toner = variables.get(layers.get("Toner for Data Overlay"), {})
    h.equal(toner.get("attribution"), REQUIRED_NOTICE,
            "the Toner layer carries the project's notice, not Stamen's default")
    h.contains(toner.get("url", ""), "stamen_toner",
               "the Toner layer points at the Toner template")

    h.contains(printed, "london_custom_tiles.html",
               "the listing names the file it wrote")

    h.write_json("london_tiles.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "base_layers": list(layers),
        "drawn_on_load": sorted(added & set(layers.values())),
        "toner_attribution": toner.get("attribution"),
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
