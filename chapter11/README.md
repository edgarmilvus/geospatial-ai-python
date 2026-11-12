# Chapter 11 — Introduction to Rasterio - Reading Satellite Imagery

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script_efficient_geochip/example/` | `geochip_extraction.py` | Writes a four-band 1024 x 1024 scene in UTM zone 17N at 10 m resolution, opens it, computes the window that centres a 256-pixel chip, derives that window's own affine transform, and reads three bands through it. |
| `basic_code_example_reading_core_satellite_met/example/` | `read_scene_metadata.py` | Writes the smallest valid single-band GeoTIFF the chapter can read: 100 columns by 80 rows over a one-degree box in EPSG:4326, uint16, constant 500, nodata 0. |
| `exercise_1/exercise/` | `metadata_deep_dive.py` | Writes a three-band 120 x 90 scene in UTM zone 33N at 30 m and a single-band scene with the same geometry, then reads both with `inspect_raster_metadata`. |
| `exercise_2_efficient_windowed_reading_and_arr/exercise/` | `windowed_tile_read.py` | Writes an 800 x 600 four-band scene at 20 m, computes the window that centres a 512-pixel tile — 144 columns in, 44 rows down — and reads the first three bands through it, cast to `float32`. |
| `exercise_3_advanced_modification_challenge_si/exercise/` | `downsample_retransform.py` | Writes a 960 x 720 three-band scene at 10 m, reads it back through `out_shape=(180, 240)` with nearest-neighbour resampling, and computes the transform that belongs to the coarse grid: the original scaled by four. |
| `exercise_4_interactive_band_selection_and_err/exercise/` | `band_selection_reader.py` | Writes a four-band 200 x 150 scene whose bands have deliberately different ranges (band 2 lives between 200 and 599), then reads a band chosen by the caller. |
| `exercise_5_creating_a_geotiff_template_for_ge/exercise/` | `classification_template.py` | Writes a four-band uint16 input, copies its profile, and changes the four keys the exercise names: `count` to 1, `dtype` to uint8, `nodata` to 255 and `interleave` to `band`. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter11/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter11/output/run_11.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
