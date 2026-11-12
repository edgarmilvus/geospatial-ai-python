"""Harness for chapter 3, exercise 3 — counts that only a correct join produces.

Central must come out at 2 and North at 5. Getting there requires the join to run
in the right direction (points within polygons), the filter to be applied to the
joined frame, and the aggregation to count detections rather than rows of the
original layer. Each of those mistakes changes a number here.
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
    h = Harness("chapter 3 exercise 3 (residential counts)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_residential_counts.py", "ch3_counts")
    printed = log.getvalue()

    joined = module.joined_detections
    counts = module.residential_counts_df

    # Nine of ten detections fall inside a neighborhood; one does not.
    h.equal(len(joined), 9, "nine detections fall inside a neighborhood")
    h.equal(joined["hood_name"].isna().sum(), 0, "every joined detection carries a hood name")

    # The answer: two per neighborhood, and the counts sum to the filter's total.
    h.equal(counts["hood_name"].tolist(), ["Central", "North"],
            "the summary has one row per neighborhood, alphabetically")
    values = dict(zip(counts["hood_name"], counts["residential_building_count"]))
    h.equal(int(values["Central"]), 2, "Central counts two residential buildings")
    h.equal(int(values["North"]), 5, "North counts five")
    h.equal(int(counts["residential_building_count"].sum()), 7,
            "all seven residential detections are counted")

    # Guard against the common wrong answer: counting every joined row.
    h.check(int(counts["residential_building_count"].sum())
            < int(joined.groupby("hood_name").size().sum()),
            "the residential count is smaller than the joined row count")

    # The frames are the ones the exercise describes.
    h.equal(len(module.building_detections_gdf), 10, "ten detections were loaded")
    h.equal(len(module.neighborhoods_gdf), 2, "two neighborhoods were loaded")
    h.equal(int((module.building_detections_gdf["building_type"] == "Residential").sum()), 7,
            "seven of the ten detections are residential")

    h.contains(printed, "Detections inside a neighborhood: 9",
               "the listing prints how many detections joined")
    h.contains(printed, "Detections outside every neighborhood: 1",
               "the listing prints how many did not")
    h.contains(printed, "  Central                           2",
               "the listing prints Central's count")
    h.contains(printed, "    North                           5",
               "the listing prints North's count")

    h.write_json("residential_counts.json", {
        "detections": len(module.building_detections_gdf),
        "joined": len(joined),
        "outside": len(module.building_detections_gdf) - len(joined),
        "residential_total": int((module.building_detections_gdf["building_type"]
                                  == "Residential").sum()),
        "counts": {k: int(v) for k, v in values.items()},
        "predicate": "within",
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 exercise 3 (residential counts)", FILES).crash())
