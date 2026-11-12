"""Harness for chapter 3, example 1 — four operations on two known rectangles.

Every number here can be derived with a pen: the two rectangles have area 80
each, they overlap on a 5 x 4 patch, so the intersection is 20 and the union is
140. The buffer is the one place the number is not round — a unit buffer adds a
perimeter strip and four quarter-circles — so it is checked against the closed
form instead of a constant.
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
    h = Harness("chapter 3 example 1 (overlay, buffer, sjoin)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_zoning_overlay_basics.py", "ch3_zoning")
    printed = log.getvalue()

    conflict = module.gdf_conflict
    union = module.gdf_union
    buffer = module.gdf_buffer
    joined = module.gdf_joined_check

    # The inputs are the two rectangles the chapter describes.
    h.close(module.gdf_development.geometry.area.iloc[0], 80.0,
            "the development zone is 10 x 8", tol=1e-9)
    h.close(module.gdf_reserve.geometry.area.iloc[0], 80.0,
            "the reserve is 10 x 8", tol=1e-9)

    # Intersection: the 5 x 4 overlap.
    h.equal(len(conflict), 1, "the two zones overlap in one piece")
    h.close(conflict.geometry.area.iloc[0], 20.0,
            "the conflict patch is 5 x 4", tol=1e-9)
    h.equal(conflict["Name_1"].tolist(), ["Development Zone"],
            "the overlay keeps the left frame's name under Name_1")
    h.equal(conflict["Name_2"].tolist(), ["Natural Reserve"],
            "and the right frame's under Name_2")
    h.equal(conflict["Max_Height"].tolist(), [50], "the development attributes travel with the geometry")
    h.equal(conflict["Status"].tolist(), ["Protected"], "so do the reserve's")

    # Union: three pieces that add up to 80 + 80 - 20.
    h.equal(len(union), 3, "the union splits into A-B, A and B, B-A")
    h.close(union.geometry.area.sum(), 140.0, "the union covers 140 square units", tol=1e-9)

    # Buffer: 80 + perimeter * 1 + pi * 1^2, the closed form for a rectangle.
    expected_buffer = 80.0 + 2 * (10 + 8) * 1.0 + math.pi
    # A buffered corner is a polygon, not an arc, so the result lands a few
    # thousandths under the closed form: 119.1365 against 119.1416.
    h.close(buffer.geometry.area.iloc[0], expected_buffer,
            "a one-unit buffer adds the perimeter strip and four quarter circles", tol=0.01)
    h.equal(buffer["Name"].tolist(), ["Reserve Buffer"], "the buffer is relabelled")

    # Spatial join: one development zone touches the buffer.
    h.equal(len(joined), 1, "the development zone intersects the reserve buffer")
    h.equal(joined["Development"].tolist(), ["Development Zone"], "the join carries the left name")
    h.equal(joined["Buffer_Status"].tolist(), ["Reserve Buffer"], "and the right name")
    h.equal(joined["Height"].tolist(), [50], "and the left attribute")

    # What the reader sees.
    h.contains(printed, "Area of Intersection (sq units): 20.00", "the listing prints the overlap area")
    h.contains(printed, "Total Features after Union: 3", "the listing prints the union piece count")
    h.contains(printed, "Total Union Area: 140.00", "the listing prints the union area")
    h.contains(printed, "Buffered Area: 119.14", "the listing prints the buffered area")

    h.write_json("zoning_overlay.json", {
        "development_area": module.gdf_development.geometry.area.iloc[0],
        "reserve_area": module.gdf_reserve.geometry.area.iloc[0],
        "intersection_area": conflict.geometry.area.iloc[0],
        "union_features": len(union),
        "union_area": union.geometry.area.sum(),
        "buffer_area": buffer.geometry.area.iloc[0],
        "buffer_area_closed_form": round(expected_buffer, 6),
        "sjoin_rows": len(joined),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 example 1 (overlay, buffer, sjoin)", FILES).crash())
