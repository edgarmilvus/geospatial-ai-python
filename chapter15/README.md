# Chapter 15 — Time Series from Space - Tracking Deforestation over Time

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script/example/` | `01_deforestation_date_detection.py` | Builds a sixty-month Sentinel-2 cube (2019-01 to 2023-12) of 50 × 50 pixels, injects a clear-cut in a 10 × 10 block from month 30, converts both bands to NDVI, and then dates the change per pixel. |
| `basic_code_example/example/` | `01_ndvi_time_series_stack.py` | Simulates three observations of a 10 × 10 pixel patch as `(Time, Height, Width, Bands)`, with Red at band 0 and NIR at band 1, and walks the time axis once. |
| `exercise_1/exercise/` | `01_ndvi_cube.py` | Simulates a five-date data cube over 100 × 100 pixels with a labelled `band` axis, transposes it to `(time, y, x, band)`, and reduces it to a single NDVI `DataArray` with three dimensions. |
| `exercise_2_cloud_masking_and_temporal_gap_fil/exercise/` | `02_cloud_mask_gap_fill.py` | Builds a five-date NDVI cube and a matching QA band, one contaminated observation in ten, and forces two interior observations of pixel (50, 50) to be cloudy so a gap appears somewhere interpolation can reach. |
| `exercise_3_defining_baseline_and_monitoring_p/exercise/` | `02_baseline_monitoring.py` | Takes an alert date and builds the two windows around it with `timedelta`: an eighteen-month baseline that ends the day before the alert, and a six-month monitoring window that starts on it. |
| `exercise_4_advanced_challenge_modifying_spect/exercise/` | `02_config_merge.py` | Defines a default configuration for a spectral-trajectory model and a second dictionary of degradation parameters, then merges the second into the first with `dict.update`. |
| `exercise_5_interactive_challenge_quantifying/exercise/` | `02_annual_area_plot.py` | Simulates three annual boolean deforestation maps over a 500 × 500 pixel scene, at 1 %, 2 % and 3 % loss, and converts each map's `True` count into hectares at 100 m² per pixel. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter15/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter15/output/run_15.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
