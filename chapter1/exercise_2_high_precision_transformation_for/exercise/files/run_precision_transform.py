"""Harness for exercise 2 — four corners, one bulk transformation, one distance.

The exercise asks for three things at once: pick the UTM zone from the data, move
every point in one call, and prove the result by measuring a known edge. The
harness checks the zone, the shape and precision of the output, and the measured
distance between the two top corners against the ground truth the coordinates
were built from.
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
    h = Harness("exercise 2 (precision transformation)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_precision_transform.py", "precision_transform")
    printed = log.getvalue()

    result = module.transform_roi_to_utm(module.roi_wgs84)

    # San Francisco is west of -120, which is UTM zone 10 north; the exercise's
    # own helper must produce that code, not a hard-coded one.
    h.equal(module.get_utm_epsg(-122.41, 37.77), 32610,
            "the helper derives UTM zone 10N from the longitude")
    h.equal(module.get_utm_epsg(-47.93, -15.78), 32723,
            "south of the equator the helper adds the 327 prefix")
    h.equal(result["target_epsg"], 32610, "the transform reports the zone it chose")

    points = result["transformed_coordinates"]
    h.equal(len(points), 4, "all four corners survive the bulk transformation")
    h.check(all(len(point) == 2 for point in points),
            "each corner is an (easting, northing) pair")

    eastings = [point[0] for point in points]
    northings = [point[1] for point in points]
    # UTM 10N puts this longitude near 550 km east and this latitude near
    # 4 180 km north. A lat/lon pair left unswapped lands outside both ranges.
    h.check(all(400_000 < value < 700_000 for value in eastings),
            "eastings land where zone 10N puts them")
    h.check(all(4_000_000 < value < 4_300_000 for value in northings),
            "northings land where zone 10N puts them")
    h.check(all(round(value, 3) == value for point in points for value in point),
            "every coordinate is rounded to three decimals")

    # The ROI is a 0.01 degree box. At this latitude that is about 880 m on the
    # top edge, which is the number the listing prints as its verification.
    from math import hypot
    distance = hypot(points[1][0] - points[0][0], points[1][1] - points[0][1])
    h.check(870 < distance < 890,
            "the transformed top edge measures about 880 m (%0.3f)" % distance)

    h.contains(printed, "Target UTM EPSG: 32610", "the listing prints the chosen zone")
    h.contains(printed, "Calculated Distance:", "the listing prints the verification distance")

    h.write_json("utm_transform.json", {
        "target_epsg": result["target_epsg"],
        "points": points,
        "top_edge_metres": round(distance, 3),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (precision transformation)", FILES).crash())
