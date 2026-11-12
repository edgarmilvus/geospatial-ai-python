# Exercise 3 — downsampling without moving the map

## What it does

Writes a 960 x 720 three-band scene at 10 m, reads it back through
`out_shape=(180, 240)` with nearest-neighbour resampling, and computes the transform
that belongs to the coarse grid: the original scaled by four. The origin and the
bounds do not move; only the pixel size grows.

## The listings

| file | what it is |
| --- | --- |
| `downsample_retransform.py` | the solution: scene writer, `downsample_and_retransform` |
| `run_downsample.py` | the harness: shape, ratio, origin, bounds, factor 2 |
| `prompt_sketch_a_context.py` | the exercise's quoted "previous example", as the book prints it |
| `prompt_sketch_b_requirements.py` | the exercise's stub fence, as the book prints it |

## Run it

```bash
cd chapter11/exercise_3_advanced_modification_challenge_si/exercise/files
python3 downsample_retransform.py
```

It writes `output/downsample_scene.tif`, downsamples it by four and prints the old
and new pixel sizes. `run_downsample.py` checks that the coarse transform covers the
same bounds as the source, that `a` and `e` are exactly four times larger, and that a
factor of two halves both sides, and exits non-zero when the transform stops
following the shape.

```text
--- Downsampling Verification ---
Original dimensions: 960x720
Resampled data shape (Bands, H, W): (3, 180, 240)

Original Transform (a, e): 10.0000, -10.0000
New Downsampled Transform (a, e): 40.0000, -40.0000
Verification successful: Pixel size increased by factor of 4.
```

## What it produces

| path | what it is |
| --- | --- |
| `output/downsample_scene.tif` | the 960 x 720 x 3 fine-grid scene |
| `output/downsample.json` | both transforms, the ratio, both bounds, both means |

## Notes

- The new transform is `original_transform * Affine.scale(factor, factor)`. That is
  exact because the bounds are unchanged: the same ground, one fourth of the columns.
  The printed draft's `calculate_default_transform(original_crs, original_crs,
  width, height, src.bounds, new_width, new_height)` passes a `BoundingBox` as
  `left` and leaves `top` unset; rasterio 1.4 raises `ValueError: Some, but not all,
  bounding box parameters were provided` before any transform is returned.
- Nearest-neighbour is the right default here because the values are class-like
  integers; averaging would invent values between classes.
- The mean is not preserved exactly: the coarse grid is a subset, not an average. The
  harness allows 2 % and asserts the range never leaves the source's.
