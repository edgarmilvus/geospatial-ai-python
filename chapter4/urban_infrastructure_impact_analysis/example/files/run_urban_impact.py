"""Harness for the advanced application script — one industrial zone, two geometries.

The script answers two different questions with two different geometries: the true
area and the true separation, which only the ellipsoid can give, and the local
"is this housing inside the 500 m buffer" test, which wants a flat metric plane.
The harness checks both, and it checks the number the script does not print but
implies: Web Mercator inflates area by 1/cos(latitude)^2, so the same diamond
measures about 1.46 times larger in EPSG:3857 than on the ellipsoid.
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
    h = Harness("advanced application (urban infrastructure)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_urban_impact_assessment.py", "urban_impact")
    printed = log.getvalue()

    iz, res = module.industrial_zone_gdf, module.res_gdf

    # 1. The inputs arrive in the geographic CRS, as GPS or satellite data does.
    h.equal(iz.crs.to_epsg(), 4326, "the industrial zone starts in WGS 84")
    h.equal(res.crs.to_epsg(), 4326, "the residential points start in WGS 84")
    h.equal(len(iz), 1, "one industrial zone")
    h.equal(len(res), 3, "three residential zones")
    h.equal(iz.geometry.iloc[0].geom_type, "Polygon", "the zone is a polygon")

    # 2. Geodesic metrics: the diamond spans 0.1 degrees of latitude (11.07 km) and
    #    0.1 degrees of longitude at 34 N (9.21 km), so half their product is ~51 km2.
    area_km2 = abs(module.area_sq_m) / 1e6
    h.check(51.0 <= area_km2 <= 51.5,
            "the ellipsoidal area is 51.2 sq km (got %.2f)" % area_km2)
    h.check(28_800.0 <= module.perimeter_m <= 29_000.0,
            "the ellipsoidal perimeter is 28.9 km (got %.1f m)" % module.perimeter_m)

    # 3. The centroid of a symmetric diamond is its centre vertex line.
    h.close(round(module.iz_centroid_wgs84.y, 6), 34.0, "centroid latitude is 34 N")
    h.close(round(module.iz_centroid_wgs84.x, 6), -118.15, "centroid longitude is -118.15")

    # 4. The planar pair is what the buffer is built in.
    h.equal(module.iz_planar.crs.to_epsg(), 3857, "the zone is reprojected to Web Mercator")
    h.equal(module.res_planar.crs.to_epsg(), 3857, "the points follow it")
    h.equal(module.BUFFER_DISTANCE_M, 500, "the impact threshold is 500 m")

    # Web Mercator is conformal but not equal-area: at 34 N one ground square metre
    # becomes 1/cos(34)^2 = 1.455 projected square metres. That is the distortion the
    # chapter warns about, and the harness pins it to the latitude.
    inflation = module.iz_planar.geometry.area.iloc[0] / abs(module.area_sq_m)
    expected = 1.0 / math.cos(math.radians(34.0)) ** 2
    h.check(abs(inflation - expected) < 0.02,
            "EPSG:3857 inflates this polygon by 1/cos(34)^2 = %.3f (got %.3f)"
            % (expected, inflation))

    # 5. A buffer of r metres grows the bounding box by r on every side, in the units
    #    of the CRS it is computed in. The circle is drawn as 8 segments per quadrant,
    #    so the tangent extreme can fall a metre short of r: tolerance is 5 m.
    buf = module.proximity_buffer
    west, south, east, north = module.iz_planar.total_bounds
    h.close(buf.bounds[0], west - 500, "the buffer reaches 500 m west", tol=5.0)
    h.close(buf.bounds[1], south - 500, "the buffer reaches 500 m south", tol=5.0)
    h.close(buf.bounds[2], east + 500, "the buffer reaches 500 m east", tol=5.0)
    h.close(buf.bounds[3], north + 500, "the buffer reaches 500 m north", tol=5.0)
    h.check(buf.contains(module.iz_planar.geometry.iloc[0]),
            "the buffer contains the zone it was grown from")

    # 6. The verdicts. Zone 3 sits *inside* the diamond, so it is impacted even though
    #    its distance is measured to the boundary and is therefore far above 500 m:
    #    "inside" and "within 500 m of the edge" are different questions.
    zones = module.impacted_zones
    h.equal([z["Status"] for z in zones], ["IMPACTED", "SAFE", "IMPACTED"],
            "near and critical zones are impacted, the far one is not")
    h.check(float(zones[2]["Planar_Boundary_Distance_m"]) > 500,
            "the critical zone is impacted from 2.5 km inside the boundary")
    # The near zone is 0.03 degrees east and 0.01 north of the centroid: 2.99 km.
    h.check(2.9 <= float(zones[0]["Geodesic_Centroid_Distance_km"]) <= 3.1,
            "the near zone is 3 km away on the ellipsoid (got %s)"
            % zones[0]["Geodesic_Centroid_Distance_km"])
    h.check(float(zones[1]["Geodesic_Centroid_Distance_km"]) > 20,
            "the far zone is tens of kilometres away")

    h.contains(printed, "IZ Calculated Geodesic Area: 51.24 sq km",
               "the listing prints the ellipsoidal area")
    h.contains(printed, "Proximity Analysis Results (500m Planar Buffer)",
               "the listing prints the proximity table")
    h.contains(printed, "Zone 1 Status: IMPACTED", "the summary repeats the first verdict")

    h.write_json("urban_impact.json", {
        "industrial_zone": {
            "crs_wgs84": 4326,
            "crs_planar": 3857,
            "geodesic_area_sq_km": round(area_km2, 3),
            "geodesic_perimeter_m": round(module.perimeter_m, 2),
            "centroid": [round(module.iz_centroid_wgs84.x, 5),
                         round(module.iz_centroid_wgs84.y, 5)],
            "web_mercator_area_inflation": round(inflation, 4),
            "theoretical_inflation": round(expected, 4),
        },
        "buffer_m": module.BUFFER_DISTANCE_M,
        "buffer_area_sq_m": round(buf.area, 1),
        "zones": [
            {"zone": z["Zone"], "status": z["Status"],
             "planar_boundary_distance_m": float(z["Planar_Boundary_Distance_m"]),
             "geodesic_centroid_distance_km": float(z["Geodesic_Centroid_Distance_km"])}
            for z in zones
        ],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("advanced application (urban infrastructure)", FILES).crash())
