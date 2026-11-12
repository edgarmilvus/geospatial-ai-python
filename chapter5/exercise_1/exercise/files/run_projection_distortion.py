"""Harness for exercise 1 — the same 58 cells on three GeoAxes.

The exercise asks the reader to *see* distortion, and with Cartopy the three panels are three
projections rather than three reprojected frames. The harness checks the projection of each panel,
that an equal-area projection reproduces the ellipsoidal area, that Web Mercator triples it, that
the same longitude and latitude lands in three different places, and that the PNG exists.
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
    h = Harness("exercise 1 (projection distortion)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_projection_distortion_triptych.py", "triptych")
    printed = log.getvalue()

    import cartopy.crs as ccrs
    from pyproj import Geod

    world = module.world
    ax_plate, ax_eckert, ax_mercator = [panel[0] for panel in module.panels]

    h.equal(len(world), 58, "58 land cells")
    h.equal(len(module.panels), 3, "three panels")

    # Three GeoAxes, three projections, one frame in WGS 84.
    for ax, kind, label in ((ax_plate, ccrs.PlateCarree, "Plate Carree"),
                            (ax_eckert, ccrs.EckertIV, "Eckert IV"),
                            (ax_mercator, ccrs.CRS, "an EPSG projection")):
        h.equal(type(ax).__name__, "GeoAxes", "panel is a GeoAxes (%s)" % label)
        h.check(isinstance(ax.projection, kind), "its projection is %s" % label)
    h.check(ax_mercator.projection == ccrs.epsg(3857), "the third panel is Web Mercator")
    h.check(str(ax_plate.projection) != str(ax_eckert.projection),
            "the panels really are different projections")

    # A degree squared is not an area: 58 cells of 30 x 20 give 34 800 of them.
    h.close(module.area_deg2, 34_800.0, "34 800 square degrees, which measure nothing")

    # Eckert IV is equal-area, so its total must reproduce the ellipsoidal area - the strongest
    # check available, because it compares the projection against the Earth.
    geod = Geod(ellps="WGS84")
    true_area = 0.0
    for geometry in world.geometry:
        area, _ = geod.geometry_area_perimeter(geometry)
        true_area += abs(area)
    h.check(abs(module.area_eckert - true_area) / true_area < 0.01,
            "Eckert IV returns the ellipsoidal area within 1%% (%.3f vs %.3f million sq km)"
            % (module.area_eckert / 1e12, true_area / 1e12))

    # Mercator stretches the high latitudes: about 3x the equal-area total for these cells.
    ratio = module.area_mercator / module.area_eckert
    h.check(2.5 <= ratio <= 3.5, "Web Mercator triples the same cells (got %.2fx)" % ratio)

    # The extents, in each panel's own units.
    plate_extent = ax_plate.get_extent(crs=ccrs.PlateCarree())
    h.equal(tuple(round(float(v), 6) for v in plate_extent), (-180.0, 180.0, -90.0, 90.0),
            "the first panel covers the globe")
    merc_extent = ax_mercator.get_extent(crs=ax_mercator.projection)
    h.close(merc_extent[0], -20_037_508.34, "the Mercator panel starts at the 85th parallel",
            tol=0.01)
    h.close(merc_extent[1], 20_037_508.34, "and ends at it", tol=0.01)
    h.close(module.x_limit_3857, 20_037_508.34, "the listing records that limit", tol=0.01)

    # One longitude and latitude, three answers: the axes owns the projection.
    lon, lat = 10.0, 60.0
    plate_xy = ax_plate.projection.transform_point(lon, lat, ccrs.PlateCarree())
    eckert_xy = ax_eckert.projection.transform_point(lon, lat, ccrs.PlateCarree())
    merc_xy = ax_mercator.projection.transform_point(lon, lat, ccrs.PlateCarree())
    h.close(plate_xy[0], 10.0, "Plate Carree keeps the longitude", tol=1e-9)
    h.close(merc_xy[0], 1_113_194.9, "Mercator turns it into metres", tol=1.0)
    h.check(eckert_xy[1] != merc_xy[1], "Eckert IV and Mercator disagree about the northing")
    h.check(abs(eckert_xy[1] - 6_996_129.3) < 5.0,
            "Eckert IV puts (10 E, 60 N) at 6 996 129 m north")

    # The figure: three panels, one PNG.
    figure = module.figure_path
    h.check(figure.exists(), "the figure was written")
    payload = figure.read_bytes()
    h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the figure is a PNG")
    h.check(50_000 < len(payload) < 4_000_000,
            "a 150 dpi triptych is a sizeable PNG (got %d bytes)" % len(payload))

    h.contains(printed, "Mercator / Eckert IV: 2.98x", "the listing prints the distortion factor")
    h.contains(printed, "PlateCarree      extent", "the listing reports each panel's extent")

    h.write_json("projection_distortion.json", {
        "panels": ["PlateCarree", "EckertIV", "EPSG:3857"],
        "features": len(world),
        "area_sq_degrees": round(module.area_deg2, 2),
        "area_equal_area_sq_km": round(module.area_eckert / 1e6, 1),
        "area_mercator_sq_km": round(module.area_mercator / 1e6, 1),
        "ellipsoidal_area_sq_km": round(true_area / 1e6, 1),
        "mercator_over_equal_area": round(ratio, 3),
        "extent_plate_degrees": [round(float(v), 3) for v in plate_extent],
        "extent_mercator_m": [round(float(v), 1) for v in merc_extent],
        "point_10E_60N_m": {"eckert": [round(v, 1) for v in eckert_xy],
                            "mercator": [round(v, 1) for v in merc_xy]},
        "figure_bytes": len(payload),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (projection distortion)", FILES).crash())
