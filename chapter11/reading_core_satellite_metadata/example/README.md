# Example 1 — write a GeoTIFF, then read its three pillars

## What it does

Writes the smallest valid single-band GeoTIFF the chapter can read: 100 columns by
80 rows over a one-degree box in EPSG:4326, uint16, constant 500, nodata 0. It then
opens it with the same context manager the chapter teaches and prints the CRS, the
affine transform, the dimensions, the band count and the dtype, followed by the
band's shape, type, minimum and maximum. The file is removed at the end of the run.

## The listings

| file | what it is |
| --- | --- |
| `read_scene_metadata.py` | the listing: `create_scene`, `inspect_scene`, `main` |
| `run_read_scene_metadata.py` | the harness: shape, dtype, CRS, transform, both bounds |

## Run it

```bash
cd chapter11/reading_core_satellite_metadata/example/files
python3 read_scene_metadata.py
```

It writes `output/basic_rasterio_scene.tif`, reads it back, prints its metadata and
removes the file. `run_read_scene_metadata.py` reads the metadata the functions
return and checks the geometry — 0.01 degrees per pixel, north edge at 0.8 — and
exits non-zero when a pillar changes.

```text
--- 1. Creating dummy file: basic_rasterio_scene.tif ---
Dummy GeoTIFF created successfully.

--- 2. Reading metadata and data using Rasterio ---
File Name: .../output/basic_rasterio_scene.tif
------------------------------
1. Coordinate System (CRS):
EPSG:4326
------------------------------
2. Affine Transform (Geo-T):
| 0.01, 0.00, 0.00|
| 0.00,-0.01, 0.80|
| 0.00, 0.00, 1.00|
------------------------------
3. Dimensions & Structure:
   Width (Columns): 100
   Height (Rows): 80
   Number of Bands: 1
   Pixel Data Type: uint16

4. Reading Band Data (Index 1)...
   Data shape read (H, W): (80, 100)
   Data type read: uint16
   Minimum pixel value: 500
   Maximum pixel value: 500

--- 3. Cleanup: Removed basic_rasterio_scene.tif ---
```

## What it produces

Written by the listing: `output/basic_rasterio_scene.tif` while it runs, deleted
before it exits.

Written by the harness:

| path | what it is |
| --- | --- |
| `output/scene_metadata.json` | shape, dtype, CRS, both transforms, bounds, pixel range |

## Notes

- `from_bounds(0, 0, 1, 0.8, width=100, height=80)` gives `a = 0.01` and
  `e = -0.01`: 100 columns across one degree, 80 rows down 0.8 degrees. The negative
  `e` is what makes row 0 the north edge.
- The pixel centre, not the pixel corner, is what a coordinate usually means:
  `AFFINE_TRANSFORM * (0.5, 0.5)` is `(0.005, 0.795)`, and the harness checks the
  inverse returns `(0.5, 0.5)`.
- The listing cleans up after itself, so a second run starts from an empty
  `output/`. The harness asserts the GeoTIFF is gone, not that it is present.
