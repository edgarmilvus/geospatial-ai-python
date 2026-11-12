"""Harness for chapter 3, exercise 1 — a corridor cut out of three parcels.

The exercise grades five numbers per parcel. Three of them are derivable: the
corridor is 500 m either side of a 10 km line, parcel 101 lies wholly inside it
(100 %), parcel 102 is cut to half its height (1 000 000 of 4 000 000 m², 25 %),
and parcel 103 is 20 km away and must be absent from the result.

The harness also checks that the original area was joined back from the input
frame rather than taken from the clipped geometry — the mistake that makes every
percentage read 100 %.
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
    h = Harness("chapter 3 exercise 1 (pipeline corridor impact)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_pipeline_corridor_impact.py", "ch3_pipeline")
    printed = log.getvalue()

    final = module.final_impact_analysis_gdf

    # Two of the three parcels are touched; the distant one is not.
    h.equal(sorted(final["parcel_id"].tolist()), [101, 102],
            "only the two parcels along the pipeline are clipped")
    h.check(103 not in final["parcel_id"].tolist(), "the parcel 20 km away is excluded")

    # Areas, in metres, against the geometry the input declares.
    areas = dict(zip(final["parcel_id"], final["impacted_area_sqm"]))
    h.close(areas[101], 3000000.0, "parcel 101 gives 3 km x 1 km of land to the corridor", tol=1e-6)
    h.close(areas[102], 1000000.0, "parcel 102 gives 1 km x 1 km", tol=1e-6)

    # The percentage needs the *original* area, not the clipped one.
    percents = dict(zip(final["parcel_id"], final["impact_percent"]))
    h.close(percents[101], 100.0, "parcel 101 is fully inside the corridor", tol=1e-6)
    h.close(percents[102], 25.0, "parcel 102 loses a quarter of its area", tol=1e-6)
    originals = dict(zip(final["parcel_id"], final["total_area_sqm_original"]))
    h.close(originals[102], 4000000.0, "the original area is the input's 4 000 000 m²", tol=1e-6)

    # The corridor itself: a 10 km line buffered by 500 m.
    h.close(module.pipeline_gdf.geometry.length.iloc[0], 10000.0,
            "the pipeline is 10 km long", tol=1e-6)
    h.equal(final.crs.to_epsg(), 32617, "the result stays in the metric CRS")

    h.contains(printed, "Parcels clipped by the corridor: [101, 102]",
               "the listing prints the clipped parcel ids")
    h.contains(printed, "       101     Wheat          3000000.0                3000000.0           100.0",
               "the listing prints 100 % for the fully covered parcel")
    h.contains(printed, "       102      Corn          1000000.0                4000000.0            25.0",
               "the listing prints 25 % for the halved parcel")

    h.write_json("pipeline_impact.json", {
        "parcels_total": len(module.parcels_gdf),
        "parcels_affected": sorted(final["parcel_id"].tolist()),
        "parcels_unaffected": [103],
        "impacted_area_sqm": {int(k): v for k, v in areas.items()},
        "original_area_sqm": {int(k): v for k, v in originals.items()},
        "impact_percent": {int(k): v for k, v in percents.items()},
        "pipeline_length_m": module.pipeline_gdf.geometry.length.iloc[0],
        "buffer_m": 500,
        "crs": final.crs.to_string(),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 exercise 1 (pipeline corridor impact)", FILES).crash())
