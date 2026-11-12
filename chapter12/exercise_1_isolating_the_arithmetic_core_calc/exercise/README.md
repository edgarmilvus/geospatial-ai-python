# Exercise 1 — the prompt, and where its solution lives

## What it does

Holds the code block the book prints as the exercise's starting point: two 5×5
reflectance arrays in digital numbers. The task is to compute the index from them
with vectorised arithmetic, keep it `float32`, print the denominator before dividing,
and report the minimum and maximum.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the prompt sketch, exactly as the exercise prints it — not a program |
| `../exercise_1/exercise/files/ndvi_arithmetic_core.py` | the worked solution, one folder over |

## Run it

```bash
cd chapter12/exercise_1/exercise/files
python3 ndvi_arithmetic_core.py
```

The sketch beside this README defines data and nothing else, so there is nothing to
run: the runnable version, its harness and the measured numbers live in the sibling
`exercise_1/` project. That harness asserts 21 facts on the same two arrays and exits
non-zero if any of them changes.

```text
--- Denominator Check ---
Sum Bands (NIR + Red):
 [[600. 750. 900. 670. 830.]
 [620. 770. 920. 690. 850.]
 [640. 790. 940. 710. 870.]
 [660. 810. 960. 730. 890.]
 [680. 830. 980. 750. 910.]]
```

## What it produces

Nothing. It is a prompt: the output belongs to the solution folder.

## Notes

- The sketch is kept verbatim so the book and the tree agree on what the student was
  given.
- `run_ndvi_arithmetic.py` in the sibling folder is the grader; this folder has no
  harness and no `output/`.
