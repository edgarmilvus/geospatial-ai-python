# Example 1 — one marker, one popup, one deliberate offset

## What it does

Puts a single GeoAI detection on the map: a marker at the Eiffel Tower, an explicit
`folium.Popup` with `max_width=350`, and a tooltip that appears on hover. The map is
centred 0.005° **north** of the marker on purpose, so the marker sits below the centre
of the window where the zoom buttons cannot cover it. It is the chapter's smallest
complete workflow: data, map, popup, marker, save.

## The listings

| file | what it is |
| --- | --- |
| `marker_with_popup.py` | the listing: constants, map, popup, marker, save |
| `run_marker_popup.py` | the harness: reads the marker, the centre and the popup out of the HTML |

## Run it

```bash
cd chapter7/basic_code_example/example/files
python3 marker_with_popup.py
```

It writes `output/basic_marker_map.html` and prints the path once. `run_marker_popup.py`
asserts that the marker sits on `[48.8584, 2.2945]` in that order, that the centre is
the offset latitude rather than the point, that the zoom is 15 and that the popup
sentence is in the document; it exits non-zero if any of those stop being true.

```text
Interactive map successfully generated: output/basic_marker_map.html
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/basic_marker_map.html` | the standalone map with its single marker |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/marker_popup.json` | the centre, the zoom, the marker position, the popup text |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- 48.8584 + 0.005 is 48.863400000000006 in binary floating point, which is why the
  centre is compared with a tolerance instead of a string.
- The popup is wrapped in a `folium.Popup` object rather than passed as a bare string
  precisely so `max_width` can be set; the harness reads that value back off the
  object.
