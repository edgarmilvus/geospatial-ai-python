"""Harness for exercise 2 — Svalbard to Reykjavik, flat versus round.

The exercise asks for the percentage error of treating degrees as a plane. The
harness pins the planar answer to the arithmetic of the two coordinate pairs, pins
the geodesic answer to the real separation of the two stations (about 2000 km),
and checks that the error has the sign the prose claims: a flat reading of degrees
*underestimates* the distance at high latitude.
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

# Reykjavik and Svalbard, as the exercise states them.
SVALBARD = (78.22, 15.64)
REYKJAVIK = (64.14, -21.94)


def main():
    h = Harness("exercise 2 (high-latitude distance)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_high_latitude_distance.py", "high_latitude")
    printed = log.getvalue()

    h.equal(module.station_a, SVALBARD, "the first station is Svalbard")
    h.equal(module.station_b, REYKJAVIK, "the second station is Reykjavik")

    # Shapely is fed (lon, lat), the order the plane expects: 37.58 degrees of
    # longitude and 14.08 of latitude, so Pythagoras gives 40.1311 degrees.
    expected_planar = math.hypot(REYKJAVIK[1] - SVALBARD[1], REYKJAVIK[0] - SVALBARD[0])
    h.close(module.planar_distance_degrees, expected_planar,
            "the planar distance is the diagonal of the degree difference", tol=1e-9)
    h.check(39.0 < module.planar_distance_degrees < 41.0,
            "the planar answer is about 40 degrees")

    # 1 degree of latitude is 111.32 km; of longitude at the mean latitude 71.18 N it
    # is 111.32 * cos(71.18) = 35.9 km. The listing uses that single factor for both.
    mean_lat = (SVALBARD[0] + REYKJAVIK[0]) / 2
    h.close(math.degrees(module.avg_lat_rad), mean_lat, "the mean latitude is 71.18 N", tol=1e-9)
    h.close(module.degree_to_km_factor, 111.32 * math.cos(math.radians(mean_lat)),
            "the conversion factor is 111.32 km times cos(mean latitude)", tol=1e-6)

    # The stations really are 2000 km apart on the ellipsoid; the flat reading of the
    # same two points, converted at 35.9 km per degree, gives only 1441 km.
    h.check(1990.0 <= module.true_geodesic_distance_km <= 2010.0,
            "the geodesic distance is 2000 km (got %.1f)" % module.true_geodesic_distance_km)
    h.check(1430.0 <= module.planar_distance_km_approx <= 1450.0,
            "the converted planar distance is 1441 km (got %.1f)"
            % module.planar_distance_km_approx)
    h.check(module.planar_distance_km_approx < module.true_geodesic_distance_km,
            "the planar method underestimates, by 559 km here")

    # Error = |planar - geodesic| / geodesic, so it is 27.9 per cent.
    error = abs(module.planar_distance_km_approx - module.true_geodesic_distance_km) \
        / module.true_geodesic_distance_km * 100
    h.close(module.error_percentage, error, "the error is the formula the book prints", tol=1e-9)
    h.check(25.0 <= module.error_percentage <= 30.0,
            "the error is 27.9 per cent (got %.2f)" % module.error_percentage)

    # Geodesic/planar ratio is the same 1.388 either way: the error is a property of
    # the latitude, not of the unit the answer is reported in.
    h.check(abs(module.true_geodesic_distance_km / module.planar_distance_km_approx
                - 1.388) < 0.01, "the true distance is 1.39 times the planar one")

    h.contains(printed, "1. Planar Distance (Degrees): 40.1311",
               "the listing prints the planar answer in degrees")
    h.contains(printed, "2. True Geodesic Distance (KM): 2000.05",
               "the listing prints the geodesic answer in kilometres")
    h.contains(printed, "Percentage Error (Planar vs. Geodesic): 27.94%",
               "the listing prints the error it was asked for")

    # The task statement in this folder publishes the two stations and stops there.
    starter = load_listing(FILES / "prompt_sketch_high_latitude.py", "starter_high_latitude")
    h.equal(starter.station_a, (78.22, 15.64), "the starter's station A is Svalbard")
    h.equal(starter.station_b, (64.14, -21.94), "the starter's station B is Reykjavik")

    h.write_json("high_latitude_distance.json", {
        "stations": {"A": list(SVALBARD), "B": list(REYKJAVIK)},
        "planar_degrees": round(module.planar_distance_degrees, 4),
        "planar_km_approx": round(module.planar_distance_km_approx, 2),
        "geodesic_km": round(module.true_geodesic_distance_km, 2),
        "error_percent": round(module.error_percentage, 2),
        "degree_to_km_at_mean_latitude": round(module.degree_to_km_factor, 4),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (high-latitude distance)", FILES).crash())
