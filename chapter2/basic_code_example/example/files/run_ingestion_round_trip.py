"""Harness for chapter 2, example 1 — the same three cities, read twice.

What is worth asserting here is not that a print happened but that the two
formats agree on the data and disagree on one column name: the DBF inside a
Shapefile truncates field names at ten characters. That difference is the
chapter's sidecar lesson, and it is a fact about the format, not a quirk of the
run.
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
    h = Harness("chapter 2 example 1 (Shapefile and GeoJSON ingestion)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_ingest_shapefile_and_geojson.py", "ch2_ingest")
    printed = log.getvalue()

    from_shp = module.gdf_from_shp
    from_json = module.gdf_from_json

    import geopandas as gpd

    # Both reads produce the specialised frame, not a plain DataFrame.
    h.check(isinstance(from_shp, gpd.GeoDataFrame), "the Shapefile read is a GeoDataFrame")
    h.check(isinstance(from_json, gpd.GeoDataFrame), "the GeoJSON read is a GeoDataFrame")

    # Three cities survive both round trips, in the order they were written.
    h.equal(len(from_shp), 3, "the Shapefile holds three features")
    h.equal(len(from_json), 3, "the GeoJSON holds three features")
    h.equal(from_shp["City"].tolist(), ["London", "Paris", "Berlin"],
            "the Shapefile preserves the row order")

    # WGS 84 survives the write, in both formats.
    h.equal(from_shp.crs.to_epsg(), 4326, "the Shapefile declares EPSG:4326")
    h.equal(from_json.crs.to_epsg(), 4326, "the GeoJSON declares EPSG:4326")

    # The geometry column has the standard name, and carries points.
    h.equal(from_shp.geometry.name, "geometry", "the Shapefile geometry column is 'geometry'")
    h.equal(from_json.geometry.name, "geometry", "the GeoJSON geometry column is 'geometry'")
    h.equal(from_shp.geom_type.unique().tolist(), ["Point"], "the Shapefile holds points")

    # London's coordinates are unchanged: 0.1278 E, 51.5074 N.
    london = from_shp.loc[from_shp["City"] == "London"].geometry.iloc[0]
    h.close(london.x, 0.1278, "London keeps its longitude", tol=1e-9)
    h.close(london.y, 51.5074, "London keeps its latitude", tol=1e-9)

    # The one real disagreement: DBF field names are ten characters wide.
    h.equal(from_shp.columns.tolist(), ["City", "Country", "Population", "geometry"],
            "the Shapefile truncates Population_M to Population")
    h.contains(from_json.columns.tolist(), "Population_M",
               "the GeoJSON keeps the full field name")
    h.close(float(from_shp["Population"].iloc[0]), 9.6,
            "the truncated column still carries London's population", tol=1e-9)

    # Phase 4 did its job: nothing of the temporary round trip is left behind.
    leftovers = sorted(p.name for p in (FILES.parent / "output").glob("european_cities.*"))
    h.equal(leftovers, [], "the cleanup phase removes the Shapefile sidecars and the GeoJSON")

    # What the reader sees.
    h.contains(printed, "Successfully created: european_cities.shp",
               "the listing reports the files it wrote")
    h.contains(printed, "2. CRS Detected: EPSG:4326",
               "the listing prints the CRS of each read")
    h.contains(printed, "Shapefile: ['City', 'Country', 'Population', 'geometry']",
               "the listing prints the truncated Shapefile columns")

    h.write_json("ingestion_round_trip.json", {
        "features": {"shapefile": len(from_shp), "geojson": len(from_json)},
        "crs": {"shapefile": from_shp.crs.to_string(), "geojson": from_json.crs.to_string()},
        "shapefile_columns": from_shp.columns.tolist(),
        "geojson_columns": from_json.columns.tolist(),
        "truncated_field": {"written": "Population_M", "read_back": "Population"},
        "london": {"lon": london.x, "lat": london.y},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 example 1 (Shapefile and GeoJSON ingestion)", FILES).crash())
