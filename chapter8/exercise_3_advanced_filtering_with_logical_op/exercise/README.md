# Exercise 3 — (A OR B) AND C, and bins built after the filter

## What it does

Simulates fifteen Florida counties with a population, a median income and a coastal flag,
then keeps only those that are coastal **and** either populous (over 500 000) or poor
(under 45 000). The full state is drawn behind in grey for context and the six survivors are
coloured by income, classified on the survivors — not on the state.

## The listings

| file | what it is |
| --- | --- |
| `coastal_vulnerability_filter.py` | the solution: three named conditions, one mask, one overlay |
| `run_coastal_filter.py` | the harness: the mask, the two exclusions, the subset's breaks |
| `prompt_sketch_exercise_3.py` | the exercise's own prompt fence, as the book prints it |

## Run it

```bash
cd chapter8/exercise_3_advanced_filtering_with_logical_op/exercise/files
python3 coastal_vulnerability_filter.py
```

It prints the size of each condition and of the combined mask, lists every county with its
values and whether it passed, prints the quantile breaks over the subset next to the breaks
the whole state would have produced, and writes `output/vulnerable_coastal_counties.png`.
`run_coastal_filter.py` rebuilds the mask from the thresholds, checks that the subset is
exactly what the mask selects, and reads the two collections to confirm the background
still holds all fifteen counties (36 assertions).

```text
High population (> 500,000): 7 counties
Low income (< 45,000): 6 counties
Coastal: 8 counties
(high population OR low income) AND coastal: 6 counties

Selected: FL_C0, FL_C2, FL_C6, FL_C8, FL_C10, FL_C14
...
Quantile breaks over the subset: 35,769, 40,000, 41,396, 54,769, 60,658
The same quantiles over the whole state would have been: 37,684, 48,099, 54,273, 62,723, 74,188
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/vulnerable_coastal_counties.png` | the grey state with the six selected counties coloured |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/coastal_filter.json` | condition counts, the selected counties, both break sets |

## Notes

- The data is seeded. Without `np.random.seed(42)` the number of counties that pass the
  filter changes on every run, and with it the map.
- The mask is the exercise's real content: `condition_1 = high | low` and
  `final_mask = condition_1 & coastal`. FL_C5 is populous but inland; FL_C4 is coastal but
  neither poor nor populous. One exclusion per way of failing.
- Classifying after filtering is not a detail. The subset's quintiles start at 35 769 and
  end at 60 658; the state's start at 37 684 and end at 74 188. Using the state's breaks
  would leave the poorest selected county below the first class.
- `Quantiles` on six counties with five classes gives one empty class; the legend still
  prints five entries, which is the honest number of classes it asked for.
