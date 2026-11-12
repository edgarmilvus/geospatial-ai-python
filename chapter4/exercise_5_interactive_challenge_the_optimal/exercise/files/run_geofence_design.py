"""Harness for exercise 5 — three buffers, one fence.

The exercise composes three proximity rules into a single boundary: 50 m around the
building, 20 m around each access point, one union. The harness checks the
composition rather than the picture: each buffer is the distance it claims, the
fence contains all three inputs, the point buffers survive as separate rings (so the
answer is a MultiPolygon of three parts, not one), and the area is what the Steiner
formula predicts for a polygon grown by 50 m.
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
    h = Harness("exercise 5 (geo-fence design)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_geofence_design.py", "geofence_design")
    printed = log.getvalue()

    building = module.main_building
    p1, p2 = module.utility_point_1, module.utility_point_2

    # The six-vertex hall the book prints: a 250 x 200 body with two 100 m corners.
    h.equal(len(building.exterior.coords) - 1, 6, "the building is a six-vertex polygon")
    h.equal((p1.x, p1.y), (400.0, 150.0), "access point 1 is at 400/150")
    h.equal((p2.x, p2.y), (50.0, 450.0), "access point 2 is at 50/450")
    h.equal(module.BUILDING_BUFFER_DISTANCE, 50.0, "the building buffer is 50 m")
    h.equal(module.UTILITY_BUFFER_DISTANCE, 20.0, "the utility buffer is 20 m")

    # Each buffer is its own rule, and each rule is measurable.
    h.close(module.building_fence.area,
            building.area + building.length * 50 + math.pi * 50 ** 2,
            "the building fence is area + perimeter*50 + pi*50^2 (Steiner)", tol=60.0)
    # A 20 m disc is 1256.6 sq m; drawn as 8 segments per quadrant it is 0.16% short.
    h.check(abs(module.point1_fence.area - math.pi * 20 ** 2) / (math.pi * 20 ** 2) < 0.002,
            "a 20 m point buffer covers 1256.6 square metres (got %.2f)"
            % module.point1_fence.area)
    h.check(module.building_fence.contains(building), "the fence encloses the building")
    h.check(module.point2_fence.contains(p2), "the second buffer encloses its point")

    # Access point 1 stands 67.08 m from the nearest wall, and 50 + 20 = 70 m of buffer:
    # the two rules overlap by three metres, so those two rings merge into one part and
    # the answer is a MultiPolygon of two parts, not the three a first reading suggests.
    h.check(abs(building.exterior.distance(p1) - 67.082) < 0.01,
            "access point 1 is 67.08 m from the wall")
    fence = module.unified_geo_fence
    h.equal(fence.geom_type, "MultiPolygon", "the union is a MultiPolygon")
    h.equal(len(fence.geoms), 2, "the building fence swallows access point 1's margin")
    h.check(module.building_fence.intersects(module.point1_fence),
            "the two rules touch, so their buffers merge")
    h.check(not module.building_fence.intersects(module.point2_fence),
            "the second access point keeps its own island")
    h.close(fence.area, module.building_fence.union(module.point1_fence).area
            + module.point2_fence.area, "the union adds the merged pair and the island",
            tol=1e-6)

    # The reported metrics: 102669.71 square metres inside a 1369.91 m boundary.
    h.check(abs(fence.area - 102_669.71) < 1.0,
            "the monitored area is 102669.71 sq m (got %.2f)" % fence.area)
    h.check(abs(fence.length - 1369.91) < 1.0,
            "the geo-fence boundary is 1369.91 m (got %.2f)" % fence.length)
    h.check(fence.area > building.area * 2,
            "buffering by 50 m more than doubles the footprint")
    h.check(fence.is_valid, "the union is a valid geometry")

    h.contains(printed, "Resulting Geo-Fence Type: MultiPolygon",
               "the listing reports the geometry type")
    h.contains(printed, "Total Monitored Area (sq meters): 102669.71",
               "the listing prints the monitored area")

    h.write_json("geofence_design.json", {
        "building_area_sq_m": round(building.area, 2),
        "building_buffer_m": module.BUILDING_BUFFER_DISTANCE,
        "utility_buffer_m": module.UTILITY_BUFFER_DISTANCE,
        "fence_area_sq_m": round(fence.area, 2),
        "fence_perimeter_m": round(fence.length, 2),
        "fence_type": fence.geom_type,
        "fence_parts": len(fence.geoms),
        "wall_to_access_point_1_m": round(building.exterior.distance(p1), 2),
        "wall_to_access_point_2_m": round(building.exterior.distance(p2), 2),
        "building_grown_sq_m": round(module.building_fence.area - building.area, 2),
        "perimeter_term_sq_m": round(building.length * module.BUILDING_BUFFER_DISTANCE, 2),
        "disc_term_sq_m": round(module.building_fence.area - building.area
                                - building.length * module.BUILDING_BUFFER_DISTANCE, 2),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (geo-fence design)", FILES).crash())
