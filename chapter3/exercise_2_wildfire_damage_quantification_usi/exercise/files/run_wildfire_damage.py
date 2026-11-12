"""Harness for chapter 3, exercise 2 — burned hectares, one row per ecosystem.

The domain facts are arithmetic on the fixtures: the fire is 10 000 ha, the old
growth zone is 900 ha and sits wholly inside it, the wetland contributes the
2 500 ha the fire reaches, and the shrubland 20 km away contributes nothing. A
solution that intersects the wrong way round, or forgets the 10 000 m² to
hectare step, cannot produce all four at once.
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
    h = Harness("chapter 3 exercise 2 (wildfire damage)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_wildfire_damage.py", "ch3_wildfire")
    printed = log.getvalue()

    burned = module.burned_areas_gdf
    summary = module.ecosystem_damage_summary

    # Only two zones meet the fire.
    h.equal(sorted(burned["zone_id"].tolist()), [201, 202],
            "the fire reaches zones 201 and 202, not 203")

    # Hectares: area in square metres divided by 10 000.
    per_zone = dict(zip(burned["zone_id"], burned["burned_area_hectares"]))
    h.close(per_zone[201], 900.0, "the old growth zone loses all 900 ha", tol=1e-6)
    h.close(per_zone[202], 2500.0, "the wetland loses the 2 500 ha the fire reaches", tol=1e-6)

    # The grouped summary: one row per ecosystem, and the total is the sum.
    h.equal(len(summary), 2, "one summary row per burned ecosystem")
    h.equal(sorted(summary["ecosystem_type"].tolist()),
            ["Old Growth Forest", "Wetland Habitat"],
            "the summary names both ecosystems")
    totals = dict(zip(summary["ecosystem_type"], summary["total_burned_hectares"]))
    h.close(totals["Old Growth Forest"], 900.0, "Old Growth Forest totals 900 ha", tol=1e-6)
    h.close(totals["Wetland Habitat"], 2500.0, "Wetland Habitat totals 2 500 ha", tol=1e-6)
    h.close(summary["total_burned_hectares"].sum(), 3400.0,
            "3 400 ha burn inside protected zones", tol=1e-6)

    # The whole fire, for scale: 10 km x 10 km.
    h.close(module.fire_perimeter_gdf.geometry.area.iloc[0] / 10000, 10000.0,
            "the fire perimeter covers 10 000 ha", tol=1e-6)
    h.check(summary["total_burned_hectares"].sum() < 10000.0,
            "the protected damage is a subset of the burned area")
    h.equal(summary.index.tolist(), [0, 1], "the summary is a plain DataFrame from reset_index")

    h.contains(printed, "Total burned across protected zones: 3,400.0 ha",
               "the listing prints the total burned area")
    h.contains(printed, "Zones left untouched: [203]", "the listing names the untouched zone")

    h.write_json("wildfire_damage.json", {
        "fire_area_ha": module.fire_perimeter_gdf.geometry.area.iloc[0] / 10000,
        "zones_total": len(module.protected_zones_gdf),
        "zones_burned": sorted(int(z) for z in burned["zone_id"]),
        "burned_hectares_by_zone": {int(k): v for k, v in per_zone.items()},
        "summary": {k: v for k, v in totals.items()},
        "total_burned_ha": summary["total_burned_hectares"].sum(),
        "hectare_divisor": module.HA_PER_SQM,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 exercise 2 (wildfire damage)", FILES).crash())
