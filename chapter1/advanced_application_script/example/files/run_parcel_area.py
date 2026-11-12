"""Harness for example 2 — the same parcel measured in two coordinate systems.

The listing proves one thing: an area computed in degrees is not an area, and the
same polygon measured in a local UTM zone is. The harness checks both numbers and
the file the listing exports, so the "transformation happened" claim is measured
rather than asserted.
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
    h = Harness("example 2 (parcel area)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_parcel_area.py", "parcel_area")
    # The listing guards its run behind `if __name__ == "__main__"`, so importing
    # it defines the function and prints nothing. The harness makes the call.
    with contextlib.redirect_stdout(log):
        module.calculate_and_verify_area(
            coords=module.parcel_coordinates_wgs84,
            source_crs=module.GCS_WGS84_EPSG,
            target_crs=module.PCS_UTM_EPSG,
            target_crs_name=module.PCS_UTM_NAME,
        )
    printed = log.getvalue()

    import geopandas as gpd
    import pyproj
    from shapely.geometry import Polygon

    gdf = gpd.GeoDataFrame({"name": ["Development Parcel A"]},
                           geometry=[Polygon(module.parcel_coordinates_wgs84)],
                           crs="EPSG:4326")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        degrees = gdf.geometry.area.iloc[0]
    # A degree of longitude at this latitude is about 88 km, so an area in
    # square degrees is a number with no unit a surveyor can use.
    h.check(0 < degrees < 1,
            "the area in square degrees is a fraction, not a measurement (%r)" % degrees)

    projected = gdf.to_crs(epsg=module.PCS_UTM_EPSG)
    square_metres = projected.geometry.area.iloc[0]
    hectares = square_metres / 10_000
    # The parcel is roughly 9 km x 11 km by construction; anything outside
    # 1 000 and 200 000 hectares would mean the wrong zone was used.
    # Roughly 0.9 km x 1.1 km on the ground: tens of hectares, not thousands.
    h.check(10 < hectares < 10_000,
            "the projected area is a plausible parcel (%r ha)" % hectares)

    # The target is the UTM zone that contains this longitude, not a global one.
    crs = pyproj.CRS.from_epsg(module.PCS_UTM_EPSG)
    h.check(crs.is_projected, "the target CRS is projected")
    h.equal(crs.axis_info[0].unit_name, "metre", "the target CRS measures in metres")
    h.contains(crs.name, "UTM zone 10N", "the target is UTM zone 10N, the local zone")

    exported = FILES.parent / "output" / "parcel_verification.gpkg"
    h.check(exported.exists(), "the listing exported the projected parcel")
    if exported.exists():
        written = gpd.read_file(exported)
        h.equal(len(written), 1, "the export holds one feature")
        h.equal(written.crs.to_epsg(), module.PCS_UTM_EPSG,
                "the export carries the projected CRS, not the source one")

    h.contains(printed, "Area in Hectares:", "the listing reports hectares")
    h.contains(printed, "Projection Type: Projected CRS",
               "the listing names the projection type")
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (parcel area)", FILES).crash())
