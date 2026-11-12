"""Harness for example 1 — the two CRS objects, read property by property.

The listing prints; nothing returns. So the harness imports it, keeps the objects
it built, and checks the properties the chapter says distinguish a geographic CRS
from a projected one: the axis order, the units, and the flag that was False for
WGS 84 and True for Web Mercator.
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
    h = Harness("example 1 (CRS objects)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_crs_objects.py", "crs_objects")
    printed = log.getvalue()

    geographic = module.geographic_crs
    projected = module.projected_crs

    # The two objects the chapter builds, from the two EPSG codes it defines.
    h.equal(geographic.to_epsg(), 4326, "the geographic CRS resolves to EPSG:4326")
    h.equal(projected.to_epsg(), 3857, "the projected CRS resolves to EPSG:3857")

    h.check(geographic.is_geographic, "WGS 84 reports itself as geographic")
    h.check(not geographic.is_projected, "WGS 84 is not projected")
    h.check(projected.is_projected, "Web Mercator reports itself as projected")
    h.check(not projected.is_geographic, "Web Mercator is not geographic")

    # The axis order is the chapter's pitfall: degrees are angular, and WGS 84
    # names latitude first. Reading a lon/lat pair as lat/lon is the bug.
    geo_axes = [axis.name for axis in geographic.axis_info]
    h.equal(len(geo_axes), 2, "a geographic CRS carries two axes")
    h.contains(geo_axes[0].lower(), "latitude",
               "WGS 84 puts latitude on the first axis")
    h.contains(geo_axes[1].lower(), "longitude",
               "WGS 84 puts longitude on the second axis")
    h.equal(geographic.axis_info[0].unit_name, "degree",
            "the geographic axes are measured in degrees")

    # A projected CRS is the one that has a metre to measure with.
    h.equal(projected.axis_info[0].unit_name, "metre",
            "the projected axes are measured in metres")
    h.check(projected.area_of_use is not None and geographic.area_of_use is not None,
            "both systems declare an area of use")

    method = projected.to_json_dict().get("conversion", {}).get("method", {}).get("name")
    h.contains(method.lower(), "mercator",
               "the projected CRS names its projection method")

    # What the reader sees, so a silent listing cannot pass.
    h.contains(printed, "Successfully loaded WGS 84 (EPSG:4326)",
               "the listing reports the geographic CRS it loaded")
    h.contains(printed, "5. Linear Unit of Measurement: metre",
               "the listing prints the projected linear unit")
    h.contains(printed, "Easting (metre), Northing (metre)",
               "the listing prints the projected axis order")

    h.write_json("crs_summary.json", {
        "geographic": {"epsg": geographic.to_epsg(), "name": geographic.name,
                       "axes": geo_axes, "unit": geographic.axis_info[0].unit_name},
        "projected": {"epsg": projected.to_epsg(), "name": projected.name,
                      "axes": [axis.name for axis in projected.axis_info],
                      "unit": projected.axis_info[0].unit_name,
                      "method": method},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (CRS objects)", FILES).crash())
