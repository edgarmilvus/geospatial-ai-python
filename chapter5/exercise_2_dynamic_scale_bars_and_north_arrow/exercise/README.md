# Exercise 2 — dynamic scale bars and north arrows

## What it does

Puts six regions of the Great Lakes and Saint Lawrence on a UTM 17N `GeoAxes` — so the axes' units
are metres — shades them with a custom density ramp, adds a labelled Cartopy graticule, and draws
the two annotations the exercise is about: a 150 km scale bar of four alternating 37.5 km segments
measured in the projection's metres, and a north arrow whose label and shaft both live in axes
coordinates. It prints the axes type, its projection, its extent in metres and in degrees, the
graticule's label count and the projected coordinate of one region.

## The listings

| file | what it is |
| --- | --- |
| `01_scale_bar_north_arrow.py` | the listing: `GeoAxes`, the two helpers, the graticule, the PNG |
| `run_scale_bar_north_arrow.py` | the harness: zone, transform vs pyproj, segments, arrow anchoring |

## Run it

```bash
cd chapter5/exercise_2_dynamic_scale_bars_and_north_arrow/exercise/files
python3 01_scale_bar_north_arrow.py
```

It draws the six regions on a UTM 17N `GeoAxes` with the bar, the arrow and a labelled graticule and
saves `output/scale_bar_north_arrow.png`, printing the CRS pair, the bounds, the density range, the
extent in both units and the bar's measured length. `run_scale_bar_north_arrow.py` asserts zone
17N, that Cartopy's transform matches pyproj's, four 37 500 m segments adding to 150 000 m, a bar
starting 10 % in from the left edge, labelled gridlines and an arrow anchored in axes fraction; it
exits non-zero when any of them changes.

```text
CRS: EPSG:4326 -> axes UTM (UTM 17N)
Algoma at (-82.5, 46.6) -> (385,114.1, 5,161,807.9) m
Extent (metres): (243267.0, 1243396.0, 4710894.0, 5288376.0)
Bar length in data units: 150,000 m
Four segments of 37,500 m each
```

## What it produces

| path | what it is |
| --- | --- |
| `output/scale_bar_north_arrow.png` | the regional map with both annotations and a graticule |
| `output/scale_bar_north_arrow.json` | zone, segments, extent, label counts, projected point |

## Notes

- The north arrow was broken in the book's version: `ax.annotate(..., transform=ax.transAxes)` moves
  only the label, so the arrow was aimed at x = 0.9 *metres* — off the map. It uses
  `xycoords="axes fraction"` now, and the harness checks where its head lands.
- The bar is drawn *after* `set_extent`: both annotations place themselves from the axes' current
  limits, and a bar drawn first lands outside the map.
- The regions sit inside the zone on purpose. `set_extent` clips to the projection's own boundary,
  so a region straddling the edge would be cut in half — which is the honest demonstration of why a
  UTM zone is a local projection, and the reason the placement is commented in the listing.
