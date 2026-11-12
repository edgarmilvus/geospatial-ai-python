# Exercise 2 — reading bands 3 and 4 out of a four-band GeoTIFF

## What it does

Writes a four-band vendor-style GeoTIFF (Blue, Green, Red, NIR as uint16 digital
numbers), opens it, reads only bands 3 and 4 as float32, and inspects the CRS and the
affine transform the next exercise needs in order to write the product back.

## The listings

| file | what it is |
| --- | --- |
| `read_bands_rasterio.py` | the solution: scene, band extraction, metadata |
| `run_read_bands.py` | the harness: the 1-based index, the DN windows, the georeferencing |
| `prompt_sketch_exercise_2.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter12/exercise_2_geospatial_integration_reading_ban/exercise/files
python3 read_bands_rasterio.py
```

It prints both array shapes, the band count, the CRS, the transform and the DN range
of each band. `run_read_bands.py` asserts 27 facts — band 3 is not band 1, the scene
holds four bands, the cell is 0.02° over 10°W-9°W and 40°N-41°N, NIR sits above
4000 DN — and exits non-zero if any of them changes.

```text
--- Array Dimensions Check ---
Red Array Shape: (50, 50)
NIR Array Shape: (50, 50)
Aligned for band math: True

--- Geospatial Metadata Inspection ---
Band Count: 4
Data Type: uint16
Coordinate Reference System (CRS): EPSG:4326
Geospatial Transform Matrix (Affine):
| 0.02, 0.00,-10.00|
| 0.00,-0.02, 41.00|
| 0.00, 0.00, 1.00|

--- Digital Number Ranges ---
Red (band 3): 1000 to 1999
NIR (band 4): 4000 to 5999
```

## What it produces

| path | what it is |
| --- | --- |
| `output/image_001.tif` | the four-band uint16 scene, 50×50 cells of 0.02° |
| `output/bands_read.json` | written by the harness: shapes, band indices, profile, DN ranges |

## Notes

- `src.read(n)` is 1-based. Reading index 1 returns Blue, not Red, and nothing warns
  you: the array is the right shape and the wrong band.
- The scene is kept rather than deleted, so the run can be inspected afterwards and
  the next exercise can be compared against the same numbers.
- 0.02° cells are fine for a *picture* and wrong for a *distance*: they are about
  2.2 km east-west and 2.2 km north-south at this latitude, and they are not square
  in metres everywhere.
