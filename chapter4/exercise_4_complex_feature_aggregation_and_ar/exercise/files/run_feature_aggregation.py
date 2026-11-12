"""Harness for exercise 4 — two patches merge, one stays an island.

The exercise's numbers are its own test case: two 100-unit squares overlapping in a
25-unit square give a 175-unit blob, and the isolated 100-unit patch leaves the
union a MultiPolygon of 275 square units, over the 150-unit threshold. The harness
checks the parts, the whole, the geometry type and the threshold branch.
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
    h = Harness("exercise 4 (feature aggregation)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_feature_aggregation.py", "feature_aggregation")
    printed = log.getvalue()

    p1, p2, p3 = module.patch_1, module.patch_2, module.patch_3

    # Each patch is a 10 x 10 square: 100 square units, not the 10 the book's first
    # comment claimed.
    h.close(p1.area, 100.0, "patch 1 is 100 square units")
    h.close(p2.area, 100.0, "patch 2 is 100 square units")
    h.close(p3.area, 100.0, "patch 3 is 100 square units, not 10")
    h.equal(module.patches, [p1, p2, p3], "the listing aggregates the three patches")
    h.equal(module.original_patch_count, 3, "three patches go in")

    # The overlap is the 5 x 5 square the two offsets share.
    overlap = p1.intersection(p2).area
    h.close(overlap, 25.0, "the two western patches share 25 square units")
    h.check(p1.intersects(p2), "patch 1 and patch 2 really touch")
    h.check(not p1.intersects(p3), "patch 3 is isolated: 200 units away")

    union = module.unified_feature
    h.close(union.area, 275.0, "100 + 100 - 25 + 100 = 275 square units")
    h.close(union.area, p1.area + p2.area - overlap + p3.area,
            "the union area follows from the parts", tol=1e-9)
    h.equal(union.geom_type, "MultiPolygon", "one island and one blob: a MultiPolygon")
    h.equal(len(union.geoms), 2, "two parts survive the union")
    h.check(sorted(round(g.area, 6) for g in union.geoms) == [100.0, 175.0],
            "the parts are 175 and 100 square units")

    # The merged blob is one ring: the two squares became a single polygon.
    biggest = max(union.geoms, key=lambda g: g.area)
    h.equal(len(biggest.interiors), 0, "the merged blob has no hole")

    # Threshold branch: 275 >= 150, so the listing includes the feature and says so.
    h.equal(module.MIN_AREA_THRESHOLD, 150.0, "the ecological threshold is 150 square units")
    h.check(union.area >= module.MIN_AREA_THRESHOLD, "275 clears the threshold")
    h.contains(printed, "Total Area of Aggregated Feature: 275.00",
               "the listing prints the aggregated area")
    h.contains(printed, "STATUS: INCLUDED in Final Analysis Layer.",
               "the listing takes the inclusion branch")

    # The task statement in this folder documents the three patches and the threshold.
    starter = load_listing(FILES / "prompt_sketch_feature_aggregation.py", "starter_aggregation")
    h.equal(starter.MIN_AREA_THRESHOLD, 150.0, "the starter's area threshold is 150 units")

    h.write_json("feature_aggregation.json", {
        "patches": [p1.area, p2.area, p3.area],
        "overlap_sq_units": overlap,
        "union_area_sq_units": round(union.area, 2),
        "union_type": union.geom_type,
        "union_parts": [round(g.area, 2) for g in union.geoms],
        "threshold_sq_units": module.MIN_AREA_THRESHOLD,
        "included": bool(union.area >= module.MIN_AREA_THRESHOLD),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (feature aggregation)", FILES).crash())
