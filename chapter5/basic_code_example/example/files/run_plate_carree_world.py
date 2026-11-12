"""Harness for the basic example — a GeoAxes whose projection matches the data.

The example is about agreement: a frame in WGS 84, a Cartopy `GeoAxes` created with
`projection=ccrs.PlateCarree()`, a labelled graticule and an extent in degrees. The harness checks
the axes' type and projection, the extent it reports, that the graticule really produced labels,
and that a PNG of a plausible size came out of the closed figure.
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
    h = Harness("basic example (Plate Carree world)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_plate_carree_world.py", "plate_carree")
    printed = log.getvalue()

    import cartopy.crs as ccrs

    world, ax = module.world, module.ax

    h.equal(world.crs.to_epsg(), 4326, "the data is WGS 84, as a GeoDataFrame from GPS would be")
    h.check(world.crs.is_geographic, "4326 is a geographic CRS: its units are degrees")
    h.equal(len(world), 58, "the land mask keeps 58 of the 96 cells")

    # The axes is the chapter's claim: a GeoAxes, and specifically a Plate Carree one.
    h.equal(type(ax).__name__, "GeoAxes", "plt.subplots(subplot_kw=...) built a GeoAxes")
    h.check(isinstance(ax.projection, ccrs.PlateCarree), "its projection is ccrs.PlateCarree()")
    from cartopy.mpl.geoaxes import GeoAxes as CartopyGeoAxes
    h.check(isinstance(ax, CartopyGeoAxes), "the object really is a cartopy GeoAxes")

    # The extent, asked for in the data's own CRS: the whole globe, pole to pole.
    extent = ax.get_extent(crs=ccrs.PlateCarree())
    h.equal(tuple(round(float(v), 6) for v in extent), (-180.0, 180.0, -90.0, 90.0),
            "the axes covers 180 W to 180 E and 90 S to 90 N")

    # Plate Carree leaves a degree where it found it, which is why the data needed no transform.
    x, y = ax.projection.transform_point(-120.0, 45.0, ccrs.PlateCarree())
    h.close(x, -120.0, "Plate Carree maps longitude to x unchanged", tol=1e-9)
    h.close(y, 45.0, "and latitude to y unchanged", tol=1e-9)

    # The graticule is Cartopy's: labels on the bottom and left only, drawn as degree text.
    gl = module.gl
    h.equal(gl.bottom_labels, True, "the graticule drew its bottom labels")
    h.equal(gl.top_labels, False, "and not the top ones - the book's aesthetic choice")
    h.equal(gl.right_labels, False, "nor the right ones")
    bottom = sorted(a.get_text() for a in gl.bottom_label_artists)
    left = sorted(a.get_text() for a in gl.left_label_artists)
    h.check(len(bottom) >= 5, "at least five longitude labels (%d)" % len(bottom))
    h.check(len(left) >= 3, "at least three latitude labels (%d)" % len(left))
    h.check(all(text.endswith(("°", "W", "E")) for text in bottom),
            "longitude labels are degrees with W or E")
    h.check(any(text.endswith("W") for text in bottom),
            "and the western ones say W, not a negative number")
    h.check(any("N" in text for text in left) and any("S" in text for text in left),
            "latitude labels say N and S")

    # Cells still measure 30 x 20 degrees, so the total is 34 800 square degrees - a number with
    # no unit, which is the next exercise's warning.
    bounds = world.geometry.bounds
    widths = bounds.maxx - bounds.minx
    heights = bounds.maxy - bounds.miny
    h.check(bool((widths == 30.0).all() and (heights == 20.0).all()),
            "each cell is 30 degrees wide and 20 tall")

    figure = module.figure_path
    h.check(figure.exists(), "the figure was written")
    payload = figure.read_bytes()
    h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the figure is a PNG")
    h.check(20_000 < len(payload) < 2_000_000,
            "the PNG is a plausible size (got %d bytes)" % len(payload))

    h.contains(printed, "Type: GeoAxes", "the listing reports the axes type")
    h.contains(printed, "Extent (degrees): (-180.0, 180.0, -90.0, 90.0)",
               "the listing reports the extent in the data's units")

    h.write_json("plate_carree_world.json", {
        "axes_type": type(ax).__name__,
        "projection": type(ax.projection).__name__,
        "projection_crs": "ccrs.PlateCarree()",
        "features": len(world),
        "crs_epsg": 4326,
        "bounds_degrees": [float(v) for v in world.total_bounds],
        "extent_degrees": [round(float(v), 3) for v in extent],
        "gridline_labels": {"bottom": len(bottom), "left": len(left)},
        "figure_bytes": len(payload),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("basic example (Plate Carree world)", FILES).crash())
