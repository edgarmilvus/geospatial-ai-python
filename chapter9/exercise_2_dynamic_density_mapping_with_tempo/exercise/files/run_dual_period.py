"""Harness for exercise 2 — two density surfaces, one map, a real shift between them.

The exercise's claim is temporal: the morning window and the mid-day window sit in
different parts of the city. The harness recomputes both windows from the listing's own
frame, measures the distance between their centroids, and then reads the two `L.heatLayer`
datasets out of the saved document — sizes, radius, gradient stops and the alpha the
book tried to set with an option Leaflet does not have.
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

NAME = "exercise 2 (dual-period density)"


def centroid(pairs):
    latitudes = [pair[0] for pair in pairs]
    longitudes = [pair[1] for pair in pairs]
    return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "dual_period_heatmap.py", "dual_period")
    printed = log.getvalue()

    frame = module.gdf
    h.equal(len(frame), 20000, "twenty thousand pings are simulated")
    h.equal(frame.crs.to_epsg(), 4326, "the frame is in WGS 84")
    h.equal(str(frame["start_time"].dtype)[:8], "datetime", "start_time is a datetime")

    # The segmentation, rebuilt from the hour of each ping.
    hours = frame["start_time"].dt.hour
    morning = frame[(hours >= 7) & (hours < 9)]
    midday = frame[(hours >= 11) & (hours < 13)]
    h.equal(len(morning), len(module.morning_data),
            "the morning layer holds every ping between 07:00 and 08:59")
    h.equal(len(midday), len(module.mid_day_data),
            "the mid-day layer holds every ping between 11:00 and 12:59")
    h.equal(len(morning) + len(midday) < len(frame), True,
            "the two windows are a subset, not the whole day")
    # A uniform clock over 24 hours would put about 1 667 pings in a two-hour window.
    h.check(1500 <= len(morning) <= 1800,
            "the morning window holds %d pings, about a twelfth of the day" % len(morning))
    h.check(1500 <= len(midday) <= 1800,
            "and so does the mid-day window (%d)" % len(midday))

    # The heatmap data is [lat, lon], first element first.
    first = module.morning_data[0]
    h.equal(len(first), 2, "the plugin is fed [lat, lon] pairs")
    h.check(abs(first[0] - module.morning_peak_gdf.geometry.y.iloc[0]) < 1e-12,
            "and the first element is the latitude")
    h.check(abs(first[1] - module.morning_peak_gdf.geometry.x.iloc[0]) < 1e-12,
            "the second is the longitude")

    # The shift. This is the whole point of the exercise, and it is a number.
    morning_centre = centroid(module.morning_data)
    midday_centre = centroid(module.mid_day_data)
    h.check(abs(morning_centre[0] - 40.720) < 0.006,
            "the morning cloud sits over the residential district (%.4f N)" % morning_centre[0])
    h.check(abs(morning_centre[1] + 74.020) < 0.006,
            "and west of the centre (%.4f E)" % morning_centre[1])
    h.check(abs(midday_centre[0] - 40.755) < 0.006,
            "the mid-day cloud sits over the business district (%.4f N)" % midday_centre[0])
    h.check(abs(midday_centre[1] + 73.985) < 0.006,
            "and east of it (%.4f E)" % midday_centre[1])
    h.check(midday_centre[0] - morning_centre[0] > 0.02,
            "the two windows are %.4f degrees apart in latitude"
            % (midday_centre[0] - morning_centre[0]))
    h.check(midday_centre[1] - morning_centre[1] > 0.02,
            "and %.4f degrees apart in longitude"
            % (midday_centre[1] - morning_centre[1]))

    # The document: two heat layers, each with its own data and its own gradient.
    saved = FILES.parent / "output" / "dynamic_density_map.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.check(abs(centre[0] - 40.7) < 1e-9 and abs(centre[1] + 73.97) < 1e-9,
                "centred on the city the listing names")
    h.equal(maphtml.zoom(text), 12, "at zoom 12")
    urls = maphtml.tile_urls(text)
    h.check(urls and "cartocdn.com/dark_all" in urls[0],
            "the base map is CartoDB Dark Matter, the high-contrast style asked for")

    layers = maphtml.heat_layers(text)
    h.equal(len(layers), 2, "the document holds two heat layers")
    options = maphtml.heat_layer_options(text)
    h.equal(len(options), 2, "each with its own options")
    if len(layers) == 2:
        h.equal(len(layers[0]), len(module.morning_data),
                "the first layer is the morning window")
        h.equal(len(layers[1]), len(module.mid_day_data),
                "the second is the mid-day window")
        h.equal(options[0].get("radius"), 15, "both layers use radius 15")
        h.equal(options[1].get("radius"), 15, "so the smoothing is comparable")
        h.check(abs(options[0].get("minOpacity", 0) - 0.2) < 1e-9,
                "and both start at 0.2 opacity")

        morning_stops = options[0].get("gradient", {})
        midday_stops = options[1].get("gradient", {})
        h.equal(len(morning_stops), 3, "the morning gradient has three stops")
        h.equal(len(midday_stops), 3, "the mid-day gradient has three stops")
        h.check(all("rgba(" in colour and ",0.7)" in colour
                    for colour in morning_stops.values()),
                "every morning stop carries the 0.7 alpha the requirement asks for")
        h.check(all("rgba(" in colour and ",0.7)" in colour
                    for colour in midday_stops.values()),
                "and so does every mid-day stop")
        h.check("255,0,0" in morning_stops.get("0.9", ""),
                "the morning ramp ends red")
        h.check("0,0,139" in midday_stops.get("0.9", ""),
                "the mid-day ramp ends dark blue")
        h.check(all("maxOpacity" not in option for option in options),
                "no maxOpacity is passed: leaflet-heat has no such option, which is why "
                "the alpha lives in the gradient")

    overlays = [name for name, _ in maphtml.overlays(text)]
    h.equal(sorted(overlays),
            ["Mid-Day Density (11 AM-1 PM)", "Morning Peak Density (7-9 AM)"],
            "the layer control offers both windows as toggles")

    h.contains(printed, "Morning peak (07:00-08:59): 1630 pings",
               "the run reports the morning count")
    h.contains(printed, "Shift between the windows:  +0.0349 latitude",
               "and the shift between the two clouds")
    h.contains(printed, "output/dynamic_density_map.html",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("dual_period.json", {
        "pings": len(frame),
        "morning": {"count": len(module.morning_data),
                    "centre": [round(value, 4) for value in morning_centre]},
        "midday": {"count": len(module.mid_day_data),
                   "centre": [round(value, 4) for value in midday_centre]},
        "shift": [round(midday_centre[0] - morning_centre[0], 4),
                  round(midday_centre[1] - morning_centre[1], 4)],
        "radius": options[0].get("radius") if options else None,
        "gradients": [option.get("gradient") for option in options],
        "overlays": overlays,
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
