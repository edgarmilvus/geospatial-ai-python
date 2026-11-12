# Exercise 5 — the live store and the twelve-column grid

## What it does

Adds a `dcc.Interval` that simulates a database query every 60 seconds and a
bootstrap grid that reflows from one column on a phone to a 25/75 split on a
desktop. The interval writes `live-raw-data-store`; the filtering stage lists that
store as an `Input`, so every refresh re-filters the new data against the controls
the user already set; the rendering stage still reads only the filtered store.

## The listings

| file | what it is |
| --- | --- |
| `live_dbc_dashboard.py` | the solution: deterministic cycle clock, DBC rows, three callbacks |
| `run_live_dbc.py` | the harness: cycle payloads, callback wiring, xs/lg columns |

## Run it

```bash
cd chapter10/exercise_5_integrating_external_data_and_layo/exercise/files
python3 live_dbc_dashboard.py
```

It builds the app for cycle 0 and writes the layout and the grid rules, then
returns. `run_live_dbc.py` calls `refresh_data(0)` and `refresh_data(1)`, checks
that the second payload differs and its timestamp is one minute later, reads the
column widths off the DBC components, and exits non-zero when a refresh stops
re-triggering the filter or the grid stops matching the specification.

```text
--- Dynamic GeoAI Dashboard (DBC & Live Data) ---
Cycle 0 at 2024-06-01 12:00:00: 500 detections
  v_test: 254 detections
  v_prod: 246 detections
Default filter v_test at 0.8-1.0 keeps 62 rows
Grid: controls xs=12/lg=3, map xs=12/lg=9, histogram xs=12 in its own row
Wrote output/dashboard_layout.json and live_dashboard_summary.json
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | the stores, the interval, the two DBC rows |
| `output/live_dashboard_summary.json` | cycle 0 counts, interval, grid rules |
| `output/live_dbc.json` | the harness's two cycles and the callback wiring |

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- The clock is simulated: cycle *n* is `2024-06-01 12:00:00` plus *n* minutes and
  seeds its generator with `1000 + n`. The original seeded from
  `datetime.now().timestamp()`, which cannot be re-run and whose timestamp is the
  reason its printed output changes every second.
- The refresh callback writes `live-raw-data-store`; the filter callback takes it as
  a third `Input`. That is the chaining the exercise asks for, and the harness checks
  it from `app.callback_map` rather than from the layout.
- `xs=12, lg=3` on the control column and `xs=12, lg=9` on the map column are read
  off the `Col` objects; the histogram's own row carries only `xs=12`.
