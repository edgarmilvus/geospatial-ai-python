"""Harness for exercise 3 — the nearest service centre, and the circle around the pair.

The exercise asks for three things and the harness checks that they belong to each
other: the nearest POI of five, the centre of the segment joining it to the incident,
and the radius that makes that centre the centre of the smallest circle holding both
points. That last one is the point of the exercise — the radius is half the measured
distance, and the check that proves it is that both points sit exactly on the circle.
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

INCIDENT = (500000, 4500000)
# The five POIs, in the order the listing defines them; the first is the nearest.
POIS = [(500100, 4500100), (500500, 4499000), (499500, 4500050),
        (501000, 4501000), (498000, 4490000)]


def main():
    h = Harness("exercise 3 (proximity assignment)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_proximity_assignment.py", "proximity_assignment")
    printed = log.getvalue()

    h.equal(module.TARGET_CRS.to_epsg(), 26910,
            "the plane is UTM zone 10N, so the units are metres")
    h.equal((module.incident_x, module.incident_y), INCIDENT, "the incident is at 500000/4500000")
    h.equal(len(module.poi_gs), 5, "five service centres are on the map")
    h.equal([(p.x, p.y) for p in module.poi_gs], POIS, "the five POIs are the documented ones")
    h.equal(module.poi_gs.crs.to_epsg(), 26910, "the POIs carry the projected CRS")

    # The vectorised distance call returns one number per POI: the harness checks it
    # agrees with the per-point distance, so a mis-shaped frame cannot pass silently.
    h.equal(len(module.distances), 5, "one distance per service centre")
    h.close(module.distances.iloc[1], math.hypot(500, 1000),
            "POI 2 is 500 m east and 1000 m south: 1118.03 m", tol=1e-6)
    h.equal(module.distances.idxmin(), 0, "the first POI is the nearest")

    # Nearest POI 1 is 100 m east and 100 m north: sqrt(2) * 100 = 141.42 m.
    h.close(module.min_distance, math.hypot(100, 100),
            "the nearest POI is 141.42 m away", tol=1e-6)
    h.close(module.min_distance, math.sqrt(2) * 100, "the diagonal of a 100 m square",
            tol=1e-9)
    h.equal((module.closest_poi.x, module.closest_poi.y), POIS[0], "POI 1, not POI 2")

    # The centroid of the segment is the midpoint, and half the distance is the
    # radius of the smallest circle through both points.
    h.close(module.center_x, 500050.0, "the zone centre sits halfway in easting")
    h.close(module.center_y, 4500050.0, "the zone centre sits halfway in northing")
    h.close(module.critical_radius, module.min_distance / 2, "the radius is half the distance",
            tol=1e-9)
    h.check(abs(module.critical_radius - 70.71) < 0.01,
            "the radius is 70.71 m (got %.2f)" % module.critical_radius)

    # The definition of that circle: both points are on it, and no smaller one holds
    # both. Distance from the centre to each point equals the radius.
    centre = module.center_of_zone
    h.close(centre.distance(module.incident), module.critical_radius,
            "the incident lies on the circle", tol=1e-6)
    h.close(centre.distance(module.closest_poi), module.critical_radius,
            "the nearest POI lies on the circle", tol=1e-6)
    h.close(module.connecting_line.length, 2 * module.critical_radius,
            "the segment is the diameter", tol=1e-6)
    h.check(module.connecting_line.length <= 200.0,
            "the critical zone needs no more than 141 m of travel")

    h.contains(printed, "Closest POI Found (Index 0): (500100, 4500100) m",
               "the listing names the nearest centre")
    h.contains(printed, "Minimum Required Proximity Radius: 70.71 meters",
               "the listing prints the radius")

    h.write_json("proximity_assignment.json", {
        "crs_epsg": module.TARGET_CRS.to_epsg(),
        "incident": list(INCIDENT),
        "poi_count": len(module.poi_gs),
        "distances_m": [round(float(d), 2) for d in module.distances],
        "closest_poi": [module.closest_poi.x, module.closest_poi.y],
        "distance_m": round(module.min_distance, 2),
        "centre": [module.center_x, module.center_y],
        "radius_m": round(module.critical_radius, 2),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (proximity assignment)", FILES).crash())
