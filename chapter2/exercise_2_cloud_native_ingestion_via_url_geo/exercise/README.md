# Exercise 2 — the cloud-native GeoJSON read, offline

## What it does

Shows the call the exercise is about — `gpd.read_file(source)` — where `source` may
be a path, an archive or a URL. The sandbox has no network, so the listing writes the
hourly wildfire-perimeter feed into `output/` and reads that file with the same
function. The configured URL stays in the listing as what a deployment would use;
swapping one string for the other is the whole difference.

## The listings

| file | what it is |
| --- | --- |
| `01_cloud_native_geojson.py` | the solution: build the feed, read it through one call, print shape and CRS |
| `run_cloud_native_read.py` | the harness: 2 x 3 shape, EPSG:4326, the two intensities, no network |

## Run it

```bash
cd chapter2/exercise_2_cloud_native_ingestion_via_url_geo/exercise/files
python3 01_cloud_native_geojson.py
```

It writes `output/wildfire_perimeters.geojson`, reads it with the same `gpd.read_file`
call a remote pipeline would use, prints the shape and the CRS; `run_cloud_native_read.py`
asserts `(2, 3)`, EPSG:4326 and both intensities, and exits non-zero if the feed stops
carrying them.

## What it produces

| path | what it is |
| --- | --- |
| `output/wildfire_perimeters.geojson` | the feed the read consumes |
| `output/cloud_native_read.json` | shape, columns, CRS, ids, intensities, `network_used: false` |

```text
3. GeoDataFrame Shape (Rows, Columns): (2, 3)

4. CRS Check:
   CRS: EPSG:4326
   Confirmed: CRS is WGS 84 (EPSG:4326), standard for GeoJSON.
```

## Notes

- `gpd.read_file()` handles the HTTP transfer itself (through GDAL's `/vsicurl/`);
  `requests` and a manual download are not needed and are not used here.
- GeoJSON is WGS 84 by specification (RFC 7946), so the CRS check is a confirmation
  rather than a discovery.
- The lesson that survives the offline build: the read call does not change when the
  source moves from a disk to a bucket.
