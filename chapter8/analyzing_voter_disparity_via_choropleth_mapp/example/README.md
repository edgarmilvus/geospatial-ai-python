# Example 2 — two schemes, one column, and the breaks that decide the story

## What it does

Simulates twelve counties with an election each, derives two comparable metrics (turnout
rate and one candidate's share of the vote), and draws them twice: Jenks natural breaks on
the first, quantiles on the second. The figure is the chapter's argument in one image —
the same underlying numbers, two different sets of class breaks, two different stories.

## The listings

| file | what it is |
| --- | --- |
| `voter_turnout_choropleth.py` | the listing: twelve counties, five statistics per county, two maps |
| `run_voter_turnout.py` | the harness: the arithmetic, both classifiers, both legends, the PNG |

## Run it

```bash
cd chapter8/analyzing_voter_disparity_via_choropleth_mapp/example/files
python3 voter_turnout_choropleth.py
```

It builds the counties and the election table, classifies turnout with Jenks and the
candidate's share with quantiles, prints both sets of breaks and the count per class, and
writes `output/voter_turnout_choropleth.png`. `run_voter_turnout.py` re-derives the rates,
checks that no county registers or votes impossibly, and confirms that each panel's legend
prints the breaks the classifier found (38 assertions).

```text
Loaded 12 administrative units for mapping.

--- Map A: Voter Turnout Rate, Jenks (k=5) ---
Breaks (%):  35.36, 50.54, 67.35, 80.29, 91.81
Counties per class: 2, 3, 3, 2, 2

--- Map B: Candidate A share, Quantiles (k=5) ---
Breaks (%):  35.98, 42.30, 48.93, 55.36, 66.37
Counties per class: 3, 2, 2, 2, 3
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/voter_turnout_choropleth.png` | the two-panel map, each panel with its own legend |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/voter_turnout.json` | both break lists, both count lists, the ranges, the legend edges |

## Notes

- The book loads `gpd.datasets.get_path('naturalearth_lowres')`. GeoPandas 1.0 removed the
  bundled datasets and this volume does not download, so the twelve counties are built as a
  4 by 3 mosaic over the United States interior. Same columns, same CRS, no network.
- Three defects in the printed script are fixed in place: `np.random.uniform(0.5, 0.7)`
  without a `size` multiplies a whole column by one constant (every county then has the
  same turnout); candidate votes are now a share of the votes actually cast, because the
  independent draw let one candidate take more votes than were cast; and the divisible-by-
  zero guard is kept.
- `scheme='NaturalBreaks'` inside `GeoDataFrame.plot()` re-runs the optimisation with
  different tie-breaking from `mapclassify.NaturalBreaks(...).bins` (44.5 against 47.1 on
  the same values), so the listing passes its own breaks as a `UserDefined` scheme. The
  legend then describes the map it is attached to.
- Map B is a diverging palette over a percentage, and the listing says what that costs:
  the white midpoint is not 50% of the vote here, so the red/blue split is a ranking, not a
  verdict. Exercise 2 maps the margin, which is what a diverging ramp is for.
