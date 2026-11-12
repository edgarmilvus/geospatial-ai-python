# Example 1 — a map of Mount Fuji, built from two constants

## What it does

Instantiates a `folium.Map` and saves it as a standalone HTML file. The whole
example is the viewport: `location=[35.3606, 138.7278]` in that order — latitude
first, the chapter's pitfall — and `zoom_start=12`, which is the regional view the
prose argues for. Everything else in the file is folium serialising that decision
into Leaflet's JavaScript.

## The listings

| file | what it is |
| --- | --- |
| `fuji_map_initialization.py` | the listing: two constants, one `Map`, one `save` |
| `run_fuji_map.py` | the harness: reads the HTML back and checks centre, zoom, tile source |

## Run it

```bash
cd chapter6/initializing_and_saving_a_folium_map/example/files
python3 fuji_map_initialization.py
```

It writes `output/06_02_fuji_map.html` and prints the path once. `run_fuji_map.py`
imports the listing, re-reads the file it wrote and asserts that the centre is Fuji's
two coordinates in the right order, that the map opens at zoom 12 and that its only
tile layer is OpenStreetMap; it exits non-zero if any of those stop being true.

```text
Interactive map successfully generated and saved to: output/06_02_fuji_map.html
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/06_02_fuji_map.html` | the standalone map: Leaflet initialised at the centre and zoom above |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/fuji_map.json` | the centre, the zoom, the tile template and the file size it measured |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline, and folium only writes the JavaScript that
  would request `tile.openstreetmap.org`.
- Folium also links Leaflet, jQuery and Bootstrap from CDNs rather than embedding
  them, so the document is portable but not self-hosting: no server is needed, a
  connection is.
- `06_02_fuji_map.html` is the chapter's own name for the artefact; the folder it
  lands in is the project's `output/`, so running the listing from any working
  directory writes the same file.
