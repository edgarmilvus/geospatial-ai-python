# Example 2 — fifty detections, three confidence bands, one clustered report map

## What it does

Simulates the output of a dumping-site detector over Los Angeles and renders it as an
interactive report: 50 points with confidence scores, clustered so the map stays
readable, each marker coloured and badged by its band (≥ 0.90 confirmed, ≥ 0.75 review,
below that verify), and each popup an HTML report card inside an `IFrame` so its CSS
cannot leak into the map.

The data is generated rather than downloaded, and the seed is fixed, so two runs
produce the same 50 sites and the same band counts.

## The listings

| file | what it is |
| --- | --- |
| `geoai_detection_map.py` | the listing: data generation, popup template, clustered map |
| `run_geoai_detections.py` | the harness: rebuilds the frame and checks the map against it |

## Run it

```bash
cd chapter7/advanced_application_script_dynamic_geoai_rep/example/files
python3 geoai_detection_map.py
```

It generates the detections and writes `output/geoai_detection_map.html`.
`run_geoai_detections.py` calls the two functions the main block calls, then asserts
that the frame is 50 sites in the configured box, that two runs are identical, that the
13/14/23 band split reappears as marker colours and as popup badges, and that the
cluster group stops clustering at zoom 14; it exits non-zero if the styling and the
data disagree.

```text
Map saved successfully to output/geoai_detection_map.html
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/geoai_detection_map.html` | the clustered map with 50 iframe popups |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/geoai_detection_map.json` | centre, zoom, site count, band counts, marker and popup totals |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- Two copies of the same threshold decide the look: `create_rich_popup_html` picks the
  badge and `map_geoai_detections` picks the icon. They are separate `if` chains, which
  is why the harness counts both and compares them with the data instead of trusting
  one.
- Popup HTML is stored base64-encoded in a `data:` URI, so any check on popup text has
  to decode the iframe first.
- `disableClusteringAtZoom: 14` is a Leaflet option, not Python: the harness can only
  assert that it reached the document.
