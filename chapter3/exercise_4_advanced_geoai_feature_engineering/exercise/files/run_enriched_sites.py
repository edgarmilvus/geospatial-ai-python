"""Harness for chapter 3, exercise 4 — three features merged back without loss.

The failure this exercise is built around is silent: aggregate the overlay and
assign it by position and the sites with no overlap either vanish or receive the
wrong value. So the harness checks the full vector of results, one entry per
site id, in the original order — four rows, not one.
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
    h = Harness("chapter 3 exercise 4 (enriched sites)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_enriched_sites.py", "ch3_enriched")
    printed = log.getvalue()

    enriched = module.enriched_sites_gdf

    # Nothing lost: four sites in, four rows out, ids back as a column.
    h.equal(len(enriched), 4, "all four extraction sites survive the pipeline")
    h.equal(sorted(enriched["site_id"].tolist()), [1, 2, 3, 4],
            "the site ids are restored as a column")
    h.equal(enriched.columns[0], "site_id", "site_id is the first column after reset_index")

    # Part A: only site 1 is within 100 m of Park A.
    near = dict(zip(enriched["site_id"], enriched["is_near_sensitive_area"]))
    h.equal([bool(near[site]) for site in [1, 2, 3, 4]], [True, False, False, False],
            "only site 1 sits inside the 100 m buffer")
    h.equal(str(enriched["is_near_sensitive_area"].dtype), "bool",
            "the proximity flag is a real boolean, not an object column")

    # Part B: the concession each site falls inside, with NONE for the rest.
    concessions = dict(zip(enriched["site_id"], enriched["concession_id"]))
    h.equal(concessions[1], "C1", "site 1 is inside concession C1")
    h.equal(concessions[3], "C2", "site 3 is inside concession C2")
    h.equal(concessions[2], "NONE", "site 2 is inside no concession")
    h.equal(concessions[4], "NONE", "site 4 is inside no concession")
    h.equal(int((enriched["concession_id"] == "NONE").sum()), 2,
            "two sites fall outside every concession")

    # Part C: site 1's 50 m buffer is wholly inside Park A, so the overlap is
    # pi * 50^2 = 7 854 m²; the polygonised circle lands slightly under it.
    overlaps = dict(zip(enriched["site_id"], enriched["max_sensitive_overlap_sqm"]))
    circle = math.pi * 50 ** 2
    h.check(circle * 0.99 < overlaps[1] <= circle,
            "site 1 overlaps the park by almost the whole 50 m circle (got %.2f of %.2f)"
            % (overlaps[1], circle))
    h.equal([overlaps[site] for site in [2, 3, 4]], [0.0, 0.0, 0.0],
            "the other three sites overlap nothing and get 0.0, not NaN")
    h.equal(int((enriched["max_sensitive_overlap_sqm"] > 0).sum()), 1,
            "exactly one site has a non-zero overlap")

    h.contains(printed, "Sites near the sensitive area: 1 of 4",
               "the listing prints the proximity count")
    h.contains(printed, "Sites inside a concession: 2 of 4",
               "the listing prints the concession count")
    h.contains(printed, "Sites with any sensitive-area overlap: 1",
               "the listing prints the overlap count")

    h.write_json("enriched_sites.json", {
        "sites": len(enriched),
        "site_ids": sorted(int(s) for s in enriched["site_id"]),
        "near_sensitive_area": {int(k): bool(v) for k, v in near.items()},
        "concession_id": {int(k): v for k, v in concessions.items()},
        "max_overlap_sqm": {int(k): round(v, 3) for k, v in overlaps.items()},
        "circle_area_sqm": round(circle, 3),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 exercise 4 (enriched sites)", FILES).crash())
