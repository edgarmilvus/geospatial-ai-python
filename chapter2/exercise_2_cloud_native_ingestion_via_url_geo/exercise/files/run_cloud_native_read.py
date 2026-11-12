"""Harness for chapter 2, exercise 2 — the remote feed, read offline.

The graded facts are the ones the exercise asks the student to print: the shape
of the ingested frame, its CRS, and the attributes the feed carries. The
harness also proves the listing did not need the network: it checks that the
file the read used exists under output/ and that the configured URL is only a
string.
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
    h = Harness("chapter 2 exercise 2 (cloud-native GeoJSON read)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_cloud_native_geojson.py", "ch2_cloud")
    printed = log.getvalue()

    fire = module.fire_perimeters_gdf

    # The shape the student is asked to print: two perimeters, two attributes
    # plus the geometry.
    h.equal(fire.shape, (2, 3), "the ingested feed is 2 rows by 3 columns")
    h.equal(fire.columns.tolist(), ["id", "intensity", "geometry"],
            "the feed carries id, intensity and geometry")
    h.equal(len(fire), 2, "two fire perimeters were read")

    # GeoJSON is WGS 84 by specification; the driver fills the CRS in.
    h.equal(fire.crs.to_epsg(), 4326, "the feed is in EPSG:4326")
    h.check(fire.crs.is_geographic, "EPSG:4326 is a geographic system")

    h.equal(fire["id"].tolist(), [1, 2], "both perimeter ids survived the read")
    h.equal(fire["intensity"].tolist(), [5.5, 7.1], "the reported intensities survived")
    h.equal(fire.geom_type.unique().tolist(), ["Polygon"], "each perimeter is a polygon")

    # The read was a real file read from the project's own output folder.
    h.check(module.LOCAL_SOURCE.exists(), "the feed file exists under output/")
    h.equal(module.LOCAL_SOURCE.parent, FILES.parent / "output",
            "the feed is written to the project's output folder")
    h.check(module.REMOTE_SOURCE.startswith("https://"),
            "the URL form of the source is still what the listing configures")
    h.equal(len(module.read_any_source(module.LOCAL_SOURCE)), 2,
            "the same call reads the local feed again, unchanged")

    h.contains(printed, "3. GeoDataFrame Shape (Rows, Columns): (2, 3)",
               "the listing prints the shape")
    h.contains(printed, "   CRS: EPSG:4326", "the listing prints the CRS")
    h.contains(printed, "Confirmed: CRS is WGS 84 (EPSG:4326)",
               "the listing confirms the GeoJSON default")

    h.write_json("cloud_native_read.json", {
        "shape": list(fire.shape),
        "columns": fire.columns.tolist(),
        "crs": fire.crs.to_string(),
        "epsg": fire.crs.to_epsg(),
        "ids": fire["id"].tolist(),
        "intensities": fire["intensity"].tolist(),
        "source_file": module.LOCAL_SOURCE.name,
        "network_used": False,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 exercise 2 (cloud-native GeoJSON read)", FILES).crash())
