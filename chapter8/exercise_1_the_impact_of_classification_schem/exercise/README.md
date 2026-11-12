# Exercise 1 — the prompt, and where its solution runs

## What it does

Holds the exercise's prompt fence exactly as the book prints it: the four requirements
(equal-interval map, quantile map, the same ramp, two critical comments) written as
comments, with the choropleth calls left for the student to write. The extractor classifies
that fence as an `exercise` block, so it keeps its own folder; it is not a program and is
not harnessed.

The worked solution lives in the sibling folder `chapter8/exercise_1/`, because the book's
*Solutions and Explanations* heading is a bare `### Exercise 1` and the extractor gives that
heading its own slug.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise's prompt fence, byte-identical to the book |
| `../exercise_1/exercise/files/density_classification_bias.py` | the solution: four counties, seven classes, two schemes |
| `../exercise_1/exercise/files/run_classification_bias.py` | the harness: the densities, both count lists, the class of each county |

## Run it

```bash
cd chapter8/exercise_1/exercise/files
python3 density_classification_bias.py
```

The fence beside this README is a task description, not a program; the command runs the
worked solution in `chapter8/exercise_1/`, which prints the two break sets and writes
`output/density_classification_bias.png`. The harness there exits non-zero if the two
schemes ever fill the same number of classes.

```text
Counties per class: 3, 0, 0, 0, 0, 0, 1
Class of each county: [6, 0, 0, 0]
```

## What it produces

Nothing: this folder publishes a prompt, and the prompt has no output. Everything the
exercise produces is under `../exercise_1/exercise/output/`.

## Notes

- Two folders for one exercise is the extractor's doing, not a choice: the prompt heading
  is `### Exercise 1: The Impact of Classification Schemes…` and the solution heading is
  `### Exercise 1`. Different text, different slug.
- The prompt asks for `k=7` over four counties. That is legal — mapclassify leaves classes
  empty — and the solution keeps it, because the empty classes are half the lesson.
