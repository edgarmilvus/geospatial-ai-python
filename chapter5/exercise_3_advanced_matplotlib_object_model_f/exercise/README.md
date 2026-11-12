# Exercise 3 — the advanced object model: two GeoAxes, one locator box

## What it does

Draws North America on an Albers Equal Area `GeoAxes` with an inset of the Aleutians on a second
`GeoAxes` in an azimuthal equidistant projection, and links them: the inset's extent is converted
into the main map's projection with `transform_points` and drawn there as a dashed rectangle
1 149 750 × 1 182 249 m across (1.36 million km²). It is the exercise where the Matplotlib object
model and the projection have to agree, and where Cartopy replaces `to_crs`.

## The listings

| file | what it is |
| --- | --- |
| `01_main_map_with_inset.py` | the listing: two `GeoAxes`, `transform_points`, the locator patch |
| `run_main_map_inset.py` | the harness: projections, transform vs pyproj, box geometry, inset placement |

## Run it

```bash
cd chapter5/exercise_3_advanced_matplotlib_object_model_f/exercise/files
python3 01_main_map_with_inset.py
```

It draws the continent in Albers, the three Aleutian islands in an azimuthal window, converts the
inset's extent into the main projection and adds the dashed locator box and a labelled graticule,
printing both projections, both feature counts and the box's dimensions. `run_main_map_inset.py`
asserts the Albers/azimuthal pair, that Cartopy's corner conversion matches pyproj's, a 1.36 million
km² box that overlaps the mapped land, a second axes placed in figure fractions and labelled
gridline edges; it exits non-zero when any of them changes.

```text
Main features: 14 in WGS 84, drawn on a AlbersEqualArea axes
Inset features: 3 in WGS 84, drawn on a AzimuthalEquidistant axes
Main:  AlbersEqualArea, extent (-5450138.0, 3064082.0, -1747275.0, 5019271.0) m
Inset: AzimuthalEquidistant, extent (-342257.0, 689241.0, -231371.0, 364891.0) m
Width x height in the main projection: 1,149,750 x 1,182,249 m
```

## What it produces

| path | what it is |
| --- | --- |
| `output/main_map_with_inset.png` | the two-axes figure |
| `output/main_map_with_inset.json` | both projections, feature counts, box dimensions, inset extent |

## Notes

- The book's inset is UTM zone 5N, and a UTM zone is a six-degree strip: the Aleutian chain crosses
  four of them, so `set_extent` cut the islands at the zone boundary. The inset is now an azimuthal
  equidistant projection centred on the chain, which has no such edge — and the locator box is
  still a conversion between two projections, which is the exercise.
- A bounding box is not invertible across projections — the box of a rotated box is larger than the
  box — so the harness checks the box's size and that it overlaps the land, not a round trip.
- `ax.add_geometries` clips to the projection's boundary, not to the inset's rectangle, so the
  inset's artist is clipped to the axes' own box; without that it draws over the main map.
- The bundled dataset was removed in GeoPandas 1.0: the continent is fourteen synthetic polygons,
  three of them Aleutian, and the inset keeps the three islands whose centres fall in the window.
