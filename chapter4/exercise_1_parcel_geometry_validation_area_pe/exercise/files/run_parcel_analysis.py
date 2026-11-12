"""Harness for exercise 1 — the parcel its starter block describes.

The folder holds the task's starter and the finished solution; the other three
exercises have their own folders, each with its own starter and harness. The
harness drives the answer, pins its three metrics to the pentagon the starter
defines, and checks the starter stayed a starter — a task that already had a
`land_parcel` in it would no longer be an exercise.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

STARTERS = ["01_parcel_metrics_starter.py"]


def main():
    h = Harness("exercise 1 (parcel metrics)", FILES)

    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "05_parcel_metrics_solution.py", "parcel_solution")
    printed = log.getvalue()

    parcel = module.land_parcel

    # The pentagon (10,20) (35,5) (50,30) (40,60) (20,50): shoelace area 1325,
    # boundary 143.92 units, centroid near (30.91, 32.04).
    h.equal(len(module.parcel_coords), 6, "five corners plus the repeated first")
    h.equal(module.parcel_coords[0], module.parcel_coords[-1], "the ring is closed")
    h.equal(parcel.geom_type, "Polygon", "the corners build a Polygon")
    h.check(parcel.is_valid, "the pentagon does not cross itself")
    h.close(parcel.area, 1325.0, "the pentagon covers 1325 square units", tol=0.01)
    h.check(abs(parcel.length - 143.92) < 0.01,
            "the boundary runs 143.92 units (got %.2f)" % parcel.length)
    h.close(parcel.centroid.x, 30.9119, "centroid easting", tol=0.0005)
    h.close(parcel.centroid.y, 32.0440, "centroid northing", tol=0.0005)

    # Outside is outside: a point beyond the far corner is not in the parcel, so the
    # centroid is a real interior point and not just the average of the corners.
    from shapely.geometry import Point
    h.check(parcel.contains(Point(30.9119, 32.0440)), "the centroid is inside the parcel")
    h.check(not parcel.contains(Point(5.0, 5.0)), "the origin is outside the parcel")

    # The custom exception is the exercise's contract: it exists, it is an Exception,
    # and the solution would raise it rather than print and carry on.
    h.check(hasattr(module, "InvalidGeoFeatureError"), "the custom error class is defined")
    h.check(issubclass(module.InvalidGeoFeatureError, Exception),
            "the custom error is an Exception")
    h.check(parcel.is_valid, "the valid input therefore does not raise it")

    # A starter is a task, not an answer: it defines its inputs and stops.
    for name in STARTERS:
        starter = load_listing(FILES / name, "starter_" + name.split("_")[0])
        h.check(not hasattr(starter, "land_parcel"),
                "%s leaves the construction to the reader" % name)
        h.check(not hasattr(starter, "unified_feature"),
                "%s leaves the aggregation to the reader" % name)

    h.contains(printed, "Feature Validation: SUCCESS (Geometry is valid)",
               "the listing reports the validation")
    h.contains(printed, "Total Parcel Area (sq units): 1325.00",
               "the area is printed to two decimals")
    h.contains(printed, "Geometric Centroid (X, Y): (30.9119, 32.0440)",
               "the centroid is printed to four decimals")

    h.write_json("parcel_analysis.json", {
        "vertices": len(module.parcel_coords),
        "area_sq_units": round(parcel.area, 2),
        "perimeter_units": round(parcel.length, 2),
        "centroid": [round(parcel.centroid.x, 4), round(parcel.centroid.y, 4)],
        "corner_mean": [round(sum(x for x, _ in module.parcel_coords[:-1]) / 5, 4),
                        round(sum(y for _, y in module.parcel_coords[:-1]) / 5, 4)],
        "valid": bool(parcel.is_valid),
        "starters": STARTERS,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (parcel metrics)", FILES).crash())
