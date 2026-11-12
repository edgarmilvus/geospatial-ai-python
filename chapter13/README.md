# Chapter 13 — Elevation Models - Analyzing Terrain and Slopes

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `geoai_feature_engineering_from_dems/example/` | `terrain_feature_stack.py` | Derives slope, aspect and profile curvature from a DEM, standardizes each one with `StandardScaler`, stacks the three into a channel-first array, writes a three-band GeoTIFF for a model and a hillshade plus a PNG for a reader. |
| `calculating_terrain_slope/example/` | `slope_from_dem.py` | Builds a 100×100 synthetic DEM — a gentle 4.09° ramp with a Gaussian hill near the centre — takes the gradient in metres per metre, combines the two partial derivatives into a tangent, and converts it to degrees. |
| `exercise_1_dem_ingestion_resampling_and_metad/exercise/` | `resample_dem.py` | Writes a 1000×1000 DEM at 1 m, inspects its metadata, computes the new grid and the new transform, resamples with bilinear interpolation, verifies that the mean and the standard deviation survived, and writes the 100×100 result at 10 m. |
| `exercise_2_comparative_analysis_of_slope_calc/exercise/` | `slope_methods.py` | Computes slope twice on the same 500×500 DEM: once with NumPy's central difference, once with Horn's 3×3 kernel. |
| `exercise_3_hydrological_feature_engineering_t/exercise/` | `twi_d8.py` | Routes flow with D8 on a hillslope that falls to the east, accumulates the cells draining through each one, converts the accumulation into a specific catchment area, and combines it with the local slope into TWI = ln(As / tan β). |
| `exercise_4_the_geoai_feature_stack_modificati/exercise/` | `feature_stack_curvature.py` | Derives four layers from a DEM — elevation, slope, aspect and profile curvature — with a hill and a hollow in the scene, z-scores the three continuous ones, leaves aspect raw, and stacks them as a four-channel array and a four-band GeoTIFF. |
| `interactive_challenge_handling_cyclical_data/exercise/` | `aspect_cyclic.py` | Turns a compass bearing into two continuous features, sin and cos of the aspect in radians, so that 359° and 1° are close in the feature space instead of 358 apart. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter13/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter13/output/run_13.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
