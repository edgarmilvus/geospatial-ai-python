# Example 2 — from logits to GeoJSON on a georeferenced chip

## What it does

Runs a 512 x 512 ten-metre chip through a segmentation model, thresholds the probability
map at 0.5, and turns the mask into five GeoJSON polygons whose rings are in UTM metres,
carrying their area in m². It is the raster-to-vector half of the chapter: the model is
the stand-in, the georeferencing is real.

## The listings

| file | what it is |
| --- | --- |
| `raster_to_vector_pipeline.py` | the example: tile, inference, threshold, vectorize, save |
| `run_raster_to_vector_pipeline.py` | the harness: logits, mask count, areas, bounds |

## Run it

```bash
cd chapter16/raster_to_vector_building_detection/example/files
python3 raster_to_vector_pipeline.py
```

It writes the chip on the first run, predicts, vectorizes and saves the GeoJSON, printing
the logit range, the pixel count and the polygon total. `run_raster_to_vector_pipeline.py`
asserts that the mask covers the 11 900 roof pixels, that the five areas are the five
rectangle areas at 100 m² per pixel, and that the rings sit on the chip's grid; it exits
non-zero when the transform or the threshold moves.

```text
[Data Load] Image shape: (512, 512, 3). CRS: EPSG:32617
[Data Load] Pixel size: 10.0 m, origin (600000, 4200000)
[SimpleBuildingDetector] Stand-in weights loaded (threshold at DN 191).
[Inference] Logit range [-4.76, 2.20], 11900 pixels above p = 0.5
[Vectorization] Detected 5 building polygons, 1,190,000 m² in total.
[Success] GeoJSON written to detected_buildings.geojson
```

## What it produces

| path | what it is |
| --- | --- |
| `output/industrial_tile.tif` | the 512 x 512 chip, three uint8 bands, EPSG:32617 |
| `output/detected_buildings.geojson` | five polygons with `building_id`, `class`, `area_m2` |
| `output/raster_to_vector.json` | the harness's logit range, areas and bounds |

## Notes

- **The trained network is the boundary, and it is stubbed.** `load_mock_weights` writes
  weights that make the model a brightness detector — the response a small U-Net converges
  to on this kind of chip — and says so in a comment. Everything after the logits is the
  book's pipeline, unchanged: sigmoid, 0.5, `rasterio.features.shapes`, GeoJSON.
- The draft was in EPSG:4326, where `polygon.area` is square degrees and 1 190 000 m²
  becomes 0.0001. The chip is EPSG:32617 at 10 m so that the areas are the number a GIS
  expects, and the polygons are 1.19 km² of roof in a 26 km² tile.
- `shapes` already returns rings in map coordinates: multiplying the shoelace area by the
  pixel area again is the double-count that inflated the draft to 119 km².
- The draft deleted its own output at the end; this one leaves both files for inspection.
  Runs in about a second on CPU.
- Needs `torch` and `rasterio`. Without `torch` the harness prints `skip` with the install
  command and ends green.
