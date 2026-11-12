# Chapter 20 — Capstone Project - Automated Disaster Damage Assessment with AI

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script/example/` | `01_adda_pipeline.py` | Runs the capstone pipeline over a pre- and post-disaster scene: it aligns the two rasters, segments the buildings, classifies each one's damage, summarises the classes, exports the assessment and answers a question about it. |
| `basic_code_example/example/` | `01_geo_distance_tool.py` | Wraps one calculation a disaster agent needs immediately — how far apart two points are — as a tool with a schema, a unit and a return value a model can read. |
| `exercise_1_implementing_robust_data_ingestion/exercise/` | `01_geojson_subsetter.py` | A loader that keeps going when the input is wrong: it validates before parsing, returns an empty result instead of raising when nothing matches, and raises the exercise's own `DataProcessingError` when the file itself is unusable. |
| `exercise_2_configuring_the_geoai_agent_pipeli/exercise/` | `01_agent_configuration.py` | Loads the pipeline's settings from the environment and refuses to start when they are incomplete, naming **every** missing variable in one message. |
| `exercise_3_modifying_the_damage_classificatio/exercise/` | `01_multitemporal_damage.py` | Extends the classifier from one pair of scenes to a time series: it computes NDVI before and after, takes the change, and assigns each building a damage class from the change and from whether the structure is still there. |
| `exercise_4_interactive_challenge_implementing/exercise/` | `01_async_gis_connection.py` | Wraps a remote GIS session in an asynchronous context manager: acquiring is an `await`, releasing is an `await`, and the release happens on the failing path too. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter20/run_offline.sh
```

`run_offline.sh` runs the 6 harnesses and prints one line per harness;
the log is written to `chapter20/output/run_20.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
