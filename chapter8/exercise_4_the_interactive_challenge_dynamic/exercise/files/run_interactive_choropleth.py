"""Harness for exercise 4 — the choropleth as an interactive document.

The exercise stops being a picture here: the output is HTML, and everything it claims is
in the file as data. The harness parses the GeoJSON payload the page loads, checks the six
Jenks classes and the tooltip fields the control advertises, calls the listing's own
`style_function` on those features to see the six fills it produces, and reads the layer
control's two basemaps out of the rendered JavaScript.
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

NAME = "exercise 4 (interactive choropleth)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "interactive_tract_choropleth.py", "tract_choropleth")
    printed = log.getvalue()

    frame = module.tract_gdf

    # The data and the classification.
    h.equal(len(frame), 30, "thirty census tracts are simulated")
    h.equal(frame.crs.to_epsg(), 4326, "the frame is in WGS 84, which is what Folium needs")
    h.equal(module.k_classes, 6, "Jenks is asked for six classes")
    change = frame["PopChange_Percent"]
    h.check(change.between(-20.0, 30.0).all(),
            "population change stays inside the simulated -20 to +30 percent window")
    h.equal(len(module.classifier.bins), 6, "six classes publish six breaks")
    h.check(list(module.classifier.bins) == sorted(module.classifier.bins),
            "the breaks ascend")
    h.equal(int(sum(module.classifier.counts)), 30, "every tract falls in one class")
    h.equal([int(value) for value in frame["Jenks_Class"]],
            [int(value) for value in module.classifier.yb],
            "each tract's class is its own entry in `yb`, not some other tract's")
    h.equal(frame["Jenks_Class"].nunique(), 6, "all six classes are used")

    # The style function is the map's colour rule. Called directly, it must answer with a
    # colour per class, the low class red and the high class green.
    geojson = module.geojson_data
    payload = __import__("json").loads(geojson)
    h.equal(payload["type"], "FeatureCollection", "the frame serialises as a FeatureCollection")
    h.equal(len(payload["features"]), 30, "all thirty tracts travel in the payload")
    property_keys = set(payload["features"][0]["properties"])
    h.check({"Tract ID", "Pop2020", "PopChange_Percent", "Jenks_Class"} <= property_keys,
            "each feature carries the identifier, the count, the change and the class")

    fills = {}
    for feature in payload["features"]:
        style = module.style_function(feature)
        fills[feature["properties"]["Jenks_Class"]] = style["fillColor"]
        h.check(style["color"] == "black" and abs(style["fillOpacity"] - 0.7) < 1e-9,
                "every feature is outlined in black at 0.7 opacity")
    h.equal(sorted(fills), [0, 1, 2, 3, 4, 5], "six different fills, one per class")
    h.equal(len(set(fills.values())), 6, "no two classes share a colour")

    def channels(hex_colour):
        return tuple(int(hex_colour[index:index + 2], 16) for index in (1, 3, 5))

    h.check(channels(fills[0])[0] > channels(fills[0])[2],
            "class 0 is red (decline): %s" % fills[0])
    h.check(channels(fills[5])[1] > channels(fills[5])[0],
            "class 5 is green (growth): %s" % fills[5])

    def luminance(hex_colour):
        red, green, blue = channels(hex_colour)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    lightest = max(fills, key=lambda index: luminance(fills[index]))
    h.equal(lightest, 3, "the palest class is the one just above the middle of the ramp")

    # The document.
    saved = FILES.parent / "output" / "interactive_tract_choropleth.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.check(abs(centre[0] - float(frame.geometry.centroid.y.mean())) < 1e-6,
                "the map is centred on the tracts' mean latitude")
        h.check(abs(centre[1] - float(frame.geometry.centroid.x.mean())) < 1e-6,
                "and on their mean longitude")
    h.equal(maphtml.zoom(text), 8, "the map opens at zoom 8")

    layers = maphtml.geojson_layers(text)
    h.equal(len(layers), 1, "one GeoJSON layer is loaded")
    h.equal(layers[0]["type"], "FeatureCollection", "and it is a FeatureCollection")
    h.equal(len(layers[0]["features"]), 30, "holding all thirty tracts")
    h.equal(sorted(feature["properties"]["Jenks_Class"] for feature in layers[0]["features"]),
            sorted(int(value) for value in frame["Jenks_Class"]),
            "the classes in the document are the ones the listing computed")

    # Two basemaps, named, and a control that offers them.
    bases = maphtml.base_layers(text)
    h.equal(len(bases), 2, "the layer control offers exactly two basemaps")
    h.equal([name for name, _ in bases], ["OpenStreetMap", "CartoDB Dark Matter"],
            "named as the requirement asks")
    urls = maphtml.layer_urls_by_name(text)
    h.check("openstreetmap.org" in urls.get("OpenStreetMap", ""),
            "OpenStreetMap resolves to the OSM tile server")
    h.check("cartocdn.com/dark_all" in urls.get("CartoDB Dark Matter", ""),
            "Dark Matter resolves to the CartoDB dark tiles")
    overlays = maphtml.overlays(text)
    h.equal([name for name, _ in overlays], ["Population Change (Jenks Classified)"],
            "the choropleth itself is a toggleable overlay")

    # The tooltip: three fields, three labelled aliases, applied on hover.
    h.contains(text, '"Tract ID", "Pop2020", "PopChange_Percent"',
               "the tooltip reads the three required properties")
    h.contains(text, '"Tract ID:"', "the tooltip labels the identifier")
    h.contains(text, '"2020 Population:"', "the tooltip labels the raw count")
    h.contains(text, '"Pop Change (2010-2020 %):"', "the tooltip labels the change")
    h.contains(text, "bindTooltip", "the tooltip is bound to the layer")
    h.equal(maphtml.count(text, "L.geoJson("), 1, "one GeoJSON layer, not two")

    h.contains(printed, "30 census tracts", "the listing reports what it built")
    h.contains(printed, "Tracts per class: 9, 6, 6, 4, 2, 3",
               "the listing prints the class counts")
    h.contains(printed, "class 0: #a50026", "and the colour of the first class")
    h.contains(printed, "output/interactive_tract_choropleth.html",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("interactive_choropleth.json", {
        "tracts": len(frame),
        "classes": module.k_classes,
        "breaks": [round(float(value), 2) for value in module.classifier.bins],
        "counts": [int(value) for value in module.classifier.counts],
        "fills": fills,
        "base_layers": [name for name, _ in bases],
        "overlays": [name for name, _ in overlays],
        "tile_urls": urls,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
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
