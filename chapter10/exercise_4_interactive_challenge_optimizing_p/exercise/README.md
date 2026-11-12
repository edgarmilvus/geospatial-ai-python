# Exercise 4 — filter once, render twice

## What it does

Splits a 100 000-row dashboard into two callbacks joined by a hidden `dcc.Store`.
Stage 1 reads the serialised raw payload as `State`, filters it against the
dropdown and the slider, and writes the surviving rows to `filtered-data-store`.
Stage 2 reads only that store and builds the map and the histogram, so it never
touches a control and never sees the full frame.

## The listings

| file | what it is |
| --- | --- |
| `state_store_dashboard.py` | the solution: 100 000 rows, two stores, two callback stages |
| `run_state_store.py` | the harness: callback wiring, filtered counts, loading branch |

## Run it

```bash
cd chapter10/exercise_4_interactive_challenge_optimizing_p/exercise/files
python3 state_store_dashboard.py
```

It builds the app, filters the default view once and writes the layout and the
summary, then returns. `run_state_store.py` reads both callback specifications from
`app.callback_map`, runs the two stages in order, checks that the figures hold
exactly the filtered rows, and exits non-zero if stage 2 starts taking a user input
or stage 1 starts taking the raw payload as an `Input`.

```text
--- Performance Optimized Dashboard (100K Detections) ---
Raw rows: 100000; serialised: 6207 KiB
  v_test: 50007 detections
  v_prod: 49993 detections
Default filter v_prod at 0.8-1.0 keeps 10128 rows (9.9x smaller)
Wrote output/dashboard_layout.json and state_store_summary.json
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | both stores, both controls, both graphs |
| `output/state_store_summary.json` | raw rows, payload size, filtered rows, reduction |
| `output/state_store.json` | the harness's stage inputs, state and figures |

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- The payload is 6 207 KiB of JSON in the browser. That is the point of the split: the
  browser keeps the raw rows, Dash sends only the inputs back, and the server returns
  the 10 128 filtered rows — a 9.9x smaller reply.
- Stage 2's specification is `[{'id': 'filtered-data-store'}]` and its `state` list
  is empty. The harness reads those two lists rather than trusting a comment.
- `pd.read_json` is given a `StringIO`, not the bare string: pandas 2.2 warns that a
  literal string may be a path, and a 6 MB payload is not a path.
- The loading branch uses an empty slice of the frame, because `px.histogram` with no
  data and a title raises on Plotly 6.
