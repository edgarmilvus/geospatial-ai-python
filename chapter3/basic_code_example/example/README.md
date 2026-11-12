# Example 1 — intersection, union, buffer and spatial join

## What it does

Runs the four operations the chapter introduces on two rectangles whose overlap can
be checked by hand: a Development Zone spanning (0,0)–(10,8) and a Natural Reserve
spanning (5,4)–(15,12). The intersection is the 5 × 4 conflict patch (20 square
units), the union is the three pieces that add up to 140, the buffer is a one-unit
strip and four quarter-circles around the reserve (119.14), and the spatial join
finds the development zone touching that buffer.

## The listings

| file | what it is |
| --- | --- |
| `01_zoning_overlay_basics.py` | the listing: overlay, union, buffer, sjoin, with printed areas |
| `run_zoning_overlay.py` | the harness: 20, 140, the buffer's closed form, one joined row |

## Run it

```bash
cd chapter3/basic_code_example/example/files
python3 01_zoning_overlay_basics.py
```

It prints the two input layers, then the area of each operation and the joined
attribute row; `run_zoning_overlay.py` asserts 20, 140, a buffer within 0.01 of
80 + 36 + π and a single joined feature, and exits non-zero if any operation changes
its answer.

## What it produces

| path | what it is |
| --- | --- |
| `output/zoning_overlay.json` | both input areas, the intersection, the union, the buffer and its closed form |

```text
--- 1. Spatial Intersection (Conflict Area) ---
Area of Intersection (sq units): 20.00
...
Total Features after Union: 3
Total Union Area: 140.00
...
Buffered Area: 119.14
```

## Notes

- The plane is deliberately unitless: EPSG:4326 is used to satisfy the API, but the
  numbers are topology, not metres. The advanced script does the metric version.
- `overlay` takes two frames positionally and adds `_1` / `_2` to the columns that
  collide, which is why the conflict row carries `Name_1` and `Name_2`.
- A buffered rectangle is a polygon, not a curve: the area lands a few thousandths
  under the closed form (119.1365 against 119.1416).
