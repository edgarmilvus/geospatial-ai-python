"""Harness for exercise 2 — a scale bar and a north arrow on a UTM GeoAxes.

The exercise hands the reader two helpers and a projected map. With Cartopy the projection is the
axes' own, so the checks are: the GeoAxes is UTM 17N, the graticule produced labels, the bar's four
segments add up to 150 000 metres of the projection, the bar starts where the helper says, and the
north arrow is anchored in axes coordinates rather than in metres.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

TARGET_KM = 150


def main():
    h = Harness("exercise 2 (scale bar and north arrow)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_scale_bar_north_arrow.py", "scale_bar")
    printed = log.getvalue()

    import cartopy.crs as ccrs

    gdf, ax = module.gdf, module.ax

    h.equal(gdf.crs.to_epsg(), 4326, "the regions arrive in WGS 84")
    h.equal(len(gdf), 6, "six regions are drawn")

    # The axes is a GeoAxes whose projection is UTM zone 17N, so its units are metres.
    h.equal(type(ax).__name__, "GeoAxes", "the map is a GeoAxes")
    h.check(isinstance(ax.projection, ccrs.UTM), "its projection is ccrs.UTM")
    h.equal(ax.projection.utm_zone, "17N", "zone 17N, the one the exercise names")
    h.check(ax.projection == ccrs.UTM(zone=17), "the projection compares equal to ccrs.UTM(17)")

    # Cartopy's forward transform against pyproj's, for the first region's centre.
    from pyproj import Transformer
    lon, lat = module.CENTRES[0]
    cx, cy = ax.projection.transform_point(lon, lat, ccrs.PlateCarree())
    px, py = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True).transform(lon, lat)
    h.close(cx, px, "Cartopy and pyproj agree on the easting", tol=1e-6)
    h.close(cy, py, "and on the northing", tol=1e-6)

    # The map view, in metres: about 1 000 km by 600 km of zone 17N.
    x0, x1, y0, y1 = ax.get_extent(crs=ax.projection)
    h.check(0 < x1 - x0 < 1_500_000, "the view is %d km wide" % ((x1 - x0) / 1000))
    h.check(0 < y1 - y0 < 1_000_000, "and %d km tall" % ((y1 - y0) / 1000))

    # The graticule: Cartopy's, with labels, on the bottom and left only.
    gl = module.gl
    h.equal(gl.bottom_labels, True, "the graticule drew its bottom labels")
    h.equal(gl.top_labels, False, "and not the top ones")
    h.check(len(gl.bottom_label_artists) >= 4,
            "at least four longitude labels (%d)" % len(gl.bottom_label_artists))
    h.check(len(gl.left_label_artists) >= 4,
            "at least four latitude labels (%d)" % len(gl.left_label_artists))

    # The bar the listing drew: start and end come back from the helper, in metres.
    drawn = module.bar_end - module.bar_start
    h.close(drawn, TARGET_KM * 1000, "the bar spans 150 000 units of the projection", tol=1e-6)

    rects = [p for p in ax.patches if p.__class__.__name__ == "Rectangle"]
    h.equal(len(rects), 4, "the bar is drawn as four segments")
    widths = [p.get_width() for p in rects]
    h.check(all(abs(w - 37_500.0) < 1e-6 for w in widths), "each segment is 37.5 km wide")
    h.close(sum(widths), 150_000.0, "the segments add up to the claimed distance")
    h.equal(rects[0].get_facecolor()[:3], (0.0, 0.0, 0.0), "the first segment is black")
    h.equal(rects[1].get_facecolor()[:3], (1.0, 1.0, 1.0), "the second is white")

    # The helper is reusable on another metric axes.
    import matplotlib.pyplot as plt
    fig2, ax2 = plt.subplots()
    ax2.set_xlim(0, 500_000)
    ax2.set_ylim(0, 500_000)
    start_50, end_50 = module.draw_scale_bar(ax2, target_km=50, location=(0.1, 0.05))
    h.close(end_50 - start_50, 50_000.0, "a 50 km bar is 50 000 units long", tol=1e-6)
    h.close(start_50, 50_000.0, "it starts 10% in from the left edge", tol=1e-6)
    plt.close(fig2)

    # The north arrow: a label and an annotation, both in axes coordinates.
    labels = [t.get_text() for t in ax.texts]
    h.contains(" ".join(labels), "N", "the arrow carries its label")
    arrows = [t for t in ax.texts if t.get_text() == ""]
    h.check(len(arrows) >= 1, "the arrow body is an annotation with no text")
    if arrows:
        arrow = arrows[0]
        h.equal(str(arrow.xycoords), "axes fraction",
                "the arrow is placed in axes coordinates, not in metres")
        h.check(0.0 <= arrow.xy[1] <= 1.0,
                "the arrow head falls inside the axes (y = %.2f)" % arrow.xy[1])

    figure = module.figure_path
    h.check(figure.exists(), "the figure was written")
    payload = figure.read_bytes()
    h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the figure is a PNG")
    h.check(20_000 < len(payload) < 2_000_000,
            "the PNG is a plausible size (got %d bytes)" % len(payload))

    h.contains(printed, "Type: GeoAxes", "the listing reports the axes type")
    h.contains(printed, "axes UTM (UTM 17N)", "the listing names the projection")
    h.contains(printed, "Bar length in data units: 150,000 m",
               "the listing reports the measured bar")

    h.write_json("scale_bar_north_arrow.json", {
        "axes_type": type(ax).__name__,
        "projection": "ccrs.UTM(zone=17)",
        "utm_zone": ax.projection.utm_zone,
        "regions": len(gdf),
        "target_km": TARGET_KM,
        "bar_units": round(drawn, 1),
        "segments": [round(w, 1) for w in widths],
        "extent_metres": [round(float(v), 0) for v in (x0, x1, y0, y1)],
        "gridline_labels": {"bottom": len(gl.bottom_label_artists),
                            "left": len(gl.left_label_artists)},
        "algoma_projected_m": [round(float(cx), 1), round(float(cy), 1)],
        "figure_bytes": len(payload),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (scale bar and north arrow)", FILES).crash())
