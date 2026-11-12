# Example 1 — a 4 × 4 window cut from a 10 × 10 raster

## What it does

Builds a 10 × 10 integer raster whose values run 0 to 99, georeferences it with
`Affine(1.0, 0.0, 0.0, 0.0, -1.0, 10.0)` so one pixel spans one degree, and hands it
to `rasterio.mask.mask` with a square polygon covering 3..7 on both axes. The clip
runs inside a `rasterio.io.MemoryFile`, so nothing is written and the whole
operation is visible in the printed array: the sixteen pixels whose centres fall in
the square, re-anchored at (3.0, 7.0).

## The listings

| file | what it is |
| --- | --- |
| `01_in_memory_raster_clipping.py` | the listing: synthetic raster, GeoJSON square, in-memory mask |
| `run_in_memory_clip.py` | the harness: 26 assertions on the retained pixels, the transform and NoData |

## Run it

```bash
cd chapter14/2_basic_code_example_in_memory_raster_clippin/example/files
python3 01_in_memory_raster_clipping.py
```

It prints the source shape, the clipped shape, the sixteen values and the new
affine transform; `run_in_memory_clip.py` re-runs the same mask call and asserts
that rows 3-6 and columns 3-6 survived, that the transform moved to (3.0, 7.0), and
that the `crop=False` variant fills 84 of 100 pixels with −9999.

```text
Starting clipping process...

--- Masking Results ---
Original Data Shape (H, W): (10, 10)
Clipped Data Shape (Bands, H, W): (1, 4, 4)

Content of Clipped Data (Band 1):
[[33 34 35 36]
 [43 44 45 46]
 [53 54 55 56]
 [63 64 65 66]]

New Affine Transform (Top-Left Coordinates):
| 1.00, 0.00, 3.00|
| 0.00,-1.00, 7.00|
| 0.00, 0.00, 1.00|
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/in_memory_clip.json` | both shapes, the sixteen values, the transform, the 84-pixel NoData count |

## Notes

- The listing writes nothing: `MemoryFile` is the file. The harness is what leaves
  an artefact behind.
- `all_touched=False` is what makes the count 16 rather than 36: a pixel joins the
  clip only when its centre is inside the polygon, and this square sits exactly on
  pixel edges, so the touching ring contributes nothing.
- `mask()` always returns three dimensions, `(bands, rows, columns)`; the listing
  indexes band `0` before printing, which is the correction the chapter's pitfall
  section makes.
