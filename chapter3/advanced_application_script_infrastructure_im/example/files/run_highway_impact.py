"""Harness for chapter 3, example 2 — the impact assessment, in metres.

The behaviour to pin down is the reprojection: the route is created in degrees,
and every number that has a unit is computed after to_crs(UTM 15N). The harness
checks the corridor's membership (three residential parcels, ids 1, 4 and 5),
the conflict length against both wetlands, and that the layer given to the join
is the projected one.
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
    h = Harness("chapter 3 example 2 (highway impact)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_highway_impact.py", "ch3_highway")
    printed = log.getvalue()

    # The inputs are lon/lat; the analysis is metric.
    h.equal(module.highway_gdf.crs.to_epsg(), 4326, "the route is created in EPSG:4326")
    h.equal(module.highway_utm.crs.to_epsg(), 32615, "the route is reprojected to UTM 15N")
    h.check(module.highway_gdf.crs.is_geographic, "the creation CRS is geographic")
    h.check(module.highway_utm.crs.is_projected, "the analysis CRS is projected")

    # A degree of longitude here is not a metre; the projected length is ~4 km.
    projected_length = module.highway_utm.geometry.length.iloc[0]
    h.check(1000 < projected_length < 2000,
            "the route is between one and two kilometres long in metres (got %.1f)"
            % projected_length)

    # The corridor is 50 m either side, so it contains the route it was built on.
    h.equal(len(module.impact_zone_gdf), 1, "the buffer produced one corridor polygon")
    h.check(module.impact_zone_gdf.geometry.iloc[0].contains(
        module.highway_utm.geometry.iloc[0]), "the corridor contains the route")

    # Membership: the residential parcels inside the corridor, by id.
    affected = module.affected_residential_parcels
    h.equal(sorted(affected["pid"].tolist()), [1, 4, 5],
            "three residential parcels fall inside the 50 m corridor")
    h.equal(len(module.affected_parcels_join), 4,
            "four parcels fall inside it in total, one of them commercial")

    # The environmental conflict, in metres of road over protected ground.
    conflict = module.conflict_area_gdf
    h.equal(sorted(conflict["name"].tolist()), ["Wetland A", "Wetland B"],
            "the route crosses both wetlands")
    total = module.total_conflict_length
    h.check(300 < total < projected_length,
            "the conflict length is a fraction of the route (got %.2f m)" % total)
    h.close(total, conflict["conflict_length_m"].sum(),
            "the reported total is the sum of the per-wetland lengths", tol=1e-6)
    h.equal(conflict.geom_type.unique().tolist(), ["LineString"],
            "a line intersecting a polygon yields line segments")

    h.contains(printed, "Residential Parcels within 50m Buffer: 3",
               "the listing prints the residential count")
    h.contains(printed, "Total Highway Conflict Length (Wetlands): 565.55 m",
               "the listing prints the conflict length")
    h.contains(printed, "Affected Parcel IDs: [1, 4, 5]", "the listing names the affected parcels")
    h.contains(printed, "Wetlands affected: ['Wetland A', 'Wetland B']",
               "the listing names the wetlands")

    h.write_json("highway_impact.json", {
        "route_length_m": round(projected_length, 2),
        "buffer_m": 50,
        "parcels_total": len(module.parcels_gdf),
        "affected_parcels": len(module.affected_parcels_join),
        "affected_residential": sorted(affected["pid"].tolist()),
        "wetlands_crossed": sorted(conflict["name"].tolist()),
        "conflict_length_m": round(total, 2),
        "creation_crs": module.highway_gdf.crs.to_string(),
        "analysis_crs": module.highway_utm.crs.to_string(),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 3 example 2 (highway impact)", FILES).crash())
