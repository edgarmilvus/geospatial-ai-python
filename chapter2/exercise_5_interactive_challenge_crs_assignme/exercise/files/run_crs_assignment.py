"""Harness for chapter 2, exercise 5 — the frame before and after set_crs.

The point of the exercise is the state transition, so the harness checks both
ends: the layer starts with no CRS and cannot be compared with anything, and it
ends with EPSG:4326 and projects to the expected Web Mercator metres. Those
metres are a fact about longitude -118.25, not about this machine.
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
    h = Harness("chapter 2 exercise 5 (CRS assignment)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_assign_crs.py", "ch2_crs")
    printed = log.getvalue()

    assigned = module.raw_points_gdf
    projected = module.projected

    # After the repair the layer declares WGS 84.
    h.check(assigned.crs is not None, "the layer ends with a CRS")
    h.equal(assigned.crs.to_epsg(), 4326, "the assigned CRS is EPSG:4326")
    h.check(assigned.crs.is_geographic, "EPSG:4326 is geographic, not projected")

    # Three points, and the coordinates were never reprojected — set_crs labels,
    # it does not move anything.
    h.equal(len(assigned), 3, "three boundary points were read")
    h.close(assigned.geometry.iloc[0].x, -118.25, "the first point keeps its longitude", tol=1e-9)
    h.close(assigned.geometry.iloc[0].y, 34.05, "the first point keeps its latitude", tol=1e-9)

    # The payoff: only now can to_crs() produce metres.
    h.equal(projected.crs.to_epsg(), 3857, "the projected copy is in EPSG:3857")
    h.check(projected.crs.is_projected, "EPSG:3857 is a projected system")
    h.close(projected.geometry.iloc[0].x, -13163530.0,
            "longitude -118.25 is about -13 163 530 m in Web Mercator", tol=5.0)
    h.close(projected.geometry.iloc[0].y, 4035518.0,
            "latitude 34.05 is about 4 035 518 m in Web Mercator", tol=5.0)

    # The source file really existed, so this was an ingestion and not a dict.
    h.check(module.POINTS_FILE.exists(), "boundary_points.geojson was written to output/")

    h.contains(printed, "2. Initial CRS: None", "the listing prints the missing CRS")
    h.contains(printed, "   Diagnostic: CRS is undefined. Manual assignment is required.",
               "the listing diagnoses the missing CRS")
    h.contains(printed, "4. Final Assigned CRS: EPSG:4326",
               "the listing prints the repaired CRS")

    h.write_json("crs_assignment.json", {
        "points": len(assigned),
        "crs_before": None,
        "crs_after": assigned.crs.to_string(),
        "epsg_after": assigned.crs.to_epsg(),
        "first_point_lonlat": [assigned.geometry.iloc[0].x, assigned.geometry.iloc[0].y],
        "first_point_web_mercator": [round(projected.geometry.iloc[0].x, 2),
                                     round(projected.geometry.iloc[0].y, 2)],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 exercise 5 (CRS assignment)", FILES).crash())
