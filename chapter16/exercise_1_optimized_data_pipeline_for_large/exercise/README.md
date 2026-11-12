# Exercise 1 — the prompt, and where its solution lives

## What it does

Holds the code block the book prints as the exercise's starting point: a `Dataset` with
`__init__`, `__len__` and `__getitem__` empty, and the mean and deviation to normalise
with. The task is on-the-fly tiling with `rasterio` windows.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the prompt sketch, exactly as the exercise prints it — not a program |
| `../exercise_1/exercise/files/tiled_dataset.py` | the worked solution, one folder over |

## Run it

```bash
cd chapter16/exercise_1/exercise/files
python3 tiled_dataset.py
```

The sketch beside this README defines an interface and nothing else, so there is nothing
to run: the runnable version, its harness and the measured numbers live in the sibling
`exercise_1/` project. That harness asserts 24 facts about the same 10 000 x 10 000 scene
and exits non-zero if the grid, the window or the augmentation changes.

```text
Scene: 10000 x 10000 pixels
Grid: 40 rows x 40 columns = 1600 tiles of 256 px
...
Tile 41 read 65,536 pixels, not the 100,000,000 of the whole scene.
```

## What it produces

Nothing. It is a prompt: the output belongs to the solution folder.

## Notes

- The sketch is kept as the book prints it, with one repair: the draft wrote
  `def def __getitem__(self, index)`, which is a syntax error and would have stopped a
  student on line one.
- `run_tiled_dataset.py` in the sibling folder is the grader; this folder has no harness
  and no `output/`.
