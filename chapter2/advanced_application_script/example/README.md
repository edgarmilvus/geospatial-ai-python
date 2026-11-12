# Example 2 — ingest, validate, and stop at the CRS mismatch

## What it does

Simulates the municipal case the chapter describes: legacy district boundaries as
a Shapefile in EPSG:4326 and proposed infrastructure zones as a GeoJSON in
EPSG:3857. Both are written to a scratch folder under `output/`, read back with
`gpd.read_file()`, counted, and compared before any spatial operation is allowed
near them. The comparison is the point: the two layers are in different reference
systems, so an intersection between them would be meaningless, and the script says
so instead of computing one.

## The listings

| file | what it is |
| --- | --- |
| `01_ingestion_validation.py` | the listing: write both formats, read, count, compare CRS, clean up |
| `run_ingestion_validation.py` | the harness: checks both counts, both codes and both area scales |

## Run it

```bash
cd chapter2/advanced_application_script/example/files
python3 01_ingestion_validation.py
```

It writes a Shapefile and a GeoJSON into `output/ingest/`, reads them, prints the
mismatch warning and the areas in each layer's own units, then removes the scratch
folder; `run_ingestion_validation.py` asserts the two features per layer, the two
EPSG codes and areas of 1.0 square degrees against 1 000 000 m², and exits non-zero
if the warning stops being raised.

## What it produces

| path | what it is |
| --- | --- |
| `output/ingestion_validation.json` | feature counts, both CRS codes, both area scales, the mismatch flag |

```text
--- CRS Consistency Check ---
WARNING: CRSs are mismatched.
  Historical CRS: EPSG:4326
  Proposed CRS: EPSG:3857
  Reprojection is required before spatial operations (e.g., intersection).

Historical district areas (square degrees): [1.0, 1.0]
Proposed zone areas (square metres): [1000000.0, 1000000.0]
```

## Notes

- The scratch folder is `output/ingest/` rather than `tempfile.mkdtemp()`: a run
  that writes inside the project leaves its evidence where the reader can find it,
  and the cleanup phase still removes everything.
- The area comparison is what makes the mismatch concrete — one layer measures a
  square in degrees, the other a square kilometre.
- Field names are kept within the ten-character DBF limit so that the only
  difference the listing reports is the CRS one.
