"""Harness for exercise 5 — the density surface as an API payload.

The exercise's product is a contract: a FeatureCollection of grid cells, each carrying a
`density_score`, produced by a handler that answers a request. The harness parses the
payload, checks the grid arithmetic (2 401 equal cells over the pings' bounding box), the
normalisation, and then calls the handler twice with different time filters — a handler
that ignores its request returns the same numbers twice, which is the failure this catches.
"""
import contextlib
import io
import json
import pathlib
import sys
import traceback
import warnings

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

# The grid cells are degrees on a plane; the area check is about regularity, not geodesy.
warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")

NAME = "exercise 5 (heatmap GeoJSON API)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "heatmap_geojson_api.py", "heatmap_api")
    printed = log.getvalue()

    frame = module.gdf
    response_gdf = module.response_gdf
    payload = json.loads(module.api_response_geojson)

    h.equal(len(frame), 6000, "six thousand pings are simulated")
    h.equal(frame.crs.to_epsg(), 4326, "the points are in WGS 84")

    # The contract.
    h.equal(payload["type"], "FeatureCollection", "the payload is a FeatureCollection")
    h.equal(len(payload["features"]), 2401,
            "a 49 by 49 grid gives 2 401 cells over the bounding box")
    h.equal(len(response_gdf), 2401, "the GeoDataFrame holds the same number of cells")
    h.equal(response_gdf.crs.to_epsg(), 4326, "and declares WGS 84")
    h.equal(response_gdf.geometry.geom_type.unique().tolist(), ["Polygon"],
            "every cell is a polygon")
    areas = response_gdf.geometry.area
    h.check((areas - areas.iloc[0]).abs().max() < 1e-12,
            "all cells have the same area, so the grid is regular")

    first = payload["features"][0]
    h.equal(list(first["properties"]), ["density_score"],
            "the only property is the one the API contract names")
    h.check(isinstance(first["properties"]["density_score"], float),
            "and it is a number, not a string")
    scores = response_gdf["density_score"]
    h.check(scores.between(0.0, 1.0).all(), "every score is in 0..1")
    h.check(abs(float(scores.max()) - 1.0) < 1e-12,
            "the hottest cell is exactly 1.0, so the scale is normalised")
    h.equal(int((scores > 0).sum()), 388,
            "388 of the cells carry pings; the rest are genuinely empty")
    h.equal(int((scores == 0).sum()), 2401 - 388, "and their score is 0, not NaN")

    # The cells cover the data: the grid's extent is the bounding box of the pings this
    # request selected - which is why a filtered request returns a finer grid, not fewer
    # cells.
    selection = frame[(frame["hour"] >= 7) & (frame["hour"] < 9)]
    minx, miny, maxx, maxy = selection.total_bounds
    gminx, gminy, gmaxx, gmaxy = response_gdf.total_bounds
    for actual, expected, label in ((gminx, minx, "west"), (gminy, miny, "south"),
                                    (gmaxx, maxx, "east"), (gmaxy, maxy, "north")):
        h.check(abs(actual - expected) < 1e-9, "the grid's %s edge is the data's" % label)

    # The request is handled, not ignored.
    peak_count = int(((frame["hour"] >= 7) & (frame["hour"] < 9)).sum())
    h.equal(peak_count, 508, "508 of the 6 000 pings fall in the 07:00-08:59 window")
    with contextlib.redirect_stdout(io.StringIO()):
        full_payload, full_gdf = module.generate_heatmap_response({"time_filter": "all_day"})
    full = json.loads(full_payload)
    h.equal(len(full["features"]), 2401, "the whole-day answer has the same grid")
    h.check(abs(float(full_gdf["density_score"].max()) - 1.0) < 1e-12,
            "and is normalised on its own peak")
    h.check(int((full_gdf["density_score"] > 0).sum())
            != int((scores > 0).sum()),
            "but it fills a different number of cells: the filter reached the histogram")

    # The file.
    feature_path = FILES.parent / "output" / "heatmap_density.geojson"
    h.check(feature_path.is_file(), "the run wrote %s" % feature_path.name)
    on_disk = json.loads(feature_path.read_text(encoding="utf-8"))
    h.equal(on_disk["type"], "FeatureCollection", "the file on disk is a FeatureCollection")
    h.equal(len(on_disk["features"]), 2401, "with the same 2 401 features")

    h.contains(module.api_response_geojson[:500], '"type": "FeatureCollection"',
               "the first 500 characters the listing prints show the collection type")
    h.contains(module.api_response_geojson[:500], "density_score",
               "and the required property")
    h.contains(printed, "API Request received with parameters: {'time_filter': 'peak_hour'",
               "the run logs the request it answered")
    h.contains(printed, "peak_hour keeps 508 of 6000 pings", "and what the filter kept")
    h.contains(printed, "Features: 2401", "and the size of the payload")
    h.contains(printed, "density_score: 0.0000 to 1.0000",
               "and the normalised range")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("heatmap_api.json", {
        "pings": len(frame),
        "features": len(payload["features"]),
        "grid": [49, 49],
        "cells_with_data": int((scores > 0).sum()),
        "score_range": [round(float(scores.min()), 4), round(float(scores.max()), 4)],
        "peak_hour_pings": peak_count,
        "all_day_cells_with_data": int((full_gdf["density_score"] > 0).sum()),
        "file": feature_path.name,
        "bytes": feature_path.stat().st_size,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
