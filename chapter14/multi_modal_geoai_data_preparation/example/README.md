# Advanced example — raster and vector clipped to one protected zone

## What it does

Prepares both halves of a training set from one boundary. A 1000 × 1000 three-band
GeoTIFF covering 0..10 degrees is cut with `rasterio.mask` to the 4 × 4 degree
protected zone, and an infrastructure GeoJSON of three features is cut with
`gpd.clip` against the same polygon. The raster clip keeps the 400 × 400 pixel
window the zone covers at 0.01 degrees per pixel; the vector clip drops the feature
that lies outside and truncates the one that crosses the boundary. Both outputs are
written to `output/`, and the printed lines report the window, its bounds and how
many features survived.

## The listings

| file | what it is |
| --- | --- |
| `01_multi_modal_data_preparation.py` | the listing: simulated scene, ROI, raster mask, vector clip |
| `run_multi_modal_preparation.py` | the harness: 31 assertions on the window, the bounds, the feature set and determinism |

## Run it

```bash
cd chapter14/multi_modal_geoai_data_preparation/example/files
python3 01_multi_modal_data_preparation.py
```

It writes four files into `output/` — the scene, the infrastructure layer, the
clipped raster and the clipped GeoJSON — and prints the pixel window, its bounds and
the number of features kept; `run_multi_modal_preparation.py` asserts 400 × 400
pixels on bounds (3, 3, 7, 7), ids `[2, 3]`, both surviving areas at 0.25 square
degrees, and that a second run reproduces the same scene.

```text
Created dummy raster: large_satellite_image.tif (1000 x 1000 px, 3 bands)
Created dummy infrastructure vector: state_infrastructure.geojson (3 features)

--- Starting GeoAI Data Preparation (Clipping) ---
Step A: Clipping large raster to ROI boundary...
Raster clipping complete. Output saved to: roi_raster_clip.tif
  raster: 400 x 400 px, bounds (3.0, 3.0, 7.0, 7.0)

Step B: Clipping infrastructure vector data to ROI boundary...
Vector clipping complete. Output saved to: roi_vector_clip.geojson
  vector: 2 of 3 features kept, ids [2, 3]

Preparation complete. Clipped data ready for GeoAI model training.
```

## What it produces

| path | what it is |
| --- | --- |
| `output/large_satellite_image.tif` | the simulated three-band scene, 1000 × 1000 px |
| `output/state_infrastructure.geojson` | three infrastructure polygons, one outside the ROI |
| `output/roi_raster_clip.tif` | the 400 × 400 px window on the protected zone |
| `output/roi_vector_clip.geojson` | the two infrastructure features that reach the zone |
| `output/multi_modal_clip.json` | the window, both areas, the kept ids, the feature counts |

## Notes

- The scene is drawn from `np.random.default_rng(14)`, so the three-band tile is the
  same on every run; the harness proves that by running the listing a second time
  and comparing the array.
- `geopandas` 1.0 deprecates `GeoSeries.union_all()`; the listing calls
  `union_all()`, which returns the same combined clipping geometry without the
  warning.
- `all_touched=False` again: the four-degree ROI lands on pixel edges, so the window
  is exactly 400 pixels a side and no partial pixel is admitted.
