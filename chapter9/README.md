# Chapter 9 — Heatmaps - Visualizing Density and Traffic

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `basic_code_example/example/` | `drone_density_heatmap.py` | Turns a list of `[lat, lon]` pairs into a `folium.plugins.HeatMap` of 500 simulated drone sightings over Los Angeles: 70 per cent clustered tightly around downtown, 30 per cent at a suburban outpost, so the density actually varies. |
| `exercise_1_data_cleansing_type_conversion_and/exercise/` | `gps_cleansing_baseline_kde.py` | Builds the exercise's noisy taxi feed (50 000 rows, 5 per cent of them with a zero, a null or a numeric string in a coordinate), then runs the three gates the prompt asks for: parse to numeric, drop nulls and zeros, check the geographic bounds. |
| `exercise_2_dynamic_density_mapping_with_tempo/exercise/` | `dual_period_heatmap.py` | Builds a day of 20 000 pings whose location depends on the hour: rush-hour pings cluster over the residential district, mid-day pings over the central business district, and the rest of the day is background. |
| `exercise_3_integrating_environment_variables/exercise/` | `bandwidth_from_env.py` | Reads the input path from `GEOAI_DATA_PATH`, falls back to a generated default when the variable is unset, cleans whatever it read, and then sets the KDE bandwidth from the sample size with Silverman's `h = C · N^(-1/5)`. |
| `exercise_4_the_advanced_modification_challeng/exercise/` | `kernel_comparison.py` | Computes two density surfaces over the cleaned feed with one fixed bandwidth of 0.008 degrees: Gaussian from `scipy.stats.gaussian_kde`, and Epanechnikov from first principles with a `cKDTree` — the kernel is `2/π(1 − u²)` inside the radius and exactly zero outside it. |
| `exercise_5_preparing_heatmap_output_for_api_c/exercise/` | `heatmap_geojson_api.py` | Converts a binned density surface into the shape a web service would return: a GeoJSON `FeatureCollection` of 2 401 grid cells, each polygon carrying one numeric property, `density_score`, normalised so the hottest cell is 1.0. |
| `advanced_application_script/example/` | `gridded_kde_traffic.py` | Goes past "drop the points and let Leaflet smooth them": it fits a Gaussian kernel density estimate to 5 000 simulated ride-share pings, evaluates that surface on a 150 by 150 grid over the city, and hands the grid to `HeatMap` as `[lat, lon, intensity]` triples. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter9/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter9/output/run_9.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
