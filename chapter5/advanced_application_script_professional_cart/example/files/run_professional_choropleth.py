"""Harness for the advanced application script — a choropleth on a Mercator GeoAxes.

The script's claims are cartographic and now partly Cartopy's: the axes is an EPSG:3857 GeoAxes,
the districts are handed over in WGS 84 and the GeoAxes does the reprojection, the basemap is
drawn the same way (no tiles), and the scale bar is 50 000 metres of the projection. The harness
checks those facts, the area inflation they imply, and that a plausible PNG exists.
"""
import contextlib
import io
import math
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("advanced application (professional choropleth)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_professional_choropleth.py", "choropleth")
    printed = log.getvalue()

    import cartopy.crs as ccrs
    from pyproj import Geod

    districts, ax = module.districts, module.ax

    h.equal(districts.crs.to_epsg(), 4326, "the districts arrive in WGS 84")
    h.equal(len(districts), 11, "eleven districts are drawn")

    # The axes, and the projection it was constructed with.
    h.equal(type(ax).__name__, "GeoAxes", "the figure is a GeoAxes")
    h.check(isinstance(ax.projection, ccrs.CRS), "the axes carries a Cartopy projection")
    h.check(ax.projection == ccrs.epsg(3857), "and that projection is EPSG:3857")

    # Cartopy's forward transform against pyproj's: the same point, two libraries, one answer.
    from pyproj import Transformer
    lon, lat = module.DISTRICT_CENTRES[4]
    cx, cy = ax.projection.transform_point(lon, lat, ccrs.PlateCarree())
    px, py = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True) \
        .transform(lon, lat)
    h.close(cx, px, "Cartopy projects the district centre like pyproj does", tol=1e-6)
    h.close(cy, py, "in both coordinates", tol=1e-6)
    h.check(-13_900_000 < cx < -13_000_000, "the easting sits over California (%.0f)" % cx)

    # The extent, in metres for the axes and in degrees for the reader.
    x0, x1, y0, y1 = ax.get_extent(crs=ccrs.epsg(3857))
    h.check(0 < x1 - x0 < 1_200_000, "the view is about %d km wide" % ((x1 - x0) / 1000))
    h.check(0 < y1 - y0 < 1_200_000, "and %d km tall" % ((y1 - y0) / 1000))
    deg_extent = ax.get_extent(crs=ccrs.PlateCarree())
    h.check(35.0 < deg_extent[2] < 38.0 and 39.0 < deg_extent[3] < 42.0,
            "the view covers 36-40 N, in degrees")

    # Density is drawn from a seeded generator, so the values are reproducible: 80 to 4 200.
    density = districts["Population_Density"]
    h.check(int(density.min()) >= 80 and int(density.max()) <= 4_200,
            "density values stay in the seeded 80-4200 band")

    # The metric column needs a projection: Web Mercator inflates area by 1/cos(latitude)^2,
    # about 1.61 at 38 N, so the projected total is 61% larger than the ellipsoidal one.
    geod = Geod(ellps="WGS84")
    true_area = 0.0
    for geometry in districts.geometry:
        area, _ = geod.geometry_area_perimeter(geometry)
        true_area += abs(area)
    projected_area = districts["Area_km2"].sum() * 1e6
    inflation = projected_area / true_area
    expected = 1.0 / math.cos(math.radians(38.0)) ** 2
    h.check(abs(inflation - expected) < 0.06,
            "3857 inflates this region by 1/cos(38)^2 = %.2f (got %.2f)" % (expected, inflation))
    h.check(100_000 < projected_area / 1e6 < 200_000,
            "the districts cover {:,.0f} sq km of projection".format(projected_area / 1e6))

    # Three geometry artists: water, land, districts. The basemap is in the same call path as
    # the data, so it is projected by the same GeoAxes - the job contextily's tiles would do.
    h.equal(len(ax.collections), 3, "two basemap layers and one choropleth layer")
    h.equal(len(ax.artists), 1, "one scale bar is attached to the axes")
    inner = ax.artists[0].size_bar.get_children()[0]
    h.close(inner.get_width(), 50_000.0, "the bar is 50 000 projected metres long")
    h.equal(ax.artists[0].txt_label.get_text(), "50 km", "and it is labelled 50 km")
    h.equal(module.SCALE_BAR_M, 50_000, "the constant says 50 km")

    h.equal(module.custom_cmap.N, 256, "the colour ramp has 256 stops")
    h.equal(len(ax.figure.axes), 2, "the map and its colour bar axes")

    figure = module.figure_path
    h.check(figure.exists(), "the figure was written")
    payload = figure.read_bytes()
    h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the figure is a PNG")
    h.check(100_000 < len(payload) < 5_000_000,
            "a 300 dpi choropleth is a large PNG (got %d bytes)" % len(payload))

    h.contains(printed, "Type: GeoAxes", "the listing reports the axes type")
    h.contains(printed, "Scale bar: 50,000 m of the projection", "the listing reports the bar")

    h.write_json("professional_choropleth.json", {
        "axes_type": type(ax).__name__,
        "projection": "EPSG:3857 (ccrs.epsg(3857))",
        "districts": len(districts),
        "crs": {"data": 4326, "axes": 3857},
        "projected_area_sq_km": round(projected_area / 1e6, 1),
        "true_area_sq_km": round(true_area / 1e6, 1),
        "mercator_inflation": round(inflation, 3),
        "density_range": [int(density.min()), int(density.max())],
        "extent_metres": [round(float(v), 0) for v in (x0, x1, y0, y1)],
        "extent_degrees": [round(float(v), 2) for v in deg_extent],
        "district_5_projected_m": [round(float(cx), 1), round(float(cy), 1)],
        "scale_bar_m": module.SCALE_BAR_M,
        "figure_bytes": len(payload),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("advanced application (professional choropleth)", FILES).crash())
