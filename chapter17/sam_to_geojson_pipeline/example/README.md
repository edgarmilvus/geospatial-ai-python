# Example 2 — box prompts to a georeferenced GeoJSON

## What it does

Opens a 1000 x 1000 one-metre chip of an industrial park, segments it with four bounding-box
prompts, and converts the four masks into polygons whose rings are in UTM metres, saving them
as GeoJSON with the CRS and each building's area. The segmenter is a stand-in; the reading,
the transforms and the write are the pipeline the chapter is about.

## The listings

| file | what it is |
| --- | --- |
| `sam_to_geojson.py` | the example: tile, box prompts, vectorize, GeoJSON |
| `run_sam_to_geojson.py` | the harness: refinement, areas, bounds, round trip |

## Run it

```bash
cd chapter17/sam_to_geojson_pipeline/example/files
python3 sam_to_geojson.py
```

It writes the tile on the first run, segments the four boxes, vectorizes and saves, printing
the image metadata, the mask count and the total area. `run_sam_to_geojson.py` asserts that
each mask is tighter than its box, that the four areas are 41 400, 32 400, 16 900 and
16 900 m², and that the rings sit on the tile's grid; it exits non-zero when the transform or
the refinement changes.

```text
Image loaded (shape (1000, 1000, 3)). CRS: EPSG:32617
[SAM] segment_anything is not installed; using the box-refinement stand-in.
Segmenter: stand-in
Starting segmentation with 4 bounding-box prompts...
Prediction complete. 4 masks of 1000 x 1000.

--- SUCCESS ---
Successfully mapped 4 features, 107,600 m² in total.
Results saved to mapped_warehouses.geojson
```

## What it produces

| path | what it is |
| --- | --- |
| `output/industrial_park.tif` | the 1000 x 1000 three-band chip, EPSG:32617, 1 m |
| `output/mapped_warehouses.geojson` | four polygons with `prompt_id`, `type`, `area_sqm` |
| `output/sam_to_geojson.json` | the prompts, mask areas, polygon areas and bounds |

## Notes

- **The inference is stubbed; the geospatial half is not.** The draft called
  `predictor.predict(box=prompts, ...)` against a method defined as
  `predict(self, box_prompts, ...)`, which is a `TypeError` on the first prompt — the script
  as printed could not run at all. The stand-in implements `predict(box=...)` the way the
  real predictor does, and returns one mask per box.
- `vectorize_masks` builds the frame from shapely geometries, not from GeoJSON feature
  dictionaries: `gpd.GeoDataFrame(features, crs=crs)` with `features` holding a `"geometry"`
  key per dict raises *"Assigning CRS to a GeoDataFrame without a geometry column"*. The
  harness caught it on the first run.
- The draft fell back to a placeholder transform when the tile was missing, which would have
  georeferenced four warehouses onto the null island. The tile is written on the first run
  instead, and the transform is always read from it.
- One feature per prompt, `prompt_id` from 0 to 3, so a downstream join can say which box
  produced which polygon.
- Needs `scipy`, `rasterio` and `geopandas`; no SAM package, no weights, no network. About
  0.4 s.
