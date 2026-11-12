"""Harness for exercise 2 — the Alpine terrain explorer.

The exercise is about making the terrain the default view, so the first tile layer in
the document — the one the map loads with — must be the terrain template, and the
second, renamed layer must still be plain OpenStreetMap dressed under a different
name for the control panel.
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

NAME = "exercise 2 (Alpine terrain)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "alpine_terrain_map.py", "alpine_terrain")
    printed = log.getvalue()

    h.equal(module.matterhorn_coords, [45.9766, 7.6585],
            "the map is centred on the Matterhorn")
    # The exercise asks for a zoom between 13 and 15, with a comment saying why.
    h.check(13 <= module.zoom_level <= 15,
            "the zoom sits in the range the exercise asks for (%r)" % module.zoom_level)
    h.equal(module.zoom_level, 14, "the solution pins the justified zoom")

    saved = FILES.parent / "output" / "alpine_terrain.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 45.9766, "the map opens on the Matterhorn")
        h.close(centre[1], 7.6585, "the map opens on the Matterhorn")
    h.equal(maphtml.zoom(text), 14, "the map opens at zoom 14")

    urls = maphtml.tile_urls(text)
    h.check(urls, "the document declares tile layers")
    if urls:
        h.contains(urls[0], "stamen_terrain",
                   "the layer the map loads with is the terrain template")

    names = [name for name, _ in maphtml.base_layers(text)]
    h.equal(len(names), 3,
            "the control holds the default and the two layers the exercise names")
    h.contains(names, "Detailed Terrain", "the terrain layer is named for the reader")
    h.contains(names, "OpenTopoMap Style", "the second layer carries the required name")

    by_name = maphtml.layer_urls_by_name(text)
    h.contains(by_name.get("Detailed Terrain", ""), "stamen_terrain",
               "the named terrain layer is the same template as the default")
    h.equal(by_name.get("OpenTopoMap Style"),
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "the simulated topo layer is plain OpenStreetMap under another name")
    h.contains(text, "Stadia Maps",
               "the terrain template carries its attribution into the document")

    h.contains(printed, "alpine_terrain.html", "the listing names the file it wrote")

    h.write_json("alpine_terrain.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "base_layers": names,
        "tile_urls": by_name,
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
