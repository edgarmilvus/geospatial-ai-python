# Exercise 3 — the full pipeline, ending in a georeferenced GeoTIFF

## What it does

Generates a four-band scene with a patch of no signal, computes the index, rewrites
the input profile for a single float32 band, and writes the index so it inherits the
input's CRS, transform and grid.

## The listings

| file | what it is |
| --- | --- |
| `ndvi_geotiff_pipeline.py` | the solution: the profile change and the write |
| `run_ndvi_pipeline.py` | the harness: inherited metadata, the nodata patch, the values |

## Run it

```bash
cd chapter12/exercise_3_full_pipeline_execution_generating/exercise/files
python3 ndvi_geotiff_pipeline.py
```

It prints the three profile changes and the inherited CRS and transform, writes
`output/ndvi_map.tif`, then reports how many pixels are index and how many are
nodata. `run_ndvi_pipeline.py` asserts 25 facts — one band, float32, nodata −9999,
the input transform, 16 nodata pixels in the shadow patch — and exits non-zero if any
of them changes.

```text
--- Output Profile Changes ---
New Dtype: float32
New Band Count: 1
New NoData Value: -9999.0
CRS inherited: EPSG:32617
Transform inherited: (20.0, 0.0, 300000.0, 0.0, -20.0, 4001000.0)

Successfully wrote NDVI map to: output/ndvi_map.tif

--- Index Summary ---
Index pixels: 2484 of 2500 (16 nodata)
NDVI Min: 0.3382
NDVI Max: 0.7117
NDVI Mean: 0.5399
```

## What it produces

| path | what it is |
| --- | --- |
| `output/scene_multiband.tif` | the four-band input, 50×50 cells of 20 m, EPSG:32617 |
| `output/ndvi_map.tif` | the index: one float32 band, nodata −9999, same transform |
| `output/ndvi_pipeline.json` | written by the harness: both profiles and the values |

## Notes

- The profile is *copied* and then updated. Writing with the input profile unchanged
  would declare four bands and write one, which rasterio refuses.
- The 4×4 shadow patch is written as nodata, not as an index of 0.0. A zero index
  reads as bare soil; −9999 reads as "no observation".
- The transform is what carries the georeferencing: the product is not just the same
  size as the input, it occupies the same ground, with the west edge at 300 000 m
  easting and the north edge at 4 001 000 m northing.
