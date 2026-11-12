# Exercise 1 — load a Shapefile and prove what came back

## What it does

Creates `city_parks.shp` (three Berlin parks in EPSG:25833, where one unit is one
metre), reads it, and answers the four checks the exercise asks for: is the object
a `GeoDataFrame`, what is the active geometry column called, what CRS does it carry,
and what do the first five rows look like. A fifth check follows, the one that
catches a real ingestion bug: each park's geometry area in square metres against
the `area_sqm` in its attribute table.

## The listings

| file | what it is |
| --- | --- |
| `01_parks_integrity_check.py` | the solution: write the Shapefile, ingest it, inspect, cross-check areas |
| `run_parks_integrity.py` | the harness: three parks, EPSG:25833, geometry area equal to the attribute |

## Run it

```bash
cd chapter2/exercise_1/exercise/files
python3 01_parks_integrity_check.py
```

It writes `output/city_parks.shp`, reads it back and prints the type, the geometry
column, the EPSG code and the preview; `run_parks_integrity.py` asserts 1 000, 5 000
and 2 500 m² on both sides of the comparison and exits non-zero if the CRS or any
area stops agreeing.

## What it produces

| path | what it is |
| --- | --- |
| `output/city_parks.shp` (+ sidecars) | the ingested layer |
| `output/parks_integrity.json` | CRS, geometry column, both area columns, the agreement flag |

```text
3. Coordinate Reference System (CRS) Inspection:
   CRS is defined.
   EPSG Code: 25833
...
5. Geometry Area vs Attribute Area (integrity check):
   geometry area (m2): [1000.0, 5000.0, 2500.0]
   attribute area_sqm: [1000, 5000, 2500]
   agree: True
```

## Notes

- A projected CRS is not decoration: it is what makes `geometry.area` comparable to
  a stored square-metre value. In EPSG:4326 the same check returns square degrees.
- The parks are 40×25, 100×50 and 50×50 metres, so the attribute table can be
  verified by hand rather than trusted.
- `isinstance(parks_gdf, gpd.GeoDataFrame)` is the cheap structural test; the geometry
  column name is the second half of it.
