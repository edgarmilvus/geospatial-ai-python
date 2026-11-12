# Example 1 — two CRS objects, read property by property

## What it does

Loads EPSG:4326 and EPSG:3857 as `pyproj.CRS` objects and prints the properties that
separate a geographic coordinate system from a projected one: the flag that decides
which is which, the axis order, the unit each axis is measured in, and the name of
the projection method. The chapter's pitfall — latitude first, longitude second —
is visible in the axis list rather than described in prose.

## The listings

| file | what it is |
| --- | --- |
| `01_crs_objects.py` | the listing: two CRS objects and their printed properties |
| `run_crs_objects.py` | the harness: checks the flags, the axis order and the units |

## Run it

```bash
cd chapter1/defining_and_inspecting_crs_objects/example/files
python3 01_crs_objects.py
```

It prints both objects property by property. `run_crs_objects.py` asserts the same
properties — including that WGS 84 puts latitude on the first axis — and exits
non-zero if either CRS stops reporting them.

```text
--- Initializing pyproj CRS Objects ---
Successfully loaded WGS 84 (EPSG:4326)
Successfully loaded Web Mercator (EPSG:3857)
...
4. Axis Order/Units: Geodetic latitude (degree), Geodetic longitude (degree)
...
4. Axis Order/Units: Easting (metre), Northing (metre)
5. Linear Unit of Measurement: metre
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/crs_summary.json` | both codes, both axis lists, both units, the method name |

## Notes

- No network: both definitions come from the PROJ database installed with `pyproj`.
- The linear unit is read from the axis, `axis_info[0].unit_name`; a CRS object has
  no `linear_units` attribute, which is what the first draft of this listing tried.
