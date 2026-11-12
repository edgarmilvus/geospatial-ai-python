# Exercise 4 — refactoring a map into the Matplotlib object model

## What it does

Takes a map built from `plt.*` calls and rebuilds it from artists on a UTM 48N `GeoAxes`:
`ax.set_title` plus a figure `suptitle`, a legend assembled from `Patch` handles, round metric
ticks, a scatter marker at a projected coordinate, a 5 km × 5 km box around a port and an
`annotate` callout. The refactor changes nothing on the page; it changes what the code can *say*
about the page — and on a `GeoAxes` it also makes "5 000 units" mean 5 km.

## The listings

| file | what it is |
| --- | --- |
| `01_refactored_annotation_layers.py` | the listing: layers, handles, marker, box, callout |
| `run_refactored_annotation.py` | the harness: zone, transform vs pyproj, artists, box geometry |

## Run it

```bash
cd chapter5/exercise_4_refactoring_and_enhancing_a_multi/exercise/files
python3 01_refactored_annotation_layers.py
```

It draws seven land polygons and one strait on a UTM 48N `GeoAxes`, projects the port with
`transform_point`, adds the annotation layer and saves a PNG, printing the layer counts, the port in
both CRSs, the extent and the box size. `run_refactored_annotation.py` asserts zone 48N, that
Cartopy's projection of the port matches pyproj's to a micrometre (372 060, 149 246 m), a 5 000 m
patch centred on it, round easting ticks, two legend handles, one scatter collection and one
callout anchored to the port; it exits non-zero when any of them changes.

```text
CRS: EPSG:4326 -> axes UTM (UTM zone 48N)
POI in WGS 84: (103.85, 1.35)
POI in the map CRS: (372,060, 149,246) m
Extent (metres): (72060.0, 672060.0, -150754.0, 449246.0)
Bounding box: 5,000 m square, 25 sq km
```

## What it produces

| path | what it is |
| --- | --- |
| `output/refactored_annotation_layers.png` | the annotated map |
| `output/refactored_annotation.json` | zone, layers, projected port, box, ticks, legend count |

## Notes

- The port is a WGS 84 coordinate and the axes speaks metres, so it is projected with
  `CRS_MAP.transform_point(...)` before anything is drawn at it. That one call is the exercise's
  new lesson: on a `GeoAxes`, data coordinates are projection coordinates.
- The `5000` in the box is metres only because the projection is metric. The same number in degrees
  would be a box 5 000 degrees wide.
- A `GeoAxes` shows ticks only where they are placed, so the refactor sets them at round eastings
  and northings and prints them plainly; `ax.set_xlabel` is what names the unit.
- The bundled dataset was removed in GeoPandas 1.0; seven land polygons and a strait stand in for
  it, and the strait replaces the book's degree-based `buffer(100000)` placeholder.
