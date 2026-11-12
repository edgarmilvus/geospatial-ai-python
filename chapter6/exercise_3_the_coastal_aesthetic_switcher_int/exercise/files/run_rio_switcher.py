"""Harness for exercise 3 (the interactive challenge) — the Rio aesthetic switcher.

Three floors of the same city: the street map, the watercolour, the dark one. The
harness checks that all three are in the control, that each points at its own
template, and that the city and the zoom are the ones the exercise names.
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

NAME = "exercise 3 (Rio switcher)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "rio_aesthetic_switcher.py", "rio_switcher")
    printed = log.getvalue()

    h.equal(module.rio_coords, [-22.9068, -43.1729],
            "the map is centred on Rio de Janeiro")
    h.equal(module.zoom_level, 11, "the exercise asks for zoom 11")

    saved = FILES.parent / "output" / "rio_aesthetic_switcher.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], -22.9068, "the map opens over Rio, south of the equator")
        h.close(centre[1], -43.1729, "the map opens over Rio, west of Greenwich")
    h.equal(maphtml.zoom(text), 11, "the map opens at zoom 11")

    names = [name for name, _ in maphtml.base_layers(text)]
    h.equal(len(names), 4,
            "the control holds the default and the three aesthetics")
    for required in ("Standard Detail", "Watercolor Presentation", "Dark Context"):
        h.contains(names, required, "the control lists %r" % required)

    urls = maphtml.layer_urls_by_name(text)
    h.equal(urls.get("Standard Detail"),
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "the readable layer is OpenStreetMap")
    h.contains(urls.get("Watercolor Presentation", ""), "stamen_watercolor",
               "the presentation layer is the watercolour template")
    h.contains(urls.get("Dark Context", ""), "dark_all",
               "the dark layer is CartoDB Dark Matter")
    named = [urls.get(name, "") for name in
             ("Standard Detail", "Watercolor Presentation", "Dark Context")]
    h.equal(len(set(named)), 3,
            "the three aesthetics are three different templates, not one renamed")

    h.equal(len(maphtml.added_to_map(text)), 4, "all four base layers are attached")
    h.contains(printed, "rio_aesthetic_switcher.html",
               "the listing names the file it wrote")

    h.write_json("rio_switcher.json", {
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
