# Exercise 3 — points or polygons from the same graph

## What it does

Simulates 200 detections, two thirds of which carry a GeoJSON segmentation mask,
and puts a checklist in front of one `dcc.Graph`. Ticked to points, the callback
returns `px.scatter_mapbox` with one trace per object type. Ticked to polygons, it
returns a `go.Figure` whose `layout.mapbox.layers` hold one `FeatureCollection` per
object type. An empty or doubled selection falls back to points.

## The listings

| file | what it is |
| --- | --- |
| `segmentation_toggle_dashboard.py` | the solution: masks built from the row's own point, two render paths |
| `run_segmentation_toggle.py` | the harness: layer counts, feature counts, colours, fallbacks |

## Run it

```bash
cd chapter10/exercise_3_advanced_modification_challenge_in/exercise/files
python3 segmentation_toggle_dashboard.py
```

It builds the app and writes the mask counts, then returns.
`run_segmentation_toggle.py` calls the callback in point mode, in polygon mode and
with the empty and doubled selections, checks that each polygon layer holds the
masks of its own class and that a mask sits on its row's coordinates, and exits
non-zero when the toggle stops changing the figure type.

```text
--- GeoAI Segmentation Visualization Toggle ---
Detections: 200; with a mask: 133
  building: 48 polygons (rgba(255, 0, 0, 0.5))
  road    : 46 polygons (rgba(0, 255, 0, 0.5))
  water   : 39 polygons (rgba(0, 0, 255, 0.5))
Wrote output/dashboard_layout.json and segmentation_summary.json
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dashboard_layout.json` | the checklist and the single graph |
| `output/segmentation_summary.json` | masks present, masks per class, colours |
| `output/segmentation_toggle.json` | the harness's per-layer feature counts and centre |

## Notes

- The Mapbox token is read from `MAPBOX_ACCESS_TOKEN`, with a placeholder when it
  is unset: the figures lay out either way, the tiles only load with a real token.

- The first draft drew the polygon coordinates from a second `np.random.uniform`
  call, so every mask was centred on some point other than the detection it was
  attached to. The listing draws latitude and longitude once and builds both the
  points and the masks from them; the harness asserts the mask's centre equals its
  row's coordinates.
- `layout.mapbox.layers` is what Plotly renders as arbitrary GeoJSON; the trace list
  is empty in polygon mode, which is why the harness counts layers instead of
  markers.
- Both boxes ticked means points, because the branch tests `'points' in mode_list`
  first. The requirement calls that the default, and the harness pins it.
