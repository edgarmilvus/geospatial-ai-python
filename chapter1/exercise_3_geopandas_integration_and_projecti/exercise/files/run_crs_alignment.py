"""Harness for exercise 3 — two layers, two CRSs, one overlay.

The exercise's point is that a spatial operation is only legal once both frames
speak the same CRS. The harness checks the unification, then performs the overlay
the listing attempts, and checks that the intersection is a real geometry with a
non-zero area rather than an empty frame that merely did not raise.
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
    h = Harness("exercise 3 (CRS alignment)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_crs_alignment.py", "crs_alignment")
    printed = log.getvalue()

    import geopandas as gpd

    # The two input frames deliberately disagree: metres against degrees.
    h.equal(module.gdf_A.crs.to_epsg(), 3857, "frame A starts in Web Mercator")
    h.equal(module.gdf_B.crs.to_epsg(), 4326, "frame B starts in WGS 84")

    unified_a, unified_b = module.unify_crs([module.gdf_A, module.gdf_B], module.TARGET_CRS)
    h.equal(unified_a.crs.to_epsg(), module.TARGET_CRS, "frame A moved to the target")
    h.equal(unified_b.crs.to_epsg(), module.TARGET_CRS, "frame B moved to the target")
    h.check(unified_a.crs == unified_b.crs, "the two frames now compare equal")

    # 5070 is an equal-area projection, so the areas are comparable numbers.
    h.equal(module.TARGET_CRS, 5070, "the exercise picks the equal-area CONUS Albers")

    overlay = gpd.overlay(unified_a, unified_b, how="intersection")
    h.check(len(overlay) >= 1, "the intersection produces at least one feature")
    if len(overlay):
        h.check(overlay.geometry.area.iloc[0] > 0,
                "the intersection has an area, so the layers really overlap")

    # The source frames must not be mutated by the unification: to_crs returns
    # a new frame, and a helper that wrote into its argument would be a trap.
    h.equal(module.gdf_A.crs.to_epsg(), 3857, "frame A is unchanged after unification")
    h.equal(module.gdf_B.crs.to_epsg(), 4326, "frame B is unchanged after unification")

    h.contains(printed, "CRS Match Confirmed: True", "the listing confirms the match")
    h.contains(printed, "Resulting features:", "the listing reports the overlay result")

    h.write_json("crs_alignment.json", {
        "source": {"A": 3857, "B": 4326},
        "target": module.TARGET_CRS,
        "intersection_features": int(len(overlay)),
        "intersection_area_sq_m": float(overlay.geometry.area.iloc[0]) if len(overlay) else 0.0,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (CRS alignment)", FILES).crash())
