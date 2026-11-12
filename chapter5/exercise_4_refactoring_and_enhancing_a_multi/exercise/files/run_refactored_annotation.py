"""Harness for exercise 4 — the refactor, now on a GeoAxes.

The exercise rewrites `plt.*` calls as artists. With Cartopy there is one more fact to assert: the
axes is a UTM GeoAxes, so the marker's position is a projected coordinate and the 5 km box is
5 000 of the projection's metres. The harness checks the transform against pyproj, the artists on
the axes, and the box's geometry about that point.
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
    h = Harness("exercise 4 (refactored annotation layers)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_refactored_annotation_layers.py", "refactor")
    printed = log.getvalue()

    import cartopy.crs as ccrs
    from pyproj import Transformer

    ax = module.ax

    h.equal(type(ax).__name__, "GeoAxes", "the map is a GeoAxes")
    h.check(isinstance(ax.projection, ccrs.UTM), "its projection is ccrs.UTM")
    h.equal(ax.projection.utm_zone, "48N", "zone 48N, in metres")
    h.equal(len(module.land_wgs84), 7, "seven land features")
    h.equal(len(module.water_wgs84), 1, "one water feature")

    # The point of interest is a WGS 84 coordinate the listing projects with transform_point.
    reference = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True) \
        .transform(103.85, 1.35)
    h.close(module.poi_x, reference[0], "the port's easting matches pyproj", tol=1e-6)
    h.close(module.poi_y, reference[1], "and its northing", tol=1e-6)
    h.close(module.poi_x, 372_060.0, "the port lands at 372 060 m east", tol=1.0)
    h.close(module.poi_y, 149_246.0, "and 149 246 m north", tol=1.0)

    # The bounding box: 5 km by 5 km, because the projection is in metres. That is the whole
    # point of "5000 units" - the same number in degrees would be a fifth of the planet.
    h.equal(module.box_size_m, 5_000, "the annotation box is 5 km square")
    box = [p for p in ax.patches if p.__class__.__name__ == "Rectangle"][0]
    h.close(box.get_width(), 5_000.0, "the patch is 5 000 projection metres wide")
    h.close(box.get_height(), 5_000.0, "and 5 000 tall")
    h.close(box.get_x() + box.get_width() / 2, module.poi_x, "the box is centred on the port",
            tol=1e-6)
    h.close(box.get_y() + box.get_height() / 2, module.poi_y, "in both axes", tol=1e-6)

    # The object-model checks: titles on both levels, axis labels and round metric ticks.
    h.contains(ax.get_title(), "Regional Infrastructure", "the axes carries a title")
    h.contains(ax.figure._suptitle.get_text(), "Advanced Map Refactoring",
               "and the figure carries its own")
    h.equal(ax.get_xlabel(), "Easting (Meters)", "the axes is labelled in metres")
    h.equal(list(ax.get_xticks())[:3], [0, 200_000, 400_000], "the ticks are round eastings")
    legend = ax.get_legend()
    h.check(legend is not None, "a legend is attached to the axes")
    h.equal(len(legend.legend_handles), 2, "two handles: land and water")
    h.equal([text.get_text() for text in legend.get_texts()],
            ["Land Areas", "Water/Buffer"], "with the layer names the reader chose")

    # The annotation layer: two geometry layers plus the marker's scatter, and one callout.
    scatter = [c for c in ax.collections if c.__class__.__name__ == "PathCollection"]
    h.equal(len(scatter), 1, "one scatter collection carries the marker")
    annotations = [t for t in ax.texts if t.get_text() == "Critical Port Location"]
    h.equal(len(annotations), 1, "one callout is placed")
    # On a GeoAxes "data coordinates" are projection metres, and the annotation's transform is
    # Cartopy's composite one rather than the string "data" - so the anchor is what is checked.
    h.close(annotations[0].xy[0], module.poi_x,
            "the callout is anchored to the port's easting", tol=1e-6)
    h.close(annotations[0].xy[1], module.poi_y, "and to its northing", tol=1e-6)

    # The view is the book's 600 km window, in the projection's metres.
    x0, x1, y0, y1 = ax.get_extent(crs=ax.projection)
    h.close(x1 - x0, 600_000.0, "the map shows a 600 km window", tol=1.0)
    h.close(y1 - y0, 600_000.0, "square", tol=1.0)

    h.check(module.figure_path.exists(), "the figure was written")
    payload = module.figure_path.read_bytes()
    h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the figure is a PNG")
    h.check(40_000 < len(payload) < 3_000_000,
            "the PNG is a plausible size (got %d bytes)" % len(payload))

    h.contains(printed, "axes UTM (UTM zone 48N)", "the listing names the projection")
    h.contains(printed, "POI in the map CRS:", "the listing reports the projected port")

    h.write_json("refactored_annotation.json", {
        "axes_type": type(ax).__name__,
        "projection": "ccrs.UTM(zone=48)",
        "utm_zone": ax.projection.utm_zone,
        "layers": {"land": len(module.land_wgs84), "water": len(module.water_wgs84)},
        "poi_m": [round(module.poi_x, 1), round(module.poi_y, 1)],
        "box_m": module.box_size_m,
        "view_m": 600_000,
        "xticks": [int(v) for v in ax.get_xticks()],
        "legend_handles": len(legend.legend_handles),
        "figure_bytes": len(payload),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (refactored annotation layers)", FILES).crash())
