"""Harness for the basic example — an L-shaped parcel measured three ways.

The listing's whole claim is that the three attributes agree with the geometry the
vertex list describes: 75 square units (two 5 x 5 squares), a 40-unit boundary
(ten edges of five, plus the two long ones) and a centroid at five sixths of the
bounding box. The harness checks the geometry, not the printout, and only then
checks that the printout carries the same numbers.
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
    h = Harness("basic example (irregular parcel)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_irregular_parcel_metrics.py", "irregular_parcel")
    printed = log.getvalue()

    parcel = module.land_parcel

    # The vertex list is the L: a 10 x 5 rectangle with a 5 x 5 bite taken out of the
    # top-right corner, so 50 + 25 square units.
    h.equal(len(module.parcel_coords), 7, "the ring arrives closed: seven vertices")
    h.equal(module.parcel_coords[0], module.parcel_coords[-1],
            "the first and last vertex are the same point")
    h.equal(parcel.geom_type, "Polygon", "the vertices build a Polygon")
    h.check(parcel.is_valid, "the ring does not cross itself")
    h.close(parcel.area, 75.0, "two 5 x 5 squares: 50 + 25 square units")
    h.equal(round(parcel.area, 2), 75.0, "the area is exact, not an approximation")

    # Boundary: 10 + 5 + 5 + 5 + 5 + 10 = 40 units, i.e. the L is the 50-unit square
    # with a 5-unit corner removed and two 5-unit edges added.
    h.close(parcel.length, 40.0, "the boundary runs 40 units")

    # The centroid of the two squares: (10*5*(5) + 5*5*(2.5)) / 75 = 4.1666...
    h.close(parcel.centroid.x, 25 / 6, "centroid easting is 25/6", tol=1e-9)
    h.close(parcel.centroid.y, 25 / 6, "centroid northing is 25/6", tol=1e-9)
    h.check(parcel.contains(parcel.centroid), "the centroid falls inside the parcel")

    # The listing must also say it: a reader learns the numbers from the printout.
    h.contains(printed, "Geospatial Feature Analysis: Irregular Parcel",
               "the listing announces the analysis")
    h.contains(printed, "2. Calculated Area (units²): 75.00", "area printed with two decimals")
    h.contains(printed, "3. Calculated Perimeter (units): 40.00",
               "perimeter printed with two decimals")
    h.contains(printed, "POINT (4.166666666666667 4.166666666666667)",
               "centroid printed as a WKT point")
    h.contains(printed, "POLYGON ((0 0, 10 0, 10 5, 5 5, 5 10, 0 10, 0 0))",
               "the ring is printed as it was defined")

    h.write_json("parcel_metrics.json", {
        "vertices": len(module.parcel_coords),
        "area_sq_units": round(parcel.area, 4),
        "perimeter_units": round(parcel.length, 4),
        "centroid": [round(parcel.centroid.x, 6), round(parcel.centroid.y, 6)],
        "valid": bool(parcel.is_valid),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("basic example (irregular parcel)", FILES).crash())
