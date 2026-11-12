# Exercise 2 — the Matterhorn, with the terrain as the default view

## What it does

Puts the topography first: the map is centred on 45.9766 N, 7.6585 E and loads with
the Stamen Terrain template, at zoom 14 — close enough to read the contours, wide
enough to keep the valleys in frame. A second layer is then added with
`folium.TileLayer` under the name "OpenTopoMap Style", which is plain OpenStreetMap
wearing a label: the exercise's way of rehearsing the class rather than the provider.

## The listings

| file | what it is |
| --- | --- |
| `alpine_terrain_map.py` | the solution: terrain default, named terrain layer, simulated topo layer |
| `run_alpine_terrain.py` | the harness: checks that the first tile layer really is the terrain |

## Run it

```bash
cd chapter6/exercise_2_the_alpine_terrain_explorer/exercise/files
python3 alpine_terrain_map.py
```

It writes `output/alpine_terrain.html`. `run_alpine_terrain.py` asserts that the first
tile template in the document — the one the map loads with — is the terrain one, that
the three control entries are the default plus the two named layers, and that
"OpenTopoMap Style" is OpenStreetMap under another name; it exits non-zero if the
default and the named layer stop agreeing.

```text
Saved output/alpine_terrain.html centred on the Matterhorn at zoom 14: terrain on load, the 'OpenTopoMap Style' layer one click away.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/alpine_terrain.html` | the terrain map with its second base layer |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/alpine_terrain.json` | centre, zoom, the three names and the templates behind them |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- The terrain template is Stadia's Stamen endpoint, passed as a URL because folium
  0.19 dropped the `"Stamen Terrain"` name; the attribution travels with it.
- The zoom is a judgement, not a constant: the exercise asks for something between 13
  and 15 and for a comment saying why. The harness accepts that range and then pins
  the 14 the solution chose.
