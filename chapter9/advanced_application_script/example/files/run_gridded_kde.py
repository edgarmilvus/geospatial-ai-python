"""Harness for the advanced application script — gridded KDE over 5 000 pings.

The script claims three things a heatmap can quietly get wrong: the bandwidth is in degrees
and not in scipy's factor units, the peak of the density surface is on the congested
hotspot the generator planted, and the intensities the Leaflet layer receives are in 0..1
so that the colour cap means something. The harness calls the script's `main()` — it is
guarded, so importing it runs nothing — and then reads the heat layer back out of the HTML.
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

NAME = "example 2 (gridded KDE traffic)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "gridded_kde_traffic.py", "gridded_kde")
        result = module.main()
    printed = log.getvalue()

    h.equal(module.N_POINTS, 5000, "five thousand GPS pings are simulated")
    h.equal(module.GRID_RESOLUTION, 150, "the grid is 150 by 150 cells")
    h.equal(result["points"], 5000, "and all of them are in the frame")
    h.equal(result["cells"], 22500, "so 22 500 cells are evaluated")
    h.check(22400 <= result["grid_points"] <= 22500,
            "%d cells carry a non-zero density" % result["grid_points"])

    # Bandwidth: the number is in degrees, and the factor handed to scipy is derived from
    # the sample's own spread, not from the number itself.
    spread = result["spread"]
    h.check(0.01 < spread < 0.05,
            "the sample spreads %.4f degrees, which is a city and not a continent" % spread)
    h.check(abs(result["bw_factor"] * spread - module.KDE_BANDWIDTH) < 1e-9,
            "bw_method x spread is the 0.0035-degree bandwidth")
    h.check(abs(module.BANDWIDTH_METRES - 389.62) < 0.5,
            "0.0035 degrees is about 390 metres (%.1f)" % module.BANDWIDTH_METRES)

    # The peak. The generator puts half the points at 34.0572 N, -118.2517 E, so the
    # highest density cell must be within a couple of hundred metres of it.
    peak_lat, peak_lon = result["peak"]
    h.check(abs(peak_lat - (module.CENTER_LAT + 0.005)) < 0.01,
            "the peak sits on hotspot 1 in latitude (%.4f)" % peak_lat)
    h.check(abs(peak_lon - (module.CENTER_LON - 0.008)) < 0.01,
            "and in longitude (%.4f)" % peak_lon)
    h.check(result["peak_density"] > 0, "the surface has a positive maximum")
    h.check(abs(result["cap"] - result["peak_density"] * module.CAP_FRACTION) < 1e-6,
            "the colour cap is half the peak, as CAP_FRACTION says")
    h.check(0 < result["saturated"] < 100,
            "%d cells reach the cap, so the cap is doing something" % result["saturated"])

    # The document.
    saved = FILES.parent / "output" / "advanced_traffic_kde_heatmap.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.check(abs(centre[0] - module.CENTER_LAT) < 1e-9, "centred on the study area")
        h.check(abs(centre[1] - module.CENTER_LON) < 1e-9, "centred on the study area")
    h.equal(maphtml.zoom(text), 12, "at zoom 12")

    layers = maphtml.heat_layers(text)
    h.equal(len(layers), 1, "one heat layer")
    if layers:
        h.equal(len(layers[0]), result["grid_points"],
                "one entry per non-empty grid cell")
        h.equal(len(layers[0][0]), 3, "the entries are [lat, lon, intensity] triples")
        intensities = [point[2] for point in layers[0]]
        h.check(all(0.0 <= value <= 1.0 for value in intensities),
                "every intensity is in 0..1, which is what leaflet-heat reads")
        h.check(sum(1 for value in intensities if value == 0.0) <= 5,
                "only the far tail underflows to zero: %d cell(s)"
                % sum(1 for value in intensities if value == 0.0))
        h.check(abs(max(intensities) - 1.0) < 1e-9,
                "the hottest cell is exactly 1.0, so the cap is where red starts")
        h.check(sum(1 for value in intensities if value >= 1.0) == result["saturated"],
                "and the number of saturated cells is the one the run printed")
        lats = [point[0] for point in layers[0]]
        lons = [point[1] for point in layers[0]]
        # The background cluster (20% of the pings, 0.05 degrees of noise) widens the grid
        # beyond the two hotspots; the whole layer still sits inside Los Angeles County.
        h.check(33.5 < min(lats) and max(lats) < 34.5,
                "the layer stays over Los Angeles in latitude (%.3f to %.3f)"
                % (min(lats), max(lats)))
        h.check(-118.7 < min(lons) and max(lons) < -117.6,
                "and in longitude (%.3f to %.3f)" % (min(lons), max(lons)))

    options = maphtml.heat_options(text)
    h.equal(options.get("radius"), 18, "the layer radius is 18 pixels")
    h.equal(options.get("blur"), 15, "the blur is 15")
    h.check(abs(options.get("minOpacity", 0) - 0.3) < 1e-9,
            "the minimum opacity is 0.3, so cold cells stay visible")
    gradient = options.get("gradient", {})
    h.equal(len(gradient), 4, "the custom gradient has four stops")
    h.equal([gradient.get(key) for key in ("0.2", "0.5", "0.8", "1.0")],
            ["blue", "lime", "orange", "red"], "and they run blue to red")
    h.check("max_val" not in options,
            "no max_val is passed: folium 0.19 removed it, which is why the weights carry the cap")

    h.contains(printed, "Prepared 22481 weighted grid points",
               "the run reports how many cells it will draw")
    h.contains(printed, "applied as bw_method=0.1462",
               "and prints the factor it derived from the bandwidth")
    h.contains(printed, "15 cells saturate the colour scale",
               "and how much of the map is at the cap")
    h.contains(printed, "output/advanced_traffic_kde_heatmap.html",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("gridded_kde.json", {
        "points": result["points"],
        "grid": [module.GRID_RESOLUTION, module.GRID_RESOLUTION],
        "grid_points": result["grid_points"],
        "bandwidth_degrees": module.KDE_BANDWIDTH,
        "bandwidth_metres": round(module.BANDWIDTH_METRES, 1),
        "spread_degrees": round(spread, 4),
        "bw_factor": round(result["bw_factor"], 4),
        "peak": [round(peak_lat, 4), round(peak_lon, 4)],
        "peak_density": round(result["peak_density"], 3),
        "cap": round(result["cap"], 3),
        "saturated": result["saturated"],
        "gradient": gradient,
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
