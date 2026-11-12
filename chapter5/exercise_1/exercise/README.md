# Exercise 1 — visualizing geographic projection distortion

## What it does

Draws the same 58 land cells on three `GeoAxes`, one per projection: Plate Carrée where they are
34 800 square degrees of nothing in particular, Eckert IV where they measure 281 934 706 km² — the
ellipsoidal answer — and Web Mercator where the same cells measure 840 665 508 km², 2.98 times as
much. The frame never changes; the axes is what carries the projection, which is why one longitude
and latitude lands at three different places.

## The listings

| file | what it is |
| --- | --- |
| `01_projection_distortion_triptych.py` | the listing: three `GeoAxes`, three areas, three panels |
| `run_projection_distortion.py` | the harness: projections, extents, equal-area fidelity, projected point |

## Run it

```bash
cd chapter5/exercise_1/exercise/files
python3 01_projection_distortion_triptych.py
```

It builds one WGS 84 frame and draws it on a Plate Carrée, an Eckert IV and an EPSG:3857 `GeoAxes`,
prints what each projection reports as the cells' area and the extent of each panel, and saves a
three-panel PNG. `run_projection_distortion.py` asserts that Eckert IV reproduces the ellipsoidal
area within 1 %, that Mercator triples it, that the Mercator panel is cut at ±20 037 508.34 m and
that (10 °E, 60 °N) projects to 6 996 129 m in Eckert IV against 8 399 738 m in Mercator; it exits
non-zero when any of them changes.

```text
Equal area (Eckert IV): 281,934,706 sq km
Web Mercator (EPSG:3857): 840,665,508 sq km
Mercator / Eckert IV: 2.98x
EckertIV         extent (-16,921,203, 16,921,203) x (-8,460,601, 8,460,601)
_EPSGProjection  extent (-20,037,508, 20,037,508) x (-20,037,508, 20,037,508)
(10.0, 60.0) on EckertIV         -> (734,351.5, 6,996,129.3)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/projection_distortion_triptych.png` | the three panels, 150 dpi |
| `output/projection_distortion.json` | panel projections, three areas, extents, one projected point |

## Notes

- The panels are `ccrs.PlateCarree()`, `ccrs.EckertIV()` and `ccrs.epsg(3857)`, so the projection
  that draws a panel is the same object the area column is measured in.
- The strongest check in the chapter lives here: the equal-area total is compared against
  `pyproj.Geod`'s ellipsoidal area, so the map is graded against the Earth, not against itself.
- The bundled dataset was removed in GeoPandas 1.0, so the cells come from a fixed land mask; the
  three projections are the book's own choice.
