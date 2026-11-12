# Exercise 2 — the centred 512 tile and the boundary refusal

## What it does

Writes an 800 x 600 four-band scene at 20 m, computes the window that centres a
512-pixel tile — 144 columns in, 44 rows down — and reads the first three bands
through it, cast to `float32`. A second call asks for a 700-pixel tile, which cannot
fit in 600 rows; the reader raises a readable `ValueError`, catches it and returns
`None` instead of letting GDAL return a short read.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_2.py` | the task statement: a windowed read over a raster the reader supplies |
| `windowed_tile_read.py` | the solution: scene generator, `read_centered_tile`, boundary call |
| `run_windowed_tile.py` | the harness: offsets, exact pixels, dtype, refusal |

## Run it

```bash
cd chapter11/exercise_2_efficient_windowed_reading_and_arr/exercise/files
python3 windowed_tile_read.py
```

It writes `output/windowed_scene.tif`, reads the 512 tile, then the 700-pixel tile
that must fail. `run_windowed_tile.py` re-reads the same window and compares the
arrays, checks the tile transform and the cast, and exits non-zero when the tile
leaves the centre or the boundary branch stops refusing.

```text
--- Wrote windowed_scene.tif: 800 x 600, 4 bands ---
Tile successfully read using windowing.
Window defined: Window(col_off=144, row_off=44, width=512, height=512)
Resulting NumPy array shape (Bands, H, W): (3, 512, 512)
Resulting NumPy array dtype: float32

Error during tile reading: Image dimensions (800x600) are too small for the requested tile size (700).
```

## What it produces

| path | what it is |
| --- | --- |
| `output/windowed_scene.tif` | the 800 x 600 x 4 source scene |
| `output/windowed_tile.json` | window offsets, shape, dtype, transform, refusal |

## Notes

- `(800 // 2) - (512 // 2)` is 144 and `(600 // 2) - (512 // 2)` is 44. Integer
  division, not `/`: a float offset is not a window.
- The cast to `float32` does not rescale. The tile's minimum and maximum still match
  the source's, which is what makes the copy safe for a model that expects floats.
- The source has a fourth band that is deliberately not read; the harness checks the
  tile carries bands 1-3 by comparing against `src.read(indexes=(1, 2, 3), ...)`.
- `out_dtype` is a read-time conversion, so the source file stays uint16 on disk.
