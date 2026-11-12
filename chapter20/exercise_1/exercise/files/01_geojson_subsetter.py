"""Chapter 20, exercise 1 — a GeoJSON subset writer that cannot leak a handle.

The rule the exercise is really about is that the file is closed on every path: the
successful one, the one where the content is not JSON, and the one where the input
does not exist. Each `with open(...)` below ends before the code that decides what to
do next, so no branch can leave a handle open — and the exception that comes back
from a corrupt file is the custom one, not a decoder error leaking out of the parser.
"""

import json
import pathlib
from typing import Tuple

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
INPUT_FILE = OUTPUT_DIR / "valid_input.geojson"
OUTPUT_FILE = OUTPUT_DIR / "subset.geojson"
CORRUPT_FILE = OUTPUT_DIR / "corrupt_input.geojson"
MISSING_FILE = OUTPUT_DIR / "non_existent_data.geojson"

BARRIER_BBOX = (0.0, 0.0, 10.0, 10.0)


# 1. The exception the caller can catch without knowing about json
class DataProcessingError(Exception):
    """Raised when geospatial input exists but cannot be processed."""


def _inside_bbox(coordinates, bbox: Tuple[float, float, float, float]) -> bool:
    """True when a lon/lat pair falls inside (minx, miny, maxx, maxy)."""
    if not coordinates:
        return False
    longitude, latitude = coordinates[0], coordinates[1]
    minx, miny, maxx, maxy = bbox
    return minx <= longitude <= maxx and miny <= latitude <= maxy


def safe_geojson_subsetter(input_path: str, output_path: str,
                           bbox_filter: Tuple[float, float, float, float]) -> int:
    """Keep the features inside the bounding box, and close both files whatever happens.

    Returns the number of features written. A missing input is reported and returns
    zero; a file that exists but is not a GeoJSON raises `DataProcessingError`.
    """
    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            try:
                data = json.load(infile)
            except json.JSONDecodeError as exc:
                # The handle is already closed by the `with`; only the content failed.
                raise DataProcessingError(
                    f"Corrupt GeoJSON in {pathlib.Path(input_path).name}: {exc}") from exc
    except FileNotFoundError:
        print(f"ERROR: input file not found at {pathlib.Path(input_path).name}. "
              "Halting operation.")
        return 0

    if data.get("type") != "FeatureCollection":
        raise DataProcessingError(
            f"{pathlib.Path(input_path).name} is a {data.get('type')!r}, "
            "not a FeatureCollection")

    kept = [feature for feature in data.get("features", [])
            if _inside_bbox(feature.get("geometry", {}).get("coordinates"),
                            bbox_filter)]

    output_data = {"type": "FeatureCollection", "features": kept}
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(output_data, outfile, indent=2)
    return len(kept)


def build_mock_input():
    """Four building points: two inside the bbox, one on its edge, one outside."""
    features = [
        {"type": "Feature", "properties": {"id": 1, "name": "inside north"},
         "geometry": {"type": "Point", "coordinates": [4.0, 8.0]}},
        {"type": "Feature", "properties": {"id": 2, "name": "inside south"},
         "geometry": {"type": "Point", "coordinates": [7.0, 3.0]}},
        {"type": "Feature", "properties": {"id": 3, "name": "on the edge"},
         "geometry": {"type": "Point", "coordinates": [10.0, 5.0]}},
        {"type": "Feature", "properties": {"id": 4, "name": "far outside"},
         "geometry": {"type": "Point", "coordinates": [42.0, -7.0]}},
    ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(INPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump({"type": "FeatureCollection", "features": features}, handle, indent=2)
    with open(CORRUPT_FILE, "w", encoding="utf-8") as handle:
        handle.write('{"type": "FeatureCollection", "features": [ truncated')


def main():
    build_mock_input()

    print("--- Test 1: a valid file, filtered by the bbox ---")
    count = safe_geojson_subsetter(str(INPUT_FILE), str(OUTPUT_FILE), BARRIER_BBOX)
    print(f"[Test 1 Success] wrote {count} of 4 features to {OUTPUT_FILE.name}")

    with open(OUTPUT_FILE, "r", encoding="utf-8") as handle:
        written = json.load(handle)
    print("  kept: " + ", ".join(feature["properties"]["name"]
                                 for feature in written["features"]))

    print("\n--- Test 2: an input that does not exist ---")
    missing = safe_geojson_subsetter(str(MISSING_FILE), str(OUTPUT_DIR / "error.geojson"),
                                     BARRIER_BBOX)
    print(f"[Test 2 Handled] returned {missing}, no exception escaped")

    print("\n--- Test 3: an input that exists but is not JSON ---")
    try:
        safe_geojson_subsetter(str(CORRUPT_FILE), str(OUTPUT_DIR / "error.geojson"),
                               BARRIER_BBOX)
    except DataProcessingError as exc:
        print(f"[Test 3 Handled] DataProcessingError: {exc}")

    return count


if __name__ == "__main__":
    main()
