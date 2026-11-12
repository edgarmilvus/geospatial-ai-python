# Exercise 2 — two density surfaces, one map, a shift you can measure

## What it does

Builds a day of 20 000 pings whose location depends on the hour: rush-hour pings cluster
over the residential district, mid-day pings over the central business district, and the
rest of the day is background. It then splits the frame into the two windows, renders each
as its own heat layer with its own gradient, and puts a `LayerControl` between them. The
shift between the windows is about 0.035 degrees in both axes — a number, not a picture.

## The listings

| file | what it is |
| --- | --- |
| `dual_period_heatmap.py` | the solution: hour-aware pings, two windows, two layers |
| `run_dual_period.py` | the harness: the segmentation, the centroids, the two layers |

## Run it

```bash
cd chapter9/exercise_2_dynamic_density_mapping_with_tempo/exercise/files
python3 dual_period_heatmap.py
```

It segments the pings, prints the count and the centroid of each window and the shift
between them, then writes `output/dynamic_density_map.html`.
`run_dual_period.py` recomputes the windows from the frame's own hours, measures the two
centroids and reads both heat layers out of the document (42 assertions); it exits non-zero
if the windows stop being a subset of the day or the shift falls below 0.02 degrees.

```text
--- 20000 pings over 28 days ---
Morning peak (07:00-08:59): 1630 pings, centre 40.7200 N, -74.0200 E
Mid-day (11:00-12:59):      1721 pings, centre 40.7548 N, -73.9850 E
Shift between the windows:  +0.0349 latitude, +0.0350 longitude
Radius for both layers: 15 pixels
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/dynamic_density_map.html` | the map: two toggleable heat layers over CartoDB Dark Matter |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/dual_period.json` | both windows' counts and centres, the shift, the gradients |

## Notes

- The book's segmentation reads exercise 1's CSV, whose timestamps are a uniform
  minute-by-minute range: the two windows then contain the same spatial distribution and the
  comparison has nothing to show. The generator here draws each ping's hour first, so the
  two windows really are in different places.
- `max_opacity=0.7` does nothing: leaflet-heat's options are `minOpacity`, `maxZoom`,
  `radius`, `blur` and `gradient`, and folium passes unknown keywords straight through to a
  browser that ignores them. The 0.7 is carried by `rgba(...)` stops in the gradient, which
  is the only place an alpha is honoured.
- Both layers use `radius=15`, which is what makes the comparison fair: the same smoothing
  over two different point sets.
- The book never saves the map (`m.save` is commented out) and only prints that the object
  exists. It is written into `output/` here.
