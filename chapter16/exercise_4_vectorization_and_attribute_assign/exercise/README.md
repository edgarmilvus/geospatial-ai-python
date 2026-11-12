# Exercise 4 — mask to GeoDataFrame, areas in square metres

## What it does

Writes a georeferenced one-metre mask with two footprints, vectorizes it with
`rasterio.features.shapes`, and builds a GeoDataFrame carrying each polygon's area in m²
and its centroid in projected metres, then writes that frame to a GeoPackage and reads it
back to prove the CRS survived.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_4.py` | the book's required structure, bodies left as `pass` |
| `raster_to_vector.py` | the solution: mask on disk, conversion, attributes, GeoPackage |
| `run_raster_to_vector.py` | the harness: areas, centroids, bounds, round trip |

## Run it

```bash
cd chapter16/exercise_4_vectorization_and_attribute_assign/exercise/files
python3 raster_to_vector.py
```

It writes the mask and the GeoPackage, printing each polygon's area and centroid and the
union bounds. `run_raster_to_vector.py` asserts that 650 mask pixels become 650 m² across two
polygons, that the centroids are the rectangle centres, and that the GeoPackage returns the
source CRS; it exits non-zero when a mask with nothing in it crashes or a CRS is lost.

```text
Wrote building_mask.tif: 100 x 100 at 1 m, EPSG:32617
Mask pixels: 650 of 10000

2 building polygons, CRS EPSG:32617
  #0: area 200 m², centroid (400030.0, 4499975.0)
  #1: area 450 m², centroid (400065.0, 4499932.5)
Total footprint: 650 m²
Union bounds: (400020.0, 4499925.0, 400080.0, 4499980.0)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/building_mask.tif` | the 100 x 100 uint8 mask, EPSG:32617, 1 m pixels |
| `output/buildings.gpkg` | the two polygons with `area_sqm`, `centroid_x`, `centroid_y` |
| `output/empty_mask.tif` | the mask with nothing in it, written by the harness |
| `output/raster_to_vector.json` | the areas, centroids, bounds and CRS |

## Notes

- The draft returned a `MockRasterFile` and never opened a path, so `binary_mask_path` was
  decoration. Here the mask is a real GeoTIFF: the transform and the CRS come from
  `rasterio.open`, which is the only way the exercise's claim — that the output is
  georeferenced off the *source* — is true.
- The area is `polygon.area` and nothing else. The rings are already in metres because
  `shapes(transform=...)` wrote them there; multiplying by the pixel area again would report
  square metres squared.
- An empty mask returns an empty frame that still carries the CRS, which the harness checks:
  a pipeline that silently drops the CRS when there are no features breaks a join three steps
  later.
- No torch, no network, under half a second.
