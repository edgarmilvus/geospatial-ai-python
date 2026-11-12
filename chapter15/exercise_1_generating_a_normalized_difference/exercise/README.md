# Exercise 1 — the prompt, and where its solution runs

## What it does

This folder holds the exercise's prompt fence exactly as the book prints it: two
function signatures, the four steps each has to perform, and the main flow in
comments. It is published as an `exercise` block by the extractor, so it keeps its
own folder, but it is not a program and is not harnessed.

The worked solution sits in the sibling folder `chapter15/exercise_1/`, because the
book's *Solutions and Explanations* heading repeats a bare `### Exercise 1` and the
extractor gives that heading its own slug.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise's prompt fence, byte-identical to the book |
| `../exercise_1/exercise/files/01_ndvi_cube.py` | the solution: the labelled cube, the reduction, the statistics |
| `../exercise_1/exercise/files/run_ndvi_cube.py` | the harness: 20 assertions on the shape, the formula and the range |

## Run it

```bash
cd chapter15/exercise_1/exercise/files
python3 01_ndvi_cube.py
```

The prompt fence in this folder is a task description; the command above runs the
worked solution in the sibling folder. `run_ndvi_cube.py` asserts the cube's axis
order and the sampled pixel's arithmetic, and exits non-zero if the reduction keeps
the band axis or the index is computed with the bands swapped.

## What it produces

| path | what it is |
| --- | --- |
| `../exercise_1/exercise/output/ndvi_cube.json` | both shapes, the five dates, the three global statistics |

```text
--- NDVI Time Series Summary ---
Minimum NDVI: 0.1120
Maximum NDVI: 0.7997
Mean NDVI: 0.4769

Final NDVI Stack Dimensions: ('time', 'y', 'x')
```

## Notes

- The sketch is kept byte-identical so the book and the tree stay in step; editing it
  here would detach the block from its heading.
- The prompt asks for `stackstac` and a STAC query. The solution substitutes a
  simulated cube with the same axis order, which is the part the exercise is graded
  on; nothing in the reduction changes when a real catalogue feeds it.
