# Exercise 4 — the choropleth as an interactive document

## What it does

Moves the same idea into Folium: thirty census tracts with a 2020 population and a
2010–2020 change, classified into six Jenks classes, drawn as a `folium.GeoJson` layer where
hovering a tract opens a tooltip with its identifier, its population and its change. Two
basemaps and a layer control let the reader switch the background and toggle the choropleth.

## The listings

| file | what it is |
| --- | --- |
| `interactive_tract_choropleth.py` | the solution: thirty tracts, six classes, one GeoJSON layer |
| `run_interactive_choropleth.py` | the harness: the payload, the fills, the tooltip, the tile layers |
| `prompt_sketch_exercise_4.py` | the exercise's own prompt fence, as the book prints it |

## Run it

```bash
cd chapter8/exercise_4_the_interactive_challenge_dynamic/exercise/files
python3 interactive_tract_choropleth.py
```

It classifies the tracts, prints the Jenks breaks, the count per class and the fill colour
of each class, and writes `output/interactive_tract_choropleth.html`.
`run_interactive_choropleth.py` parses the GeoJSON the page loads, calls the listing's own
`style_function` on each feature, and reads the layer control's two basemaps out of the
rendered JavaScript (73 assertions); it exits non-zero if the tooltip loses a field or a
class loses its colour.

```text
Jenks breaks (%): -10.02, -1.68, 6.24, 14.21, 20.42, 28.28
Tracts per class: 9, 6, 6, 4, 2, 3

Colour per class (RdYlGn, red = decline, green = growth):
  class 0: #a50026  9 tract(s)
  class 1: #f46d43  6 tract(s)
  ...
  class 5: #006837  3 tract(s)
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/interactive_tract_choropleth.html` | the standalone map: basemaps, choropleth, tooltips, control |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/interactive_choropleth.json` | breaks, counts, fills, basemap names and URLs, centre |

## Notes

- `plt.cm.get_cmap` was removed in matplotlib 3.9 and `matplotlib.colors` was never
  imported, so the book's `style_function` raised on its first call. The listing uses
  `matplotlib.colormaps['RdYlGn']` and imports `rgb2hex`.
- The class of a tract is `classifier.yb` — one entry per observation. The book indexes that
  array with the class id, which returns another tract's class and raises `IndexError`
  above the top break.
- `tiles=None`: the requirement is two basemaps, and the book's map already had
  OpenStreetMap as its default before adding OpenStreetMap again.
- The HTML needs a browser **and an internet connection to show the tiles**; the file itself
  is generated offline, and the harness never opens it, it reads it.
- The tooltip fields keep the book's own column names, including the space in `Tract ID`,
  because the GeoJSON property key is what `GeoJsonTooltip` reads.
