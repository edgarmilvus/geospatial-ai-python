# Exercise 1 — a clip that reprojects its own mask

## What it does

`clip_raster_by_vector(input_raster_path, mask_vector_path, output_raster_path)`
loads a vector boundary with GeoPandas, compares its CRS with the raster's, and
reprojects the boundary when they differ — before any geometry reaches
`rasterio.mask`. It then masks with `crop=True`, `filled=True` and the source's own
NoData, updates the profile from the clipped array, and writes the result. The
listing's demo hands the function a 600 × 600 pixel UTM zone 10N tile and the same
2 km square expressed in WGS 84, so the mismatch branch is the one that runs.

## The listings

| file | what it is |
| --- | --- |
| `01_clip_raster_by_vector.py` | the listing: the clip function and its demo inputs |
| `run_clip_raster_by_vector.py` | the harness: 22 assertions on the branch, the CRS, the window and the values |

## Run it

```bash
cd chapter14/exercise_1_high_efficiency_raster_clipping_ut/exercise/files
python3 01_clip_raster_by_vector.py
```

It writes a UTM tile and a WGS 84 mask, clips the tile to the mask, then re-opens
the result and prints its CRS, its window and its bounds; `run_clip_raster_by_vector.py`
asserts that the reprojection branch ran, that 40 000 pixels carry data, that the
804-pixel collar around them is NoData, and that the data block is the source array's
own values rather than a resampling.

```text
Demo raster: utm_tile.tif (600 x 600 px, EPSG:32610)
Demo mask: roi_wgs84.geojson (EPSG:4326, 2 km x 2 km)
Reprojecting vector from EPSG:4326 to raster CRS EPSG:32610...
Successfully clipped raster saved to: utm_tile_clipped.tif
Clipped raster: 1 band(s), 202 x 202 px, CRS EPSG:32610, nodata -9999.0
Bounds: (500490.0, 4200490.0, 502510.0, 4202510.0)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/utm_tile.tif` | the 600 × 600 px source, 10 m pixels, EPSG:32610 |
| `output/roi_wgs84.geojson` | the 2 km ROI, stored in EPSG:4326 |
| `output/utm_tile_clipped.tif` | the 202 × 202 px clip: a 200 × 200 core plus a one-pixel collar |
| `output/clip_by_vector.json` | the CRS pair, the bounds, 40 000 data pixels, 804 NoData pixels |

## Notes

- The window is 202 pixels a side, not 200: the mask is reprojected from degrees and
  comes back a fraction of a metre wider than the 2 km square, so `rasterio` snaps
  the window outwards by one pixel on each side. The harness states that as a
  tolerance — `abs(edge − ROI edge) <= 10 m` — rather than pretending the clip is
  exact.
- `filled=True` is what puts NoData in the collar; with `filled=False` the array is
  a masked array and the same values arrive through the mask.
- The temporary GeoJSON carries WGS 84 deliberately. A mask already in the raster's
  CRS would never take the reprojection branch, and the exercise is about that
  branch.
