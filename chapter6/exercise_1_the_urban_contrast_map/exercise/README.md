# Exercise 1 — San Francisco, and one layer the background recedes behind

## What it does

Answers the exercise in six lines of folium: a map centred on 37.7749 N, −122.4194 W
at zoom 12, OpenStreetMap on load, and a high-contrast layer named "High Contrast
Roads" in the control beside it. The point of the exercise is that the two layers
differ only in the string passed to `tiles` — the geometry, the centre and the zoom
are untouched.

## The listings

| file | what it is |
| --- | --- |
| `sf_contrast_map.py` | the solution: default OSM, a named OSM layer, the Toner layer, the control |
| `run_sf_contrast.py` | the harness: checks the three control entries and the templates behind them |

## Run it

```bash
cd chapter6/exercise_1_the_urban_contrast_map/exercise/files
python3 sf_contrast_map.py
```

It writes `output/sf_contrast_map.html`. `run_sf_contrast.py` asserts that the control
holds exactly three base layers, that "Standard Street Map" is OpenStreetMap, that
"High Contrast Roads" is the Toner template with its attribution, and that the map
opens on San Francisco at zoom 12; it exits non-zero if any of those stop matching.

```text
Saved output/sf_contrast_map.html: OpenStreetMap on load, the high-contrast layer one click away in the control.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/sf_contrast_map.html` | the map with its two named layers beside the default |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/sf_contrast.json` | centre, zoom, the three control names and their tile URLs |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- `folium.TileLayer('OpenStreetMap', ...)` adds a *second* copy of the same tile set
  under a readable name — the default layer is already there, so the control lists
  both. That is what the exercise asks for, and it is why three entries point at two
  templates.
- Stamen Toner is no longer a built-in name in folium 0.19; the listing passes its
  Stadia-hosted URL explicitly together with the attribution the template requires.
