# Exercise 1 — the five properties and the warning

## What it does

Writes a three-band 120 x 90 scene in UTM zone 33N at 30 m and a single-band scene
with the same geometry, then reads both with `inspect_raster_metadata`. The
three-band scene prints the five properties the exercise names and passes the POLA
check; the single-band scene prints the warning with its own band count. A third
call points at a path that does not exist and returns `None` after a readable
message.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise statement, exactly as the book prints it |
| `metadata_deep_dive.py` | the solution: two scenes, the reader, the three calls |
| `run_metadata_deep_dive.py` | the harness: properties, warning, missing-file branch |

## Run it

```bash
cd chapter11/exercise_1_geospatial_metadata_deep_dive/exercise/files
python3 metadata_deep_dive.py
```

It writes both scenes, reads the three-band one, the single-band one and a missing
path, and prints each result. `run_metadata_deep_dive.py` checks the CRS, count,
dimensions, transform and dtype, then the warning branch and the `None` return, and
exits non-zero when a property stops being reported.

```text
--- Wrote metadata_scene.tif and single_band_scene.tif ---

--- Geospatial Metadata Deep Dive ---
1. Coordinate Reference System (CRS): EPSG:32633
2. Total Number of Bands (count): 3
3. Dimensions (Width x Height): 120 x 90
4. Affine Transform Matrix:
| 30.00, 0.00, 300000.00|
| 0.00,-30.00, 5000000.00|
| 0.00, 0.00, 1.00|
5. Pixel Data Type (dtype): uint16
-----------------------------------
Verification successful: Raster has 3 or more bands.
...
WARNING: Band count (1) is insufficient for standard RGB/multispectral tasks.

Error opening raster file at does_not_exist.tif: RasterioIOError
```

## What it produces

| path | what it is |
| --- | --- |
| `output/metadata_scene.tif` | the three-band scene, 120 x 90, uint16 |
| `output/single_band_scene.tif` | the one-band scene that trips the warning |
| `output/metadata_deep_dive.json` | the harness's properties and branch results |

## Notes

- The book's solution read `IMAGE_PATH` that the reader did not have. The listing
  generates both scenes first, so the three branches are reachable on a clean machine.
- The warning is a branch of the reader, not a print in `main`: it fires whenever the
  dataset reports fewer than three bands, and the harness checks both sides.
- The error path prints the file name and the exception class, not the exception
  text: rasterio's message repeats the absolute path, and a book's terminal output
  should not carry the reader's home directory.
