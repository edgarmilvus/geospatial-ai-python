# Exercise 1 — one dropdown filters the map

## What it does

Simulates 500 land-cover detections across three model runs and three classes, then
builds the dashboard the exercise asks for: a header, one dropdown populated from
`model_run_id`, one `dcc.Graph`, and a callback that filters the frame and returns a
`scatter_mapbox` coloured by class. The empty-selection branch returns an empty map
instead of raising.

## The listings

| file | what it is |
| --- | --- |
| `model_run_dashboard.py` | the solution: seeded frame, layout, `update_map`, build report |
| `run_model_run_dashboard.py` | the harness: per-run counts, traces, coordinates, empty branch |

## Run it

```bash
cd chapter10/exercise_1_building_the_foundational_geoai_da/exercise/files
python3 model_run_dashboard.py
```

It builds the app, writes the layout and the per-run counts, and returns.
`run_model_run_dashboard.py` calls `update_map` for each of the three runs, checks
that the figure holds exactly that run's detections and three named traces, and
exits non-zero when a run loses a point or a class.

```text
--- GeoAI Model Comparison Dashboard ---
Detections: 500
  v1.0_2023: 162 detections
  v1.1_2024: 177 detections
  v1.2_2024: 161 detections
Classes: Forest, Urban, Water
Dropdown opens on: v1.1_2024
Wrote output/dashboard_layout.json and model_run_summary.json
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | the header, the control row and the graph |
| `output/model_run_summary.json` | rows, ids, counts per run, classes, default |
| `output/model_run_dashboard.json` | the harness's counts and default view |

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- The dropdown's options come from `data['model_run_id'].unique()`, so the control
  cannot offer a run the frame does not have. Its default is the first value, which
  is `v1.1_2024` on this seed.
- `update_map(None)` returns a figure built from an empty slice of the frame. The
  first draft called `px.scatter_mapbox(data.head(1))` with no `lat`/`lon`, which
  raises before returning a figure; the empty slice keeps the two columns.
- `--serve` serves the app on 8050; the plain run writes files and exits.
