# Exercise 3 — D8 flow accumulation and the topographic wetness index

## What it does

Routes flow with D8 on a hillslope that falls to the east, accumulates the cells
draining through each one, converts the accumulation into a specific catchment area,
and combines it with the local slope into TWI = ln(As / tan β).

## The listings

| file | what it is |
| --- | --- |
| `twi_d8.py` | the solution: the receivers, the accumulation, the index, the raster |
| `run_twi_d8.py` | the harness: the accumulation identity, the flat floor, a pit |
| `prompt_sketch_exercise_3.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter13/exercise_3_hydrological_feature_engineering_t/exercise/files
python3 twi_d8.py
```

It prints the sink count, the largest accumulation, the accumulation at both edges,
the index statistics and the hillslope's angle, then writes the index as a GeoTIFF.
`run_twi_d8.py` asserts 35 facts — column j accumulates j+1 cells, the index of a cell
is ln((j+1)·5/0.15), flat ground is floored at 0.001 — and exits non-zero if any of
them changes.

```text
--- D8 Flow Routing ---
Grid: (128, 128) at 5.0 m
Sinks (no lower neighbour): 128
Largest accumulation: 128 cells
Accumulation at the west edge (column 0): 1 cells
Accumulation at the east edge (column 127): 128 cells

--- TWI Calculation Results ---
TWI Min: 3.51
TWI Max: 8.36
TWI Mean: 7.38
Slope of the hillslope: 8.53° (tan beta = 0.15)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/twi.tif` | the index: one float32 band, 128×128 cells of 5 m, EPSG:32610 |
| `output/twi_d8.json` | written by the harness: accumulations, index values, the floor |

## Notes

- **richDEM is replaced by explicit D8.** Every cell drains to the single lowest of
  its eight neighbours, a diagonal step divided by √2 so it is not preferred for being
  longer, and the accumulation is one pass from the highest cell down. That is the
  algorithm `method='D8'` runs.
- The scene is a plane on purpose: every cell drains east, so column j carries j+1
  cells and the index of that column is checkable by hand. A real DEM is not a plane,
  and the numbers would no longer be auditable.
- The last column is a sink — 128 of them, one per row. A real DEM also has interior
  pits, which D8 leaves as sinks unless they are filled first; the harness adds one
  and checks it is detected and accounted for.
- `tan β` is floored at 0.001 before the logarithm. Flat ground has no aspect and no
  slope, and `ln(x/0)` is not a number.
