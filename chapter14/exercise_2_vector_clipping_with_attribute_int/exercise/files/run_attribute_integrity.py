"""Harness for exercise 2 — clipping that must not lose the attributes.

`gpd.clip` splits geometries at the ROI boundary. The harness checks the two
consequences the exercise is graded on: the geometry really was cut — each
county keeps 25 of its 100 square degrees — and every non-spatial attribute
survives unchanged for each clipped feature, not just for the sample row the
listing prints.
"""
import contextlib
import io
import pathlib
import sys

import geopandas as gpd

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 2 (vector clip, attribute integrity)"
OUTPUT = FILES.parent / "output"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(
            FILES / "01_vector_clip_attribute_integrity.py", "attribute_integrity")
    printed = log.getvalue()

    counties = module.counties_gdf
    clipped = module.clipped_gdf

    # -- what went in ----------------------------------------------------
    h.equal(len(counties), 4, "four counties enter the clip")
    h.equal(sorted(counties["County_Name"].tolist()), ["Alpha", "Beta", "Delta", "Gamma"],
            "the four counties are Alpha, Beta, Gamma and Delta")
    h.equal(int(counties["Population_2020"].sum()), 345000,
            "the four populations sum to 345 000")
    h.close(sum(geom.area for geom in counties.geometry), 400.0,
            "the counties cover 400 square degrees")

    # -- what came out ---------------------------------------------------
    h.equal(len(clipped), 2, "the ROI keeps two of the four counties")
    h.equal(sorted(clipped["County_Name"].tolist()), ["Alpha", "Beta"],
            "Alpha and Beta are the two that reach the ROI")
    h.check("Gamma" not in clipped["County_Name"].tolist(),
            "Gamma, east of the ROI, is dropped")
    h.check("Delta" not in clipped["County_Name"].tolist(),
            "Delta, further east again, is dropped")
    h.close(sum(geom.area for geom in clipped.geometry), 50.0,
            "the two clipped pieces cover 50 square degrees between them")

    # Each county was 10 x 10 degrees; the ROI starts at x=5, so each keeps 5 x 5.
    for name, expected_population in (("Alpha", 50000), ("Beta", 120000)):
        piece = clipped[clipped["County_Name"] == name].iloc[0]
        original = counties[counties["County_Name"] == name].iloc[0]
        h.close(float(piece.geometry.area), 25.0,
                "%s keeps 25 of its 100 square degrees" % name)
        h.equal(int(piece["Population_2020"]), expected_population,
                "%s keeps its 2020 population" % name)
        h.equal(int(piece["Population_2020"]), int(original["Population_2020"]),
                "%s's population is the original value, not a recomputed one" % name)

    alpha = clipped[clipped["County_Name"] == "Alpha"].iloc[0].geometry
    h.equal(tuple(round(value, 6) for value in alpha.bounds), (5.0, 5.0, 10.0, 10.0),
            "Alpha's piece runs from the ROI's corner to its own east edge")
    h.check(alpha.is_valid, "the clipped geometry is still a valid polygon")

    # -- the file on disk ------------------------------------------------
    saved = OUTPUT / "clipped_boundaries.geojson"
    h.check(saved.is_file(), "the clipped frame was written to output/")
    reread = gpd.read_file(saved)
    h.equal(len(reread), 2, "the GeoJSON holds the two clipped features")
    h.equal(reread.crs.to_string(), "EPSG:4326", "the GeoJSON is still WGS 84")
    h.equal(list(reread.columns), ["County_Name", "Population_2020", "geometry"],
            "both attribute columns and the geometry survive the round trip")
    h.equal(sorted(int(value) for value in reread["Population_2020"]), [50000, 120000],
            "the populations on disk are the original ones")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Clipped features: 2 of 4", "the listing reports the feature counts")
    h.contains(printed, "Clipped Feature Name: Alpha", "it names the sampled feature")
    h.contains(printed, "Validation Successful",
               "it reports that the attribute check passed")

    h.write_json("attribute_integrity.json", {
        "features_in": int(len(counties)),
        "features_out": int(len(clipped)),
        "kept": sorted(clipped["County_Name"].tolist()),
        "dropped": sorted(set(counties["County_Name"]) - set(clipped["County_Name"])),
        "area_in_deg2": round(sum(geom.area for geom in counties.geometry), 3),
        "area_out_deg2": round(sum(geom.area for geom in clipped.geometry), 3),
        "per_feature": {
            row["County_Name"]: {
                "population": int(row["Population_2020"]),
                "area_deg2": round(float(row.geometry.area), 3),
                "bounds": [round(value, 3) for value in row.geometry.bounds],
            }
            for _index, row in clipped.iterrows()
        },
        "geojson": saved.name,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
