# Example 1 — a one-dropdown Dash dashboard

## What it does

Builds the smallest complete Dash application the chapter needs: a header, a
dropdown of three zones, a `dcc.Graph` holding a `scatter_mapbox` figure, and a
`html.Div` whose `children` a callback rewrites. The callback looks the selected
zone up in the three-row frame and returns a formatted `html.Pre`; the figure is
built once, before the layout, so the map is on screen at load time.

## The listings

| file | what it is |
| --- | --- |
| `geoai_zone_dashboard.py` | the listing: data, figure, layout, callback, build-and-report |
| `run_zone_dashboard.py` | the harness: layout tree, callback output, and the served page |

## Run it

```bash
cd chapter10/basic_code_example/example/files
python3 geoai_zone_dashboard.py
```

It builds the application, writes its layout and stops — no socket is opened.
`run_zone_dashboard.py` checks the layout, calls the callback for Zone B and Zone C,
serves the same app on an ephemeral port to read `/` and `/_dash-layout`, and exits
non-zero if any of those disagree.

```text
--- Minimal GeoAI Zone Dashboard ---
  Zone A: (34.05, -118.25) -> value 100
  Zone B: (34.10, -118.30) -> value 250
  Zone C: (34.15, -118.35) -> value 50
Layout children: 4
Callback registered for: ['selection-details.children']
Default selection: Zone A; map style carto-positron at zoom 10
Wrote output/dashboard_layout.json and index.html
Serve it for real with: python3 geoai_zone_dashboard.py --serve
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | the whole component tree, figure included |
| `output/index.html` | `app.index_string`, the template Dash fills per request |
| `output/zone_summary.json` | zones, coordinates, values, callback key |

Written by the harness: `output/zone_dashboard.json` (the callback's text, the
served status, the map style).

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- `python3 geoai_zone_dashboard.py` builds the app; it does not serve it. To serve
  the real thing, run `python3 geoai_zone_dashboard.py --serve` and open
  `http://127.0.0.1:8050`. The `--serve` branch is the only one that calls `app.run`.
- The harness starts the app with `werkzeug.serving.make_server` on port 0 and
  shuts it down after two requests. Port 0 means the OS picks a free port, so the
  check never collides with a dashboard a reader left running.
- `Plotly 6` still accepts `px.scatter_mapbox` but prints a deprecation warning;
  the figure is unchanged and the warning is the only thing on stderr.
- The callback is a plain function after Dash registers it, so the harness calls
  `update_details("Zone B")` directly. The decorator is what makes the server call
  it too, not the other way round.
