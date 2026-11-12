# Exercise 3 (interactive challenge) — three aesthetics over Rio de Janeiro

## What it does

One city, three visual languages: the readable street map, the watercolour, and the
dark background meant for light-coloured data. All three are base layers, so the
control renders them as radio buttons and only one is ever drawn. Rio is centred on
−22.9068, −43.1729 at zoom 11 — a view wide enough to hold the bay, the beaches and
the mountains behind them.

## The listings

| file | what it is |
| --- | --- |
| `rio_aesthetic_switcher.py` | the solution: three named layers, one control |
| `run_rio_switcher.py` | the harness: checks the three names, the three templates, the view |

## Run it

```bash
cd chapter6/exercise_3_the_coastal_aesthetic_switcher_int/exercise/files
python3 rio_aesthetic_switcher.py
```

It writes `output/rio_aesthetic_switcher.html`. `run_rio_switcher.py` asserts that the
control lists the three required names, that each name resolves to a different
template (watercolour and dark included), and that the map opens on Rio at zoom 11; it
exits non-zero if a name and its template stop agreeing.

```text
Saved output/rio_aesthetic_switcher.html over Rio de Janeiro at zoom 11: OpenStreetMap on load, watercolour and dark context one click away.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/rio_aesthetic_switcher.html` | the map with three switchable aesthetics |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/rio_switcher.json` | centre, zoom, the four control names, their tile URLs |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- The watercolour style is Stadia's Stamen endpoint, written out as a URL with its
  attribution because folium 0.19 no longer ships the name.
- CartoDB Dark Matter is still a built-in name and still works, but folium 0.19 warns
  that the CartoDB basemaps want an API key — the layer is written into the document
  either way, the tiles are what need the key.
- Four entries, three aesthetics: the map's own default OpenStreetMap layer sits above
  the three named ones.
