# Exercise 1 — one NDVI cube from a bands-last stack

## What it does

Simulates a five-date data cube over 100 × 100 pixels with a labelled `band` axis,
transposes it to `(time, y, x, band)`, and reduces it to a single NDVI
`DataArray` with three dimensions. `calculate_ndvi_stack` selects the two bands by
name rather than by position, casts to float before dividing, guards the zero
denominator with `xr.where`, and drops the band coordinate so the result is
`(time, y, x)`. `verify_and_summarize` then prints the global minimum, maximum and
mean.

## The listings

| file | what it is |
| --- | --- |
| `01_ndvi_cube.py` | the listing: the 4D cube, the reduction, the three global statistics |
| `run_ndvi_cube.py` | the harness: 20 assertions on axis order, the formula, the range and the NaN count |

## Run it

```bash
cd chapter15/exercise_1/exercise/files
python3 01_ndvi_cube.py
```

It prints the minimum, maximum and mean NDVI and the dimensions of the result;
`run_ndvi_cube.py` asserts the cube is `(5, 100, 100, 2)` with `('time', 'y', 'x')`
after the reduction, that one sampled pixel equals `(NIR − Red) / (NIR + Red)`, and
that no pixel divided by zero.

```text
--- NDVI Time Series Summary ---
Minimum NDVI: 0.1120
Maximum NDVI: 0.7997
Mean NDVI: 0.4769

Final NDVI Stack Dimensions: ('time', 'y', 'x')
```

## What it produces

| path | what it is |
| --- | --- |
| `output/ndvi_cube.json` | both shapes and dimension lists, the five dates, the three statistics |

## Notes

- The bands are selected with `.sel(band='nir')`, not with `.isel(band=1)`. A
  positional read works until the band order changes, and then produces a plausible
  number with the wrong sign.
- The bands are simulated between 500 and 4 500 of a 0–10 000 scale, so the index can
  reach 0.7997 but never 1.0: a 500 m² reflectance floor and a 4 500 ceiling bound
  the ratio well short of unity.
- `xr.where` keeps the name of its first argument, so the published version returned
  a cube called `Sentinel_Bands`. The listing renames the result to `NDVI`; the
  harness checks the name because downstream code selects on it.
- Five dates six months apart, from January 2020: the cube's `time` coordinate is
  what makes `.sel(time=...)` possible, which the later exercises rely on.
