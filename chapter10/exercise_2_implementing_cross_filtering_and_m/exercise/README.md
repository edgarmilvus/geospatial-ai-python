# Exercise 2 — the map obeys three filters, the histogram two

## What it does

Adds a confidence range slider and a date picker to the dashboard and puts both
outputs behind one callback. The map is filtered by model run, date range **and**
confidence band; the histogram is filtered by model run and date range only, so the
analyst keeps the whole population in view while the map shows a subset of it.

## The listings

| file | what it is |
| --- | --- |
| `cross_filter_dashboard.py` | the solution: 1 000 detections, three controls, differential filtering |
| `run_cross_filter.py` | the harness: histogram invariance, map counts, date narrowing |

## Run it

```bash
cd chapter10/exercise_2_implementing_cross_filtering_and_m/exercise/files
python3 cross_filter_dashboard.py
```

It builds the app, computes the default split and writes the layout, then returns.
`run_cross_filter.py` calls the callback with the default band, a full band and a
band that matches nothing, checking that the histogram's total never moves with the
slider while the map's does, and exits non-zero when the two outputs stop being
differentially filtered.

```text
--- GeoAI Cross-Filtering Dashboard ---
Rows: 1000; model runs: 3
Dates: 2024-01-01 to 2024-01-30 (30 days)
Default run v1.2_2024: histogram 344 rows, map 115 rows at confidence 0.7-1.0
Wrote output/dashboard_layout.json and cross_filter_summary.json
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | the three controls and the two graphs |
| `output/cross_filter_summary.json` | window, runs, default split, confidence range |
| `output/cross_filter.json` | the harness's measured totals and first-week subset |

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- The invariances are the exercise: a callback that filters `map_df` first and then
  derives `histogram_df` from it still "works" on screen and silently breaks the
  statistical context. The harness checks the direction of the derivation.
- A confidence band of `[1.0, 1.0]` selects nothing because the scores are drawn
  from `uniform(0, 1)`; the map empties and the histogram stays at 344 rows.
- The histogram's rows are counted from the figure Plotly 6 returns: it ships the
  raw sample to the browser, so the trace's `y` is `None` and the count comes from
  `x`. The harness handles both shapes.
