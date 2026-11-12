# Exercise 1 — 1 m DEM to 10 m, with the footprint unchanged

## What it does

Writes a 1000×1000 DEM at 1 m, inspects its metadata, computes the new grid and the
new transform, resamples with bilinear interpolation, verifies that the mean and the
standard deviation survived, and writes the 100×100 result at 10 m.

## The listings

| file | what it is |
| --- | --- |
| `resample_dem.py` | the solution: the dimension helper, `reproject`, the new profile |
| `run_resample_dem.py` | the harness: the cell size, the preserved bounds, the mean |

## Run it

```bash
cd chapter13/exercise_1/exercise/files
python3 resample_dem.py
```

It prints the input metadata, the statistics before and after the resample, the new
grid and transform and whether the extent survived, then writes both GeoTIFFs.
`run_resample_dem.py` asserts 31 facts — 100 cells at 10 m, the same four edges to the
micrometre, a mean of 202.3 m on both sides — and exits non-zero if any of them
changes.

```text
--- Original DEM Metadata ---
Dimensions (W x H): 1000 x 1000
Resolution (X, Y): (1.0, 1.0)
CRS: EPSG:32617
Data Type: float32

--- Statistical Verification ---
Original Mean/Std: 202.30 / 115.48
Resampled Mean/Std: 202.30 / 115.45
Mean difference: 0.00 m

New grid: 100 x 100 at 10.0 m
Extent preserved: True
Successfully wrote resampled DEM to output/resampled_output_dem.tif
```

## What it produces

| path | what it is |
| --- | --- |
| `output/simulated_input_dem.tif` | the 1 m DEM, 1000×1000 cells, EPSG:32617 |
| `output/resampled_output_dem.tif` | the 10 m DEM, 100×100 cells, same extent |
| `output/dem_resampling.json` | written by the harness: both profiles, the mean, the bounds |

## Notes

- The transform is `src.transform * Affine.scale(10, 10)`, not `src.transform *
  src.transform.scale(...)` on a copy: the pixel size grows by the ratio of the grids
  and the origin stays where it was.
- Bilinear is the right kernel for elevation. Nearest would keep a 1 m value and call
  it a 10 m cell; cubic would overshoot on ridges.
- The mean is the check, not the proof: a resample can preserve the mean and still
  lose the ridge lines. The standard deviation is the second half of that check.
