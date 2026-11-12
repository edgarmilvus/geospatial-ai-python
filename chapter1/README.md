# Chapter 1 — Coordinate Reference Systems (CRS) - Projections Explained

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `defining_and_inspecting_crs_objects/example/` | `01_crs_objects.py` | Loads EPSG:4326 and EPSG:3857 as `pyproj.CRS` objects and prints the properties that separate a geographic coordinate system from a projected one: the flag that decides which is which, the axis order, the unit each axis is measured in, and the name of the projection method. |
| `advanced_application_script/example/` | `01_parcel_area.py` | Builds one small parcel near San Francisco in WGS 84, measures it where it stands (square degrees, a number with no unit), transforms it into the local UTM zone, measures it again, and exports the projected frame. |
| `exercise_1_validating_and_standardizing_input/exercise/` | `01_crs_validation.py` | One function accepts whatever a caller might hand it — an integer code, an `EPSG:` string, a WKT definition, or nonsense — and either returns an integer EPSG code or raises the exercise's own `InvalidCRSDefinitionError`. |
| `exercise_2_high_precision_transformation_for/exercise/` | `01_precision_transform.py` | Takes a four-corner region of interest in longitude/latitude, derives the UTM zone from the coordinates instead of hard-coding it, moves all four points in a single bulk call, and then verifies the result by measuring the top edge in metres. |
| `exercise_3_geopandas_integration_and_projecti/exercise/` | `01_crs_alignment.py` | Builds two frames that cannot be compared — one in Web Mercator metres, one in WGS 84 degrees — moves both under a single equal-area target, and proves the fix by performing the overlay that would have failed before it. |
| `exercise_4_advanced_modification_analyzing_pr/exercise/` | `01_distortion.py` | Puts one 10 km square near the pole in Polar Stereographic, measures it there, re-projects it to Web Mercator, measures it again, and quantifies the difference. |
| `interactive_challenge_the_optimal_projection/exercise/` | `01_projection_selector.py` | Turns projection choice into a decision table: a measurement goal and a location go in, an EPSG code and a one-sentence justification come out. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter1/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter1/output/run_1.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
