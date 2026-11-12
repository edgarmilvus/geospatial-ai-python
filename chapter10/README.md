# Chapter 10 — Dashboards - Combining Maps with Plotly Dash

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script/example/` | `geoai_results_dashboard.py` | Simulates a hundred weekly GeoAI observations across three districts and four segmented classes, builds a twelve-feature GeoJSON skeleton, and wires a region dropdown and a class radio list to one callback that returns both a choropleth and a line chart. |
| `basic_code_example/example/` | `geoai_zone_dashboard.py` | Builds the smallest complete Dash application the chapter needs: a header, a dropdown of three zones, a `dcc.Graph` holding a `scatter_mapbox` figure, and a `html.Div` whose `children` a callback rewrites. |
| `exercise_1_building_the_foundational_geoai_da/exercise/` | `model_run_dashboard.py` | Simulates 500 land-cover detections across three model runs and three classes, then builds the dashboard the exercise asks for: a header, one dropdown populated from `model_run_id`, one `dcc.Graph`, and a callback that filters the frame and returns a `scatter_mapbox` coloured by class. |
| `exercise_2_implementing_cross_filtering_and_m/exercise/` | `cross_filter_dashboard.py` | Adds a confidence range slider and a date picker to the dashboard and puts both outputs behind one callback. |
| `exercise_3_advanced_modification_challenge_in/exercise/` | `segmentation_toggle_dashboard.py` | Simulates 200 detections, two thirds of which carry a GeoJSON segmentation mask, and puts a checklist in front of one `dcc.Graph`. |
| `exercise_4_interactive_challenge_optimizing_p/exercise/` | `state_store_dashboard.py` | Splits a 100 000-row dashboard into two callbacks joined by a hidden `dcc.Store`. |
| `exercise_5_integrating_external_data_and_layo/exercise/` | `live_dbc_dashboard.py` | Adds a `dcc.Interval` that simulates a database query every 60 seconds and a bootstrap grid that reflows from one column on a phone to a 25/75 split on a desktop. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter10/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter10/output/run_10.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
