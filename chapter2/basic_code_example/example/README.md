# Example 1 — three cities, twice: a Shapefile and a GeoJSON

## What it does

Writes the same three European cities to an ESRI Shapefile and to a GeoJSON file
under the project's `output/` folder, then reads both back through the same
`gpd.read_file()` call and checks that the frame, the geometry column and the CRS
survive. The round trip ends on the chapter's sidecar lesson in numbers: the dBase
table behind a Shapefile truncates field names at ten characters, so `Population_M`
comes back as `Population` while the GeoJSON keeps the full name.

## The listings

| file | what it is |
| --- | --- |
| `01_ingest_shapefile_and_geojson.py` | the listing: write two formats, read both, inspect, clean up |
| `run_ingestion_round_trip.py` | the harness: checks rows, CRS, coordinates and the truncated field |

## Run it

```bash
cd chapter2/basic_code_example/example/files
python3 01_ingest_shapefile_and_geojson.py
```

It writes both files into `output/`, prints the head of each read and the column
names that came back, then removes the temporary files; `run_ingestion_round_trip.py`
asserts the three cities, EPSG:4326 on both sides and the `Population_M` → `Population`
truncation, and exits non-zero if any of them changes.

## What it produces

| path | what it is |
| --- | --- |
| `output/ingestion_round_trip.json` | both CRSs, both column lists, London's coordinates |

```text
--- Preparing Files for Ingestion ---
Successfully created: european_cities.shp (and sidecar files) and european_cities.geojson
...
--- Column Names After the Round Trip ---
Shapefile: ['City', 'Country', 'Population', 'geometry']
GeoJSON:   ['City', 'Country', 'Population_M', 'geometry']
```

## Notes

- The Shapefile is one logical dataset in five files (`.shp`, `.shx`, `.dbf`, `.prj`,
  `.cpg`); the listing writes and deletes them together with `glob`.
- The truncation is a property of the format, not of geopandas: the DBF header
  stores names in ten bytes. Plan field names that fit, or prefer GeoJSON.
- Nothing is downloaded; both definitions come from the GDAL build inside the venv.
