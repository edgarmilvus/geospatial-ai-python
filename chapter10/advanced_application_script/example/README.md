# Example 2 — one callback, two graphs

## What it does

Simulates a hundred weekly GeoAI observations across three districts and four
segmented classes, builds a twelve-feature GeoJSON skeleton, and wires a region
dropdown and a class radio list to one callback that returns both a choropleth and
a line chart. The callback filters the frame once; the map shows the summed area of
the selection, the chart shows its weekly history.

## The listings

| file | what it is |
| --- | --- |
| `geoai_results_dashboard.py` | the listing: seeded data, GeoJSON, layout, two-output callback |
| `run_results_dashboard.py` | the harness: row counts, map link, centre, chart order |

## Run it

```bash
cd chapter10/advanced_application_script/example/files
python3 geoai_results_dashboard.py
```

It builds the dashboard and writes what it would serve, then returns.
`run_results_dashboard.py` calls the callback for three combinations, checks the
map's linked id and summed area, the chart's row count and date order, and exits
non-zero when the map stops following the selected district.

```text
--- GeoAI Segmentation Results Monitor ---
Rows: 100; regions: 3; feature types: 4
GeoJSON features: 12
  District Alpha   Deforestation          12 rows
  District Alpha   Infrastructure Damage   3 rows
...
  District Gamma   Water Bodies            7 rows
Default view: District Gamma / Deforestation
Wrote output/dashboard_layout.json and dashboard_summary.json
Serve it for real with: python3 geoai_results_dashboard.py --serve
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | the component tree and the empty Graph placeholders |
| `output/dashboard_summary.json` | rows, combinations, rows per combination, total area |
| `output/geojson_features.json` | the twelve polygons the choropleth points at |
| `output/results_monitor.json` | the harness's measured selection, centre and counts |

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- The generator is seeded with `default_rng(7)`. The unseeded version printed a
  different thirteen rows per combination on every run, which makes the map's
  colour meaningless and the harness impossible to write.
- The region outline is looked up by name. Indexing `coords` by the position of a
  name in `df['Region'].unique()` gave District Gamma the Alpha polygon, because
  the random draw happens to put Gamma first.
- `--serve` opens the real server on 8050; the plain run only writes files.
- Plotly reads the GeoJSON handed to `choropleth_mapbox`, so the saved feature
  collection is the same object the browser receives, not a copy made for the file.
