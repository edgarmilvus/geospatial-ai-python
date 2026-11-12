"""Harness for the chapter's basic example — 500 drone sightings as a heat layer.

The example is about density, but the thing that can be wrong is the coordinate order: a
reversed list of pairs produces a beautiful heatmap in the wrong hemisphere. The harness
reads the `L.heatLayer` dataset out of the saved document, checks that every pair is
[latitude, longitude] inside the Los Angeles band, that the two clusters hold roughly the
70/30 split the listing simulates, and that the map is centred and zoomed as configured.
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

NAME = "example 1 (drone density heatmap)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "drone_density_heatmap.py", "drone_heatmap")
    printed = log.getvalue()

    h.equal(module.CENTER_LAT, 34.0522, "the study area is centred on Los Angeles")
    h.equal(module.CENTER_LON, -118.2437, "the study area is centred on Los Angeles")
    h.equal(module.NUM_POINTS, 500, "five hundred sightings are simulated")
    h.equal(len(module.data_points), 500, "and all of them are in the list")

    # The 70/30 split the listing's comment announces.
    downtown, outpost = module.cluster_counts
    h.equal(downtown + outpost, 500, "every sighting belongs to one of the two clusters")
    h.check(300 <= downtown <= 400,
            "the downtown cluster holds about 70%% of the points (%d)" % downtown)
    h.check(100 <= outpost <= 200,
            "the suburban outpost holds about 30%% (%d)" % outpost)

    # The coordinate order. Latitude is the first element of every pair, and here that is
    # checkable against the place: 34 N, not -118.
    latitudes = [point[0] for point in module.data_points]
    longitudes = [point[1] for point in module.data_points]
    h.check(all(33.9 < value < 34.3 for value in latitudes),
            "every first element is a Los Angeles latitude")
    h.check(all(-118.5 < value < -118.0 for value in longitudes),
            "every second element is a Los Angeles longitude")
    h.check(min(latitudes) > 0 and max(longitudes) < 0,
            "no pair was written [lon, lat]: that would put 34 in the longitude slot")

    # The document.
    saved = FILES.parent / "output" / "basic_drone_density_map.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.check(abs(centre[0] - 34.0522) < 1e-9, "the map opens over the study area")
        h.check(abs(centre[1] + 118.2437) < 1e-9, "the map opens over the study area")
    h.equal(maphtml.zoom(text), 12, "at zoom 12, a city-wide view")

    urls = maphtml.tile_urls(text)
    h.check(urls and "cartocdn.com/light_all" in urls[0],
            "the base map is CartoDB Positron, the light style the comment asks for")

    layers = maphtml.heat_layers(text)
    h.equal(len(layers), 1, "the document holds one heat layer")
    if layers:
        h.equal(len(layers[0]), 500, "all five hundred sightings are in it")
        h.equal(len({tuple(point) for point in layers[0]}), 500,
                "no pair was duplicated on the way into the layer")
        first = layers[0][0]
        h.equal(len(first), 2, "unweighted points are [lat, lon] pairs")
        h.check(abs(first[0] - module.data_points[0][0]) < 1e-12,
                "the document starts with the first simulated latitude")
    h.equal(maphtml.count(text, "L.heatLayer("), 1, "one heat layer, not two")

    h.contains(printed, "Sightings: 500", "the listing reports what it simulated")
    h.contains(printed, "Downtown cluster: 349 points", "and the size of each cluster")
    h.contains(printed, "First three pairs [lat, lon]", "and shows the pair order")
    h.contains(printed, "output/basic_drone_density_map.html",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("drone_heatmap.json", {
        "points": len(module.data_points),
        "clusters": {"downtown": downtown, "outpost": outpost},
        "lat_range": [round(min(latitudes), 4), round(max(latitudes), 4)],
        "lon_range": [round(min(longitudes), 4), round(max(longitudes), 4)],
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
