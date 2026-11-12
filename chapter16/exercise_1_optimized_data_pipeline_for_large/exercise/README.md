# Exercise 1 — a dataset that reads one tile, not the scene

## What it does

Indexes a 10 000 x 10 000 scene as 1 600 tiles of 256 pixels, reads only the window an
index names, pads the last row and column back to full size, normalises with the scene's
mean and deviation, and applies the same quarter turn to image and mask. The scene itself
is a stand-in reader: a value derived from each pixel's absolute coordinates, so any window
is reproducible.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise statement, exactly as the book prints it |
| `tiled_dataset.py` | the solution: the reader, the dataset, three tiles printed |
| `run_tiled_dataset.py` | the harness: grid, window, padding, normalisation, rotation |

## Run it

```bash
cd chapter16/exercise_1_optimized_data_pipeline_for_large/exercise/files
python3 tiled_dataset.py
```

It prints the grid, then the window, shape and roof count of a first, a middle and the last
tile. `run_tiled_dataset.py` asserts the 40 x 40 grid, the 65 536 pixels one tile costs, the
16 x 16 edge read, the exact inversion of the normalisation and the rotation of both arrays
together; it exits non-zero when the window, the padding or the augmentation moves.

```text
Scene: 10000 x 10000 pixels
Grid: 40 rows x 40 columns = 1600 tiles of 256 px

tile 0: window x=0 y=0 256 x 256 px, rotated 90°
  image (3, 256, 256) torch.float32, mean +1.354, std 2.636
  mask  (1, 256, 256) torch.float32, 15000 roof pixels (22.89%)
...
Tile 41 read 65,536 pixels, not the 100,000,000 of the whole scene.
Normalized mean on background pixels: [-0.003, 0.006, 0.006]
Normalized mean on roof pixels: [5.96, 5.969, 5.819]
```

## What it produces

| path | what it is |
| --- | --- |
| `output/tiled_dataset.json` | the grid, the two windows, the normalisation check |

## Notes

- The draft's `def def __getitem__` was a syntax error; that is the one line of the sketch
  that had to change before it could be a prompt at all.
- The scene, the mask and the augmentation are deterministic. The reader derives each pixel
  from its absolute coordinates, so tile 41 read twice is the same array, and the harness can
  invert the normalisation and compare against a fresh window read.
- The mask is the roof rule, and the image is bright exactly there. That is what makes the
  synchronised rotation checkable: undo the turn and recompute, and every roof pixel is still
  under a bright one.
- The 22.9 % roof coverage of a full tile is high for a city and deliberate: it makes the
  chip's normalised mean visibly non-zero, which is the point of using the *scene's*
  statistics rather than the chip's.
- Needs `torch` and `rasterio`. Without `torch` the harness prints `skip` and ends green.
  Runs in under a second.
