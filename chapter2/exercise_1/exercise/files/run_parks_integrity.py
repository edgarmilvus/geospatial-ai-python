"""Harness for chapter 2, exercise 1 — does the ingested layer hold its story?

The exercise asks the student to load, identify the geometry column, read the
CRS and preview rows. A correct answer can be checked on domain facts: three
parks, EPSG:25833, and — the part that catches a careless write — each park's
geometry area in square metres equal to the area_sqm in its attribute table.
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
    h = Harness("chapter 2 exercise 1 (Shapefile integrity check)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_parks_integrity_check.py", "ch2_parks")
    printed = log.getvalue()

    import geopandas as gpd

    parks = module.parks_gdf

    h.check(isinstance(parks, gpd.GeoDataFrame), "the read returns a GeoDataFrame")
    h.equal(len(parks), 3, "the park layer holds three features")
    h.equal(parks.geometry.name, "geometry", "the active geometry column is 'geometry'")
    h.equal(parks.crs.to_epsg(), 25833, "the CRS is ETRS89 / UTM 33N")

    h.equal(parks["name"].tolist(), ["Park A", "Park B", "Park C"],
            "the three parks keep their names")

    # The integrity check: attribute area against geometry area, in metres.
    h.equal(parks["area_sqm"].tolist(), [1000, 5000, 2500],
            "the attribute table declares 1000, 5000 and 2500 m2")
    for index, expected in enumerate([1000.0, 5000.0, 2500.0]):
        h.close(parks.geometry.area.iloc[index], expected,
                "park %d geometry area matches its attribute" % (index + 1), tol=1e-6)

    # A projected CRS is what makes that comparison legal at all.
    h.check(parks.crs.is_projected, "the layer is projected, so areas are in metres")
    h.equal(parks.geom_type.unique().tolist(), ["Polygon"], "every park is a polygon")

    # The preview step: three rows, so head(5) returns all three.
    h.equal(len(parks.head(5)), 3, "the preview shows all three rows")

    h.contains(printed, "   EPSG Code: 25833", "the listing prints the EPSG code")
    h.contains(printed, "   agree: True", "the listing reports that geometry and attributes agree")

    h.write_json("parks_integrity.json", {
        "features": len(parks),
        "geometry_column": parks.geometry.name,
        "crs": parks.crs.to_string(),
        "epsg": parks.crs.to_epsg(),
        "area_sqm_attribute": parks["area_sqm"].tolist(),
        "area_sqm_geometry": [round(a, 3) for a in parks.geometry.area],
        "areas_agree": bool((parks.geometry.area.round(1) == parks["area_sqm"]).all()),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 exercise 1 (Shapefile integrity check)", FILES).crash())
