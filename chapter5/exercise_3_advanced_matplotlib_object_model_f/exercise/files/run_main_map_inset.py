"""Harness for exercise 3 — two GeoAxes, two projections, one locator box.

The exercise's difficulty is the coordinate question, and Cartopy moves it from the data to the
axes: the main map is an Albers GeoAxes, the inset an azimuthal one, and the locator box is the
inset's extent converted with `transform_points` — the same operation the book performed with
`to_crs` on a GeoSeries, done in the projection space the axes draw in.
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
    h = Harness("exercise 3 (main map and inset)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_main_map_with_inset.py", "inset")
    printed = log.getvalue()

    import cartopy.crs as ccrs
    import numpy as np

    ax_main, ax_inset = module.ax_main, module.ax_inset

    # Two GeoAxes, two different projections: that is the exercise.
    h.equal(type(ax_main).__name__, "GeoAxes", "the main map is a GeoAxes")
    h.equal(type(ax_inset).__name__, "GeoAxes", "the inset is a GeoAxes too")
    h.check(isinstance(ax_main.projection, ccrs.AlbersEqualArea),
            "the main projection is an Albers Equal Area")
    h.check(isinstance(ax_inset.projection, ccrs.AzimuthalEquidistant),
            "the inset is an azimuthal equidistant projection")
    h.check(str(ax_main.projection) != str(ax_inset.projection),
            "the two panels really are in different projections")

    h.equal(len(module.main_data), 14, "fourteen features on the main map")
    h.equal(len(module.inset_data), 3, "three islands in the inset")
    h.equal(ax_main.figure, ax_inset.figure, "both axes live in one figure")

    # The locator box: the inset's extent, converted into the main projection.
    box_w, box_h = module.width_main, module.height_main
    h.check(box_w > 0 and box_h > 0, "the locator box has a positive width and height")
    h.check(1_000_000 < box_w < 2_000_000, "the box is %d km wide" % (box_w / 1000))
    h.check(abs(box_w * box_h / 1e6 - 1_359_291) < 400_000,
            "the box covers about 1.4 million sq km (got %.0f)" % (box_w * box_h / 1e6))

    # The conversion is Cartopy's, and it must agree with pyproj's for the same corner.
    from pyproj import Transformer
    ex0, ex1, ey0, ey1 = ax_inset.get_extent(crs=ax_inset.projection)
    transformer = Transformer.from_crs(ax_inset.projection.proj4_init,
                                       ax_main.projection.proj4_init, always_xy=True)
    px, py = transformer.transform(ex0, ey0)
    corners = ax_main.projection.transform_points(ax_inset.projection,
                                                  np.array([ex0]), np.array([ey0]))
    h.close(corners[0, 0], px, "Cartopy converts the inset corner like pyproj does", tol=1e-6)
    h.close(corners[0, 1], py, "in both coordinates", tol=1e-6)

    # The box has to touch the continent, or the inset locates nothing.
    import shapely.geometry as sgeom
    locator = sgeom.box(module.xmin_main, module.ymin_main,
                        module.xmax_main, module.ymax_main)
    # The box is in Albers metres, so the land has to be projected before they can be compared.
    land_in_main = module.main_data.to_crs(module.CRS_MAIN.proj4_init).union_all()
    h.check(locator.intersects(land_in_main), "the locator box overlaps the mapped land")

    # The two axes as artists: a main axes with a patch, an inset placed in figure fractions.
    h.equal(len(ax_main.figure.axes), 2, "the figure holds exactly two axes")
    boxes = [p for p in ax_main.patches if p.__class__.__name__ == "Rectangle"]
    h.equal(len(boxes), 1, "one locator rectangle on the main map")
    h.equal(boxes[0].get_linestyle(), "--", "drawn dashed, so it reads as an annotation")
    inset_position = ax_inset.get_position()
    h.check(0.5 < inset_position.x0 < 0.8 and 0.05 < inset_position.y0 < 0.3,
            "the inset sits in the lower right, in figure fractions")

    # A labelled graticule on the main map.
    gl = module.gl_main
    h.equal(gl.bottom_labels, True, "the main map's graticule drew bottom labels")
    h.check(len(gl.bottom_label_artists) >= 2 and len(gl.left_label_artists) >= 2,
            "with at least two labels per used edge (%d, %d)"
            % (len(gl.bottom_label_artists), len(gl.left_label_artists)))

    h.check(module.figure_path.exists(), "the figure was written")
    payload = module.figure_path.read_bytes()
    h.check(payload[:8] == b"\x89PNG\r\n\x1a\n", "the figure is a PNG")
    h.check(50_000 < len(payload) < 4_000_000,
            "the PNG is a plausible size (got %d bytes)" % len(payload))

    h.contains(printed, "Main:  AlbersEqualArea", "the listing names the main projection")
    h.contains(printed, "Inset: AzimuthalEquidistant", "and the inset's")

    h.write_json("main_map_with_inset.json", {
        "axes": {"main": type(ax_main.projection).__name__,
                 "inset": type(ax_inset.projection).__name__},
        "features": {"main": len(module.main_data), "inset": len(module.inset_data)},
        "inset_extent_m": [round(float(v), 0) for v in (ex0, ex1, ey0, ey1)],
        "locator_box_m": {"width": round(box_w, 0), "height": round(box_h, 0),
                          "area_sq_km": round(box_w * box_h / 1e6, 0)},
        "figure_bytes": len(payload),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (main map and inset)", FILES).crash())
