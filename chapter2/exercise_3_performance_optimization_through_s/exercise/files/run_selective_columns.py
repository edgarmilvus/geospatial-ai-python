"""Harness for chapter 2, exercise 3 — two columns in, five columns skipped.

The grade is not "the answer mentions columns". It is: the frame that reached
Python has exactly the geometry plus the two requested attributes, the full read
has more, and the rows survived the projection pushdown. The harness also
confirms that the geometry column the driver adds back is still active.
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
    h = Harness("chapter 2 exercise 3 (selective column loading)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_selective_columns.py", "ch2_columns")
    printed = log.getvalue()

    optimized = module.optimized_roads_gdf
    full = module.full_roads_gdf

    # The optimized frame carries the geometry plus the two requested fields.
    h.equal(optimized.columns.tolist(), ["segment_id", "road_class", "geometry"],
            "only the two requested attributes and the geometry were read")
    h.equal(len(optimized), 3, "all three road segments were read")
    h.equal(optimized["segment_id"].tolist(), [101, 102, 103],
            "segment ids survived the column filter")
    h.equal(optimized["road_class"].tolist(), ["Highway", "Local", "Highway"],
            "road classes survived the column filter")

    # The comparison read is what proves something was actually skipped.
    h.equal(len(full.columns), 8, "the full read has seven attributes and a geometry")
    h.equal(sorted(set(full.columns) - set(optimized.columns)),
            ["admin_code", "legacy", "length_km", "surface", "traffic"],
            "five attribute columns were left in the file")

    # Reading a subset must not despecialise the frame.
    import geopandas as gpd
    h.check(isinstance(optimized, gpd.GeoDataFrame),
            "the column-filtered read is still a GeoDataFrame")
    h.equal(optimized.geometry.name, "geometry",
            "the driver adds the geometry column back as the active one")
    h.equal(optimized.geom_type.unique().tolist(), ["LineString"],
            "the geometry survived as LineStrings")

    h.equal(module.required_attributes, ["segment_id", "road_class"],
            "the required list is exactly the two model inputs")

    h.contains(printed, "Columns read: 3 of 8", "the listing prints the column budget")
    h.contains(printed, "Columns skipped: ['admin_code', 'legacy', 'length_km', 'surface', 'traffic']",
               "the listing lists the columns it never read")

    h.write_json("selective_columns.json", {
        "optimized_columns": optimized.columns.tolist(),
        "optimized_rows": len(optimized),
        "full_columns": full.columns.tolist(),
        "skipped": sorted(set(full.columns) - set(optimized.columns)),
        "geometry_column": optimized.geometry.name,
        "geometry_types": optimized.geom_type.unique().tolist(),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 exercise 3 (selective column loading)", FILES).crash())
