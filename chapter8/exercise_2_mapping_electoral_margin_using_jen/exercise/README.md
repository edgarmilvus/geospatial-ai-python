# Exercise 2 — a diverging margin map that pivots on zero

## What it does

Turns twenty simulated districts into a signed electoral margin — `(A - B) / (A + B)`,
running from −1 to +1 — and maps it with a red-to-blue ramp whose neutral colour sits
exactly on zero. The classification is Jenks, run on the *distance* from zero and then
mirrored, so a district 0.05 to the left and one 0.05 to the right are cut the same way.
One district casts no votes at all: its margin is missing, and it is drawn grey rather
than being counted as a tie.

## The listings

| file | what it is |
| --- | --- |
| `electoral_margin_jenks.py` | the solution: twenty districts, mirrored Jenks breaks, one map |
| `run_electoral_margin.py` | the harness: the margin, the classes, the fills, the grey district |
| `prompt_sketch_exercise_2.py` | the exercise's own prompt fence, as the book prints it |

## Run it

```bash
cd chapter8/exercise_2_mapping_electoral_margin_using_jen/exercise/files
python3 electoral_margin_jenks.py
```

It computes the margin, classifies it into nine classes centred on zero, prints the edges,
the count per class and how many districts fall each side, and writes
`output/electoral_margin_jenks.png`. `run_electoral_margin.py` recomputes every margin from
the votes, rebuilds every class with `bisect`, and reads the two collections geopandas drew
to confirm the neutral colour lands on the zero edge (47 assertions).

```text
Class edges, mirrored around zero: -0.400, -0.273, -0.162, -0.073, +0.000, +0.073, +0.162, +0.273, +0.400
Zero is edge 4: True; edges are symmetric: True

Counts per class: 1, 2, 1, 4, 1, 3, 3, 3, 1
Districts left of zero: 9; right of zero: 10
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/electoral_margin_jenks.png` | the map, with the class edges and the missing-data entry in its legend |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/electoral_margin.json` | the edges, the counts, the colour and luminance of every class |

## Notes

- The book's solution does not parse: `np.where(...)` is cut off mid-expression, with no
  `else` branch and no closing parenthesis. The listing completes it, and returns NaN where
  no votes were cast so the guard is visible on the map instead of being a silent zero.
- `vmin=-abs_max, vmax=abs_max` cannot centre anything when a `scheme` is in use: class
  colouring ignores vmin/vmax. The centring has to be in the breaks, which is why the
  Jenks run is on `|margin|` and then mirrored.
- `RdBu` already runs red → white → blue; the book's `RdBu_r` would paint a Republican
  landslide blue. The listing uses `RdBu` and says so.
- The ramp is sampled at `i/k`, not `i/(k-1)`, so the neutral midpoint falls on the edge
  between class 4 and class 5 — which is zero. With the default normalisation the white
  lands on the centre of a class, and no class is centred on zero.
