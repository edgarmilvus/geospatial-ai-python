"""Harness for exercise 4 — the same parcel, two projections, one distortion.

The exercise measures what a projection costs. The harness recomputes the true
area from the geometry rather than trusting the printed one, then checks that the
formula returns the number the listing's own arithmetic implies, and that the two
projections really do disagree by orders of magnitude at this latitude.
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
    h = Harness("exercise 4 (projection distortion)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_distortion.py", "distortion")
    printed = log.getvalue()

    polar = module.gdf_polar
    h.equal(polar.crs.to_epsg(), 3413, "the parcel starts in the polar projection")
    h.check(polar.crs.is_projected, "the polar CRS is projected")

    # The polygon is 10 km x 10 km in metres, so the true area is 100 km2.
    true_area = polar.geometry.area.iloc[0]
    h.close(true_area, 100_000_000, "the true area is 10 000 m x 10 000 m", tol=1.0)

    distorted = polar.to_crs(epsg=3857)
    distorted_area = distorted.geometry.area.iloc[0]
    h.check(distorted_area > true_area,
            "Web Mercator inflates the parcel at this latitude")
    h.check(module.calculate_area_distortion(true_area, distorted_area) > 100,
            "the distortion is enormous, not a rounding difference")

    # The formula is the exercise's, so it must be right at the easy cases.
    h.close(module.calculate_area_distortion(100, 150), 50.0,
            "a 50 per cent inflation reports 50 per cent")
    h.close(module.calculate_area_distortion(100, 100), 0.0,
            "an unchanged area reports no distortion")
    h.close(module.calculate_area_distortion(100, 50), 50.0,
            "a halved area reports 50 per cent, not -50")

    h.contains(printed, "Percentage Distortion:", "the listing prints the percentage")
    h.contains(printed, "Projection Mismatch:", "the listing names the mismatch")

    h.write_json("distortion.json", {
        "true_area_sq_m": round(true_area, 2),
        "web_mercator_area_sq_m": round(distorted_area, 2),
        "percentage": round(module.calculate_area_distortion(true_area, distorted_area), 2),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (projection distortion)", FILES).crash())
