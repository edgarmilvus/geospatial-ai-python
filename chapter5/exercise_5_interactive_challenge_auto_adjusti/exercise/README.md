# Exercise 5 — auto-adjusting scale bars and grid lines

## What it does

Chooses the scale bar's number from the view instead of hard-coding it: at a 150 km wide extent the
search returns a 25 km bar, at 800 km it returns 200 km, and the grid steps from 50 km to 100 km so
its labels stay round numbers — all on a UTM 17N `GeoAxes`, whose data coordinates are metres, which
is why `ax.get_xlim()` is what the search reads. Two figures are drawn, one per zoom level.

## The listings

| file | what it is |
| --- | --- |
| `01_dynamic_scale_and_grid.py` | the listing: the nice-number search, the bar, the grid |
| `run_dynamic_scale.py` | the harness: the search across four orders of magnitude, the zone |

## Run it

```bash
cd chapter5/exercise_5_interactive_challenge_auto_adjusti/exercise/files
python3 01_dynamic_scale_and_grid.py
```

It draws both views on UTM 17N `GeoAxes` with their bars and grids and saves two PNGs, printing the
bar each extent chose, its share of the width, the extent in metres and degrees and three probes of
the search function. `run_dynamic_scale.py` asserts zone 17N, the 25/200/10 km choices, that no bar
falls outside a tenth to a third of the map across 21 widths, that the wide view's segments add to
200 km and that its ticks are round 100 km eastings; it exits non-zero when the search regresses.

```text
Regions: 6 in EPSG:4326, drawn on a UTM (UTM zone 17N)
Wide view extent (metres): (300000.0, 1100000.0, 2800000.0, 3600000.0)
Local view: 150,000 m wide -> bar of 25 km (16.7% of the width)
Wide view:  800,000 m wide -> bar of 200 km (25.0% of the width)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/dynamic_scale_local.png` | the 150 km view, 25 km bar, 50 km grid |
| `output/dynamic_scale_wide.png` | the 800 km view, 200 km bar, 100 km grid |
| `output/dynamic_scale.json` | zone, both extents and bars, the sweep's min and max ratio |

## Notes

- The book's `find_optimal_nice_number` was wrong: it searched upwards from one decade below the
  width, found nothing in the 20–30 % window, and its safety break returned 500 km for a 150 km
  map — a bar three times wider than the map. The search now covers every decade that can hold the
  window and falls back to the largest nice number that fits.
- Bars are drawn at zorder 6: on a `GeoAxes` the land is a `FeatureArtist` and a bar at the default
  zorder disappears underneath it, which is what happened to the first version of this figure.
- Nice numbers are 1, 2, 2.5 and 5 times a power of ten, which is why a 150 km map gets 25 km
  rather than 30 or 45.
