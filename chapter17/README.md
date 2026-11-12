# Chapter 17 — Segment Anything (SAM) - Using Meta's AI to Segment Satellite Imagery

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script_sam_to_geojson_pi/example/` | `sam_to_geojson.py` | Opens a 1000 x 1000 one-metre chip of an industrial park, segments it with four bounding-box prompts, and converts the four masks into polygons whose rings are in UTM metres, saving them as GeoJSON with the CRS and each building's area. |
| `basic_code_example/example/` | `sam_point_prompt.py` | Encodes a 256 x 256 patch, sends a single positive point at `(x=120, y=65)`, and gets back three candidate masks with a score each. |
| `exercise_1/exercise/` | `georeferenced_export.py` | Segments one building from a point prompt on a georeferenced 100 x 100 patch, exports the mask as a GeoPackage polygon using the source image's own transform and CRS, and then checks that the vector file reports the CRS it started from. |
| `exercise_2_handling_ambiguity_with_bounding_b/exercise/` | `mask_selection.py` | Sends one bounding box at a wetland, receives three masks with different areas and scores, selects the most confident one that clears an area floor, and closes the one-pixel dropouts the segmenter left behind. |
| `exercise_3_the_modification_challenge_standar/exercise/` | `exporter_abc.py` | Defines an abstract `GeoAIExporter` with two abstract methods, a concrete `StructuredSAMExporter` that implements both, and a `BrokenExporter` that forgets `export_vector` — and shows that Python refuses to instantiate the third. |
| `exercise_4_interactive_challenge_robust_promp/exercise/` | `prompt_router.py` | Turns a user dictionary of optional prompt types into keyword arguments for `predict`, reading each key with `dict.get` so a missing one is an omission and not an exception. |
| `exercise_5_batch_processing_and_metadata_alig/exercise/` | `batch_mosaic.py` | Processes three 100 x 100 tiles with one box prompt each, writes every mask back as a GeoTIFF carrying *that tile's* transform and CRS, and merges the three into one mosaic. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter17/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter17/output/run_17.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
