"""Harness for exercise 5 — the scale bar that picks its own number, on a UTM GeoAxes.

The exercise is an algorithm, so the harness tests it as one: the nice-number search must land in
the 20-30% window, must never overshoot the map, and must keep working across four orders of
magnitude of zoom. Two facts are Cartopy's: the axes is a UTM GeoAxes, and its extent is set in the
projection's metres, so `ax.get_xlim()` is what the search reads.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 5 (dynamic scale and grid)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_dynamic_scale_and_grid.py", "dynamic_scale")
    printed = log.getvalue()

    import cartopy.crs as ccrs

    ax = module.ax  # the wide view: the last figure the listing drew

    h.equal(type(ax).__name__, "GeoAxes", "the map is a GeoAxes")
    h.check(isinstance(ax.projection, ccrs.UTM), "its projection is ccrs.UTM")
    h.equal(ax.projection.utm_zone, "17N", "zone 17N, whose data units are metres")

    find = module.find_optimal_nice_number

    # The two extents the listing draws, and the third width the prose quotes.
    h.check(abs(find(150_000) - 25.0) < 1e-9, "a 150 km view gets a 25 km bar")
    h.check(abs(find(800_000) - 200.0) < 1e-9, "an 800 km view gets a 200 km bar")
    h.check(abs(find(40_000) - 10.0) < 1e-9, "a 40 km view gets a 10 km bar")

    # Nice numbers only: 1, 2, 2.5 or 5 times a power of ten, in kilometres.
    for width in (60_000, 150_000, 800_000, 2_500_000, 10_000_000):
        km = find(width)
        h.check(km > 0 and round(km, 6) == km,
                "%.0f m gets a finite choice (%.3f km)" % (width, km))

    # The property the exercise is about: the bar never swallows the map. Swept over three
    # orders of magnitude, every bar stays between a tenth and a third of the width.
    widths = [int(10 ** (3 + step * 0.25)) for step in range(21)]
    ratios = [find(w) * 1000.0 / w for w in widths]
    h.check(min(ratios) >= 0.10,
            "no bar is shorter than a tenth of the map (min %.3f)" % min(ratios))
    h.check(max(ratios) <= 0.30,
            "no bar is longer than a third of the map (max %.3f)" % max(ratios))
    h.check(all(r > 0 for r in ratios), "every width gets a usable bar")

    # The two figures, and the bars in them.
    h.check(abs(module.L_km - 25.0) < 1e-9, "the local view's bar is 25 km")
    h.check(abs(module.L_km_2 - 200.0) < 1e-9, "the wide view's bar is 200 km")

    segments = [p for p in ax.patches if p.__class__.__name__ == "Rectangle"]
    h.equal(len(segments), 4, "the last bar is drawn as four segments")
    total = sum(p.get_width() for p in segments)
    h.close(total, 200_000.0, "and its segments add up to 200 km", tol=1.0)

    # The view and the grid, both in the projection's metres: round ticks, 100 km apart.
    x0, x1, y0, y1 = ax.get_extent(crs=ax.projection)
    h.close(x1 - x0, 800_000.0, "the wide view is 800 km across", tol=1.0)
    h.equal(int(ax.get_xticks()[1] - ax.get_xticks()[0]), 100_000,
            "the wide view's grid runs on a 100 km interval")
    h.check(all(tick % 100_000 == 0 for tick in ax.get_xticks()),
            "and every tick is a round easting")

    for name, path in (("local", module.figure_local), ("wide", module.figure_wide)):
        h.check(path.exists(), "the %s figure was written" % name)
        payload = path.read_bytes()
        h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the %s figure is a PNG" % name)
        h.check(20_000 < len(payload) < 2_000_000,
                "the %s PNG is a plausible size (%d bytes)" % (name, len(payload)))

    h.contains(printed, "Local view: 150,000 m wide -> bar of 25 km",
               "the listing reports the local decision")
    h.contains(printed, "Wide view:  800,000 m wide -> bar of 200 km", "and the wide one")

    h.write_json("dynamic_scale.json", {
        "axes_type": type(ax).__name__,
        "projection": "ccrs.UTM(zone=17)",
        "utm_zone": ax.projection.utm_zone,
        "extents_m": [150_000, 800_000],
        "bars_km": [module.L_km, module.L_km_2],
        "bar_ratio_sweep": {"min": round(min(ratios), 3), "max": round(max(ratios), 3),
                            "widths": len(widths)},
        "grid_interval_m": {"local": 50_000, "wide": 100_000},
        "extent_metres": [round(float(v), 0) for v in (x0, x1, y0, y1)],
        "segments_wide": len(segments),
        "segment_total_m": round(total, 1),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (dynamic scale and grid)", FILES).crash())
