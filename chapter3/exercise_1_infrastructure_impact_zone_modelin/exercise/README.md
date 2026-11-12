# Exercise 1 — the prompt, and where its solution runs

## What it does

This folder holds the exercise's prompt fence exactly as the book prints it: the five
steps the student has to code, written as comments over an import. It is published as
an `exercise` block by the extractor, so it keeps its own folder, but it is not a
program and is not harnessed.

The worked solution sits in the sibling folder `chapter3/exercise_1/`, because the
book's *Solutions and Explanations* heading is a bare `### Exercise 1` and the
extractor gives that heading its own slug.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise's prompt fence, byte-identical to the book |
| `../exercise_1/exercise/files/01_pipeline_corridor_impact.py` | the solution: buffer, overlay, area, merge, percentage |
| `../exercise_1/exercise/files/run_pipeline_corridor.py` | the harness: 100 % for parcel 101, 25 % for parcel 102, 103 absent |

## Run it

```bash
cd chapter3/exercise_1/exercise/files
python3 01_pipeline_corridor_impact.py
```

It prints the corridor, the clipped parcel ids and the impact table; the harness
`run_pipeline_corridor.py` asserts both percentages and the excluded parcel, and exits
non-zero if the original areas are taken from the clipped geometry.

## What it produces

| path | what it is |
| --- | --- |
| `../exercise_1/exercise/output/pipeline_impact.json` | the affected parcels, both areas, both percentages |

```text
 parcel_id crop_type  impacted_area_sqm  total_area_sqm_original  impact_percent
       101     Wheat          3000000.0                3000000.0           100.0
       102      Corn          1000000.0                4000000.0            25.0
```

## Notes

- The sketch is kept byte-identical so the book and the tree stay in step; editing it
  here would detach the block from its heading.
- A real solution to the five steps is 40 lines of geopandas — see the sibling folder.
