# Chapter 7 — Markers and Popups - Adding Data to the Map

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script_dynamic_geoai_rep/example/` | `geoai_detection_map.py` | Simulates the output of a dumping-site detector over Los Angeles and renders it as an interactive report: 50 points with confidence scores, clustered so the map stays readable, each marker coloured and badged by its band (≥ 0.90 confirmed, ≥ 0.75 review, below that verify), and each popup an HTML report card inside an `IFrame` so its CSS cannot leak into the map. |
| `basic_code_example/example/` | `marker_with_popup.py` | Puts a single GeoAI detection on the map: a marker at the Eiffel Tower, an explicit `folium.Popup` with `max_width=350`, and a tooltip that appears on hover. |
| `exercise_1/exercise/` | `drone_severity_markers.py` | Turns a table of drone detections into a map a field team can triage at a glance: four severity levels, four colours, four icons, and a popup that states the level in words. |
| `exercise_2_dynamic_popups_for_geoai_classific/exercise/` | `classification_popups.py` | Takes five classified points and gives each one a popup built with f-strings: the class as a heading, the confidence multiplied by 100 and rounded to one decimal, the analysis date in italics, and the confidence coloured green above 0.8 and red at or below it. |
| `exercise_3_conditional_clustering_and_priorit/exercise/` | `conditional_cluster_icons.py` | Clusters 500 simulated utility defects and then overrides the cluster icon from inside Leaflet: `icon_create_function` walks the markers the cluster contains, reads their popup text, and if any of them says `Priority: 1` it swaps the default blue disc for a red, larger one. |
| `exercise_4_interactive_challenge_time_sensiti/exercise/` | `sensor_inspection_filter.py` | Simulates 15 sensors with inspection dates relative to today, asks for a maximum number of days since the last inspection, and paints every sensor red — with an exclamation icon and an OVERDUE popup — once its date falls behind the cutoff. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter7/run_offline.sh
```

`run_offline.sh` runs the 6 harnesses and prints one line per harness;
the log is written to `chapter7/output/run_7.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
