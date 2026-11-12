"""Harness for the advanced application script — the five-way tile switcher.

The script's whole claim is that one interactive file lets a reader switch between
five base maps. So the harness reads the layer control out of the HTML: its section
must be called `base_layers` (radio buttons, not checkboxes), it must hold exactly
the five names the dictionary defines, in that order, and each name must resolve to
the tile template it was configured with.
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

NAME = "example 2 (tile switcher)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "tile_layer_switcher.py", "tile_switcher")
    # The script guards its run behind `if __name__ == "__main__"`, so importing it
    # defines the functions and writes nothing. The harness makes the three calls
    # the main block makes, in that order, and reads the message it returns.
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(io.StringIO()):
        base_map = module.create_base_map(
            location=module.TARGET_COORDINATES,
            zoom_start=module.INITIAL_ZOOM,
            default_tiles=module.TILE_LAYERS[list(module.TILE_LAYERS)[0]],
        )
        module.add_multiple_tile_layers(base_map, module.TILE_LAYERS)
        message = module.finalize_and_save_map(base_map, module.OUTPUT_FILENAME)
    printed = log.getvalue()

    # The configuration the script is built on.
    layers = module.TILE_LAYERS
    h.equal(len(layers), 5, "five tile layers are configured")
    h.equal(list(layers)[0], "OpenStreetMap (Default)",
            "the first entry is the default, the one the map loads with")
    h.check(all(name for name in layers), "every layer carries a display name")

    # The two helpers, driven directly: a name from the built-in table needs no
    # attribution of its own, a URL template does.
    h.equal(module.stamen_attribution("OpenStreetMap"), None,
            "a built-in provider supplies its own attribution")
    h.check(module.stamen_attribution("https://example.test/{z}/{x}/{y}.png") is not None,
            "a URL template is given an attribution")
    h.contains(module.STAMEN_ATTRIBUTION, "Stadia Maps",
               "the Stamen attribution names the tile host")

    empty = module.create_base_map(location=(1.0, 2.0), zoom_start=4)
    h.equal(tuple(empty.location), (1.0, 2.0), "create_base_map centres where asked")
    h.equal(empty.options["zoom"], 4, "create_base_map keeps the zoom")
    h.check(empty.control_scale is True, "create_base_map turns the scale bar on")

    # The artefact.
    saved = pathlib.Path(module.OUTPUT_FILENAME)
    h.check(saved.is_file(), "the script saved an HTML file at %s" % saved)
    h.equal(saved.name, "Infrastructure_Tile_Switcher.html",
            "the file keeps the chapter's name")
    h.equal(saved.parent, FILES.parent / "output",
            "the file is written to the project's output folder")

    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 37.7749, "the map is centred on the Bay Area latitude")
        h.close(centre[1], -122.4194, "the map is centred on the Bay Area longitude")
    h.equal(maphtml.zoom(text), 12, "the map opens at zoom 12")

    # The layer control: five base layers, no overlays, open by default, top right.
    names = [name for name, _ in maphtml.base_layers(text)]
    h.equal(len(names), 5, "the control lists five base layers")
    h.equal(names, ["openstreetmap"] + list(layers)[1:],
            "the control lists the default first, then the four configured layers")
    h.equal(maphtml.overlays(text), [], "nothing is registered as an overlay")
    h.contains(text, '"position": "topright"', "the control sits top right")
    h.contains(text, '"collapsed": false', "the control starts open")
    h.contains(text, "L.control.scale()", "the scale bar is in the document")

    urls = maphtml.layer_urls_by_name(text)
    h.contains(urls.get("Stamen Toner (High Contrast Roads)", ""), "stamen_toner",
               "the Toner entry points at the Toner template")
    h.contains(urls.get("Stamen Terrain (Topography Focus)", ""), "stamen_terrain",
               "the Terrain entry points at the Terrain template")
    h.contains(urls.get("CartoDB Positron (Light Background)", ""), "light_all",
               "the Positron entry points at the light CartoDB template")
    h.contains(urls.get("CartoDB DarkMatter (Night Mode/Data Focus)", ""), "dark_all",
               "the DarkMatter entry points at the dark CartoDB template")
    h.equal(urls.get("openstreetmap"), "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "the default is OpenStreetMap")

    # Every base layer is actually attached, so switching is possible on load.
    added = maphtml.added_to_map(text)
    h.equal(len(added), 5, "all five base layers are attached to the map")

    # What the reader sees.
    h.contains(message, "output/Infrastructure_Tile_Switcher.html",
               "the confirmation names the file it wrote")
    h.contains(message, "KB", "the confirmation reports the size of the file")
    h.check(str(pathlib.Path.home()) not in message,
            "the confirmation path carries no machine's home directory")

    h.write_json("tile_switcher.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "base_layers": names,
        "overlays": maphtml.overlays(text),
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
