"""Harness for the interactive challenge's task statement — the inputs, and the target.

This section publishes the starter, not the answer: the six-vertex building, two access
points and two buffer distances, with the buffers left to the reader. So the harness
does two things a harness for a starter can honestly do: it checks that the inputs are
the documented ones, and it computes the numbers the reader's answer must reach, so
the challenge is gradeable and agrees with the solution printed in the chapter's
solutions section.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("interactive challenge (geo-fence, task statement)", FILES)
    module = load_listing(FILES / "01_geofence_spec.py", "geofence_spec")

    building = module.main_building
    p1, p2 = module.utility_point_1, module.utility_point_2

    # The strict reading of "a complex polygon": six vertices, all distinct, closed ring.
    h.equal(building.geom_type, "Polygon", "the building is a Polygon")
    h.equal(len(building.exterior.coords) - 1, 6, "six distinct vertices")
    h.check(building.is_valid, "the building is a valid geometry")
    h.close(building.area, 50_000.0, "the hall covers exactly 50000 sq m")
    h.equal(module.BUILDING_BUFFER_DISTANCE, 50.0, "the security buffer is 50 m")
    h.equal(module.UTILITY_BUFFER_DISTANCE, 20.0, "the utility margin is 20 m")

    # The access points must be outside the building; a 20 m buffer on a point already
    # inside would be swallowed by the 50 m fence.
    h.check(not building.contains(p1), "access point 1 stands apart from the building")
    h.check(not building.contains(p2), "access point 2 stands apart from the building")
    h.equal((p1.x, p1.y), (400.0, 150.0), "access point 1 is at 400/150")
    h.equal((p2.x, p2.y), (50.0, 450.0), "access point 2 is at 50/450")

    # The starter defines the problem, not the answer: nothing has been buffered yet.
    h.check(not hasattr(module, "unified_geo_fence"),
            "the starter leaves the union to the reader")
    h.check(not hasattr(module, "building_fence"), "the starter leaves the buffering open")

    # What a correct answer has to produce, computed here from the published inputs.
    fence = (building.buffer(module.BUILDING_BUFFER_DISTANCE)
             .union(p1.buffer(module.UTILITY_BUFFER_DISTANCE))
             .union(p2.buffer(module.UTILITY_BUFFER_DISTANCE)))
    h.equal(fence.geom_type, "MultiPolygon", "the correct answer is a MultiPolygon")
    h.check(abs(fence.area - 102_669.71) < 1.0,
            "the answer must cover 102669.71 sq m (got %.2f)" % fence.area)
    h.check(abs(fence.length - 1369.91) < 1.0,
            "the answer's boundary must run 1369.91 m (got %.2f)" % fence.length)

    # And the grading rule: the fence already covers each rule's buffer. Containment is
    # tested by area — adding the buffer to the fence must add nothing — because a
    # buffer built into the union shares its boundary and `contains` then says no.
    h.check(abs(fence.union(building.buffer(50)).area - fence.area) < 1e-6,
            "the fence already covers the 50 m building buffer")
    h.check(abs(fence.union(p1.buffer(20)).area - fence.area) < 1e-6,
            "the fence already covers access point 1's margin")
    h.check(abs(fence.union(p2.buffer(20)).area - fence.area) < 1e-6,
            "the fence already covers access point 2's margin")
    # Access point 1 is 67.08 m from the wall, inside the 50 + 20 m of buffer, so that
    # disc merges with the building fence; the far point keeps its own island.
    h.check(abs(building.exterior.distance(p1) - 67.082) < 0.01,
            "access point 1 stands 67.08 m from the wall")

    h.write_json("geofence_spec.json", {
        "building_vertices": len(building.exterior.coords) - 1,
        "building_area_sq_m": round(building.area, 2),
        "buffers_m": {"building": module.BUILDING_BUFFER_DISTANCE,
                      "utility": module.UTILITY_BUFFER_DISTANCE},
        "target_area_sq_m": round(fence.area, 2),
        "target_perimeter_m": round(fence.length, 2),
        "target_type": fence.geom_type,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("interactive challenge (geo-fence, task statement)", FILES).crash())
