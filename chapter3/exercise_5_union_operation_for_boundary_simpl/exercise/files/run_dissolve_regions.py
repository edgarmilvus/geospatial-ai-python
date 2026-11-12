"""Harness for chapter 3, exercise 5 — dissolve, and what a mean of means means.

The geometry and the sums are unambiguous: two regions, 5 000 m² each, populations
1 500 and 3 000. The income column is the interesting one. `aggfunc='mean'` averages
the zone averages, which equals the regional mean only when the zones are the same
size; R2's zones hold 2 000 and 1 000 people, so its plain mean (65 000) and its
population-weighted mean (56 666.67) differ. The harness checks both, so a solution
that quietly reports "the average income" cannot pass unnoticed.
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
    h = Harness("chapter 3 exercise 5 (dissolve and aggregate)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_dissolve_regions.py", "ch3_dissolve")
    printed = log.getvalue()

    unified = module.unified_regions_gdf

    # Four micro-zones become two regions.
    h.equal(len(module.micro_zones_gdf), 4, "four micro-zones go in")
    h.equal(len(unified), 2, "two regions come out")
    h.equal(sorted(unified["region_id"].tolist()), ["R1", "R2"],
            "the regions keep their ids")

    # The dissolve unions the parts: two 50 x 50 squares per region.
    areas = dict(zip(unified["region_id"], unified.geometry.area))
    h.close(areas["R1"], 5000.0, "R1 covers 5 000 m²", tol=1e-6)
    h.close(areas["R2"], 5000.0, "R2 covers 5 000 m²", tol=1e-6)
    # The two squares in each region meet at a single corner, so the union is a
    # MultiPolygon: dissolve combines features, it does not merge what does not touch.
    h.equal(unified.geom_type.unique().tolist(), ["MultiPolygon"],
            "each region dissolves to a two-part MultiPolygon")

    # Sums are sums.
    populations = dict(zip(unified["region_id"], unified["total_population"]))
    h.equal(int(populations["R1"]), 1500, "R1 sums to 1 500 people")
    h.equal(int(populations["R2"]), 3000, "R2 sums to 3 000 people")
    h.equal(int(unified["total_population"].sum()), 4500, "no population is lost or double counted")

    # Means of means, and the weighted figure beside them.
    incomes = dict(zip(unified["region_id"], unified["average_income"]))
    h.close(incomes["R1"], 55000.0, "R1 averages 50 000 and 60 000", tol=1e-9)
    h.close(incomes["R2"], 65000.0, "R2 averages 40 000 and 90 000", tol=1e-9)
    weighted = module.weighted.round(2).to_dict()
    h.close(weighted["R1"], 53333.33, "R1's population-weighted income is 53 333.33", tol=0.01)
    h.close(weighted["R2"], 56666.67, "R2's population-weighted income is 56 666.67", tol=0.01)
    h.check(abs(incomes["R2"] - weighted["R2"]) > 1000,
            "the plain mean and the weighted mean disagree for R2")

    # The join produced exactly one region per zone (no double assignment).
    h.equal(len(module.joined_micro_zones), 4, "each micro-zone is assigned to exactly one region")

    h.contains(printed, "Regions produced: 2 from 4 micro-zones",
               "the listing prints what the dissolve produced")
    h.contains(printed, "Region areas (m2): [5000.0, 5000.0]",
               "the listing prints the dissolved areas")
    h.contains(printed, "Population-weighted mean income: {'R1': 53333.33, 'R2': 56666.67}",
               "the listing prints the weighted comparison")

    h.write_json("dissolve_regions.json", {
        "micro_zones": len(module.micro_zones_gdf),
        "regions": len(unified),
        "region_ids": sorted(unified["region_id"].tolist()),
        "areas_sqm": {k: round(v, 3) for k, v in areas.items()},
        "population": {k: int(v) for k, v in populations.items()},
        "mean_of_means_income": {k: float(v) for k, v in incomes.items()},
        "population_weighted_income": {k: float(v) for k, v in weighted.items()},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 exercise 5 (dissolve and aggregate)", FILES).crash())
