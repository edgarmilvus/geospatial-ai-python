# Exercise 1 — the same four densities under two classification schemes

## What it does

Takes one skewed table of four counties — one urban at 1 000 000 people per square mile,
three rural at 11.43, 20 and 25 — and maps it twice with `k=7`, once by equal interval and
once by quantiles. The map is the answer: equal interval puts the three rural counties in
the bottom class and leaves five classes empty; quantiles gives each of the four counties
its own class and leaves three empty.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise statement, exactly as the book prints it |
| `density_classification_bias.py` | the solution: four counties, two schemes, seven classes |
| `run_classification_bias.py` | the harness: the densities, both break sets, the class of each county |

## Run it

```bash
cd chapter8/exercise_1_the_impact_of_classification_schem/exercise/files
python3 density_classification_bias.py
```

It prints the density of each county, then both break sets, both count lists and the class
each county landed in, and writes `output/density_classification_bias.png`.
`run_classification_bias.py` recomputes the densities from population and land area,
rebuilds the breaks, and counts how many classes each scheme actually fills (34
assertions); it exits non-zero if the two maps ever draw the same number of colours.

```text
--- Equal Interval (width = range / k) ---
Breaks: 142,866.94, 285,722.45, 428,577.96, 571,433.47, 714,288.98, 857,144.49, 1,000,000.00
Counties per class: 3, 0, 0, 0, 0, 0, 1
Class of each county: [6, 0, 0, 0]

--- Quantiles (equal count per class) ---
Breaks: 15.10, 18.78, 21.43, 23.57, 142,878.57, 571,439.29, 1,000,000.00
Counties per class: 1, 0, 1, 0, 1, 0, 1
Class of each county: [6, 2, 4, 0]
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/density_classification_bias.png` | the two panels side by side, each with seven legend entries |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/classification_bias.json` | both break lists, both count lists, the class of each county |

## Notes

- `k=7` over four observations is legal and the exercise asks for it, so it is what the
  listing does: five empty classes on the left panel, three on the right. The counts are
  printed rather than hidden, because "seven classes" over four counties *means* empty
  classes.
- The quantile breaks include a jump from 23.57 to 142 878.57: the fourth quantile falls
  between two adjacent county values, and the break has to sit somewhere in that gap. That
  gap is 99.998% of the data range, which is the quantile method's known weakness.
- The book's comment claims equal interval "renders the vast majority of the map in the
  lightest colour bin"; the count list makes that claim checkable — three of the four
  counties are in one class.
