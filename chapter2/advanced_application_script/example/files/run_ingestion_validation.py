"""Harness for chapter 2, example 2 — ingest, validate, refuse to mix CRSs.

The script's whole point is the last block: the two layers it read are in
different reference systems, the check catches it, and no spatial operation is
allowed to run. The harness asserts the feature counts, the two CRS codes, and
the areas that only make sense inside each system.
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
    h = Harness("chapter 2 example 2 (ingestion validation)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_ingestion_validation.py", "ch2_validation")
    printed = log.getvalue()

    historical = module.gdf_historical_in
    proposed = module.gdf_proposed_in

    # Both reads succeeded; a None here would mean the driver failed.
    h.check(historical is not None, "the Shapefile was ingested")
    h.check(proposed is not None, "the GeoJSON was ingested")
    if historical is None or proposed is None:
        return h.report()

    # Two districts, two zones — nothing lost on the way through disk.
    h.equal(len(historical), 2, "the Shapefile holds two districts")
    h.equal(len(proposed), 2, "the GeoJSON holds two zones")

    # The two codes the script printed, and the mismatch it is checking for.
    h.equal(historical.crs.to_epsg(), 4326, "the districts are in EPSG:4326")
    h.equal(proposed.crs.to_epsg(), 3857, "the zones are in EPSG:3857")
    h.check(historical.crs != proposed.crs, "the validation step has a real mismatch to report")

    # Attributes survive the Shapefile's dBase table.
    h.equal(historical["District"].tolist(), [101, 102], "district ids survive the write")
    h.equal(historical["Status"].tolist(), ["Protected", "Review"], "district status survives")
    h.equal(historical["Year_Est"].tolist(), [1950, 1985], "estimate years survive")

    # Areas mean different things in the two systems: a unit square in degrees
    # is 1 square degree; a 1000 m square in Web Mercator is 1 000 000 m².
    h.equal([round(a, 6) for a in historical.geometry.area], [1.0, 1.0],
            "each district is a one-degree square")
    h.equal([round(a, 3) for a in proposed.geometry.area], [1000000.0, 1000000.0],
            "each proposed zone is one square kilometre")

    # Cleanup removed the scratch folder; the project keeps only its artefacts.
    h.check(not module.WORK_DIR.exists(), "the working folder is removed at the end")
    h.equal(sorted(p.name for p in (FILES.parent / "output").glob("*.shp")), [],
            "no Shapefile is left in output/")

    # What the reader sees.
    h.contains(printed, "WARNING: CRSs are mismatched.", "the listing raises the CRS warning")
    h.contains(printed, "  Historical CRS: EPSG:4326", "the warning names the district CRS")
    h.contains(printed, "  Proposed CRS: EPSG:3857", "the warning names the zone CRS")
    h.contains(printed, "Reprojection is required", "the listing says what to do next")

    h.write_json("ingestion_validation.json", {
        "shapefile": {"features": len(historical), "crs": historical.crs.to_string(),
                      "districts": historical["District"].tolist(),
                      "areas_sq_degrees": [round(a, 6) for a in historical.geometry.area]},
        "geojson": {"features": len(proposed), "crs": proposed.crs.to_string(),
                    "zones": proposed["Zone_Name"].tolist(),
                    "areas_sqm": [round(a, 3) for a in proposed.geometry.area]},
        "crs_mismatch": bool(historical.crs != proposed.crs),
        "working_folder_removed": not module.WORK_DIR.exists(),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("chapter 2 example 2 (ingestion validation)", FILES).crash())
