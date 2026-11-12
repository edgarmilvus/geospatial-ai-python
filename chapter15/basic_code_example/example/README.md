# Example 1 — a 4D cube reduced to a 3D NDVI stack

## What it does

Simulates three observations of a 10 × 10 pixel patch as `(Time, Height, Width,
Bands)`, with Red at band 0 and NIR at band 1, and walks the time axis once. Each
slice is split into its two bands, `calculate_ndvi` applies `(NIR − Red) / (NIR +
Red)` with an `np.where` guard against a zero denominator, and the five resulting
maps are stacked back into `(Time, Height, Width)`. The simulated land cover moves
from healthy vegetation to bare earth, so the printed means fall from 0.7289 to
−0.3216 across the three steps.

## The listings

| file | what it is |
| --- | --- |
| `01_ndvi_time_series_stack.py` | the listing: the 4D cube, the NDVI function, the temporal loop |
| `run_ndvi_stack.py` | the harness: 17 assertions on shapes, band order, the means and the zero guard |

## Run it

```bash
cd chapter15/basic_code_example/example/files
python3 01_ndvi_time_series_stack.py
```

It prints the mean NDVI of each time step, the shape of the stacked result and the
drop from the first step to the last; `run_ndvi_stack.py` asserts the cube's
`(3, 10, 10, 2)` shape, that band 1 is NIR (a swapped read would print −0.7 instead
of +0.7), that the drop exceeds 0.9, and that a zero denominator yields 0.0.

```text
Starting time series analysis for 3 steps...
Time Step T1:
  Mean NDVI: 0.7289
Time Step T2:
  Mean NDVI: 0.3965
Time Step T3:
  Mean NDVI: -0.3216

Processing complete.
Final NDVI stack shape: (3, 10, 10)
Change detected: T1 Mean NDVI (0.7289) -> T3 Mean NDVI (-0.3216)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/ndvi_stack.json` | both shapes, the three means, the drop, the minimum and maximum |

## Notes

- The cube is drawn from `np.random.default_rng(15)`; without a seed the three means
  move by a few hundredths on every run and the printed block in the book would stop
  matching the code.
- `np.where` evaluates both branches before choosing, so a fully black pixel still
  raises a `RuntimeWarning` from the division even though the stored value is 0.0.
  The harness silences the warning with `np.errstate` and asserts the value.
- `rasterio` is imported for context only. Nothing here touches a file: the point of
  the example is the axis order, and the file I/O arrives in the next section.
