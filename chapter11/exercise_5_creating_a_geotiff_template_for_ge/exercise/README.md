# Exercise 5 — a profile that inherits the grid and changes the payload

## What it does

Writes a four-band uint16 input, copies its profile, and changes the four keys the
exercise names: `count` to 1, `dtype` to uint8, `nodata` to 255 and `interleave` to
`band`. Width, height, CRS and transform come along unchanged. It then writes an
eight-class map (0-7, with 20 unclassified rows at 255) using that profile and reads
the file back.

## The listings

| file | what it is |
| --- | --- |
| `classification_template.py` | the solution: input writer, profile edit, class map writer |
| `run_classification_template.py` | the harness: inherited keys, changed keys, file read-back |
| `prompt_sketch_exercise_5.py` | the exercise's prompt fence, as the book prints it |

## Run it

```bash
cd chapter11/exercise_5_creating_a_geotiff_template_for_ge/exercise/files
python3 classification_template.py
```

It writes `output/classification_input.tif` and `output/classification_map.tif`,
prints both profile snippets and re-opens the map it wrote.
`run_classification_template.py` checks the four inherited keys against the input
and the four changed keys against the specification, then compares the file's pixels
with the array, and exits non-zero when the output stops sharing the input's grid.

```text
--- GeoTIFF Template Creation ---

Original Input Profile Snippet:
  Count: 4, Dtype: uint16, Nodata: 0

Modified Output Classification Profile Snippet:
  Count: 1
  Dtype: uint8
  Nodata: 255
  Interleave: band

--- Wrote classification_map.tif with 9 values ---
Read back: count=1, dtype=uint8, nodata=255.0, shape=(180, 240)
Class values: [0, 1, 2, 3, 4, 5, 6, 7, 255]
```

## What it produces

| path | what it is |
| --- | --- |
| `output/classification_input.tif` | the four-band uint16 input |
| `output/classification_map.tif` | the single-band uint8 map with nodata 255 |
| `output/classification_template.json` | both profiles and the class histogram |

## Notes

- `copy.deepcopy(src.profile)` matters. `src.profile` returns a new dictionary, but
  the output profile is then updated in place; a shallow share would be a bug the
  day someone edits a nested value.
- `nodata=255` must be representable in the new dtype. 255 is the top of uint8, which
  is why the sentinel fits and why 256 would not.
- The written file is the evidence: the harness re-opens it and asserts count, dtype,
  nodata, CRS and pixel equality. A profile dictionary that looks right and a file
  that GDAL refuses are one line apart.
