# Exercise 5 — the density surface as an API payload

## What it does

Converts a binned density surface into the shape a web service would return: a GeoJSON
`FeatureCollection` of 2 401 grid cells, each polygon carrying one numeric property,
`density_score`, normalised so the hottest cell is 1.0. A mock handler
`generate_heatmap_response(request_params)` answers a request — `time_filter` really filters
the pings, so a peak-hour request and an all-day request return different numbers over the
same grid.

## The listings

| file | what it is |
| --- | --- |
| `heatmap_geojson_api.py` | the solution: the grid, the payload, the handler, the validation |
| `run_heatmap_api.py` | the harness: the contract, the normalisation, two requests |

## Run it

```bash
cd chapter9/exercise_5_preparing_heatmap_output_for_api_c/exercise/files
python3 heatmap_geojson_api.py
```

It answers the peak-hour request, prints the first 500 characters of the payload and the
grid's statistics, and writes `output/heatmap_density.geojson`. `run_heatmap_api.py` parses
the payload, checks the 2 401 equal cells and the normalisation, and calls the handler a
second time to prove the filter reaches the histogram (32 assertions); it exits non-zero if a
property stops being called `density_score` or a score leaves 0..1.

```text
API Request received with parameters: {'time_filter': 'peak_hour', 'zoom_level': 14}
  peak_hour keeps 508 of 6000 pings (07:00-08:59)

--- Payload ---
Features: 2401 (a 49 by 49 grid over the pings' bounding box)
density_score: 0.0000 to 1.0000 (normalised, so the hottest cell is 1.0)
Cells with a non-zero score: 388 of 2401
Geometry: ['Polygon'], CRS EPSG:4326
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/heatmap_density.geojson` | the FeatureCollection, ready for any GIS tool or web map |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/heatmap_api.json` | features, cells with data, score range, both requests' counts |

## Notes

- `Point` was used and never imported in the book's fallback branch, so the path that
  rebuilds the frame from a CSV raised `NameError`.
- The book normalises the densities into `density_scores` and then stores the raw
  `density_matrix[i, j]` instead. The contract is `density_score`, so that is what travels.
- The handler now handles its request: `time_filter` selects the hours. Because the grid is
  rebuilt over the *selected* pings, a filtered request returns the same 2 401 cells over a
  smaller box — a finer grid, not fewer cells. That is a design decision worth knowing, not
  an accident.
- `np.histogram2d` is binning, not KDE: the exercise asks for the output *format*, and says
  so. The surface it serialises is the one the earlier exercises computed.
