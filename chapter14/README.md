# Chapter 14 — Masking and Clipping - Extracting Region of Interest

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `2_basic_code_example_in_memory_raster_clippin/example/` | `01_in_memory_raster_clipping.py` | Builds a 10 × 10 integer raster whose values run 0 to 99, georeferences it with `Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0)` so one pixel spans one degree, and hands it to `rasterio.mask.mask` with a square polygon covering 3..7 on both axes. |
| `advanced_application_script_multi_modal_geoai/example/` | `01_multi_modal_data_preparation.py` | Prepares both halves of a training set from one boundary. |
| `exercise_1/exercise/` | `01_clip_raster_by_vector.py` | `clip_raster_by_vector(input_raster_path, mask_vector_path, output_raster_path)` loads a vector boundary with GeoPandas, compares its CRS with the raster's, and reprojects the boundary when they differ — before any geometry reaches `rasterio.mask`. |
| `exercise_2_vector_clipping_with_attribute_int/exercise/` | `01_vector_clip_attribute_integrity.py` | Builds four 10 × 10 degree counties (Alpha to Delta, 50 000 to 120 000 people), clips them with a 10 × 10 degree ROI that overlaps the first two, and then checks the result the way the exercise asks: it picks a clipped feature, finds the original row with the same `County_Name`, and compares the non-spatial columns. |
| `exercise_3_advanced_modification_challenge_co/exercise/` | `01_cli_preprocessor.py` | Turns the clipping logic into a utility with three positional paths on `sys.argv`. |
| `exercise_4_interactive_challenge_dynamic_meta/exercise/` | `02_clean_profile.py` | The exercise publishes a clipping profile and the six keys a GeoAI pipeline needs, and asks for one dictionary comprehension that keeps those keys and casts `width` and `height` to `int`. |
| `exercise_5_multi_roi_batch_clipping_simulatio/exercise/` | `01_batch_clip_rois.py` | Simulates the batch job a training set comes from: a 250 × 250 pixel scene covering 0..25 degrees is opened once, and three ROIs from a GeoDataFrame — `A001`, `B002`, `C003` — are cut out of it in a loop. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter14/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter14/output/run_14.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
