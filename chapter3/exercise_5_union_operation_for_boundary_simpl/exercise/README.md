# Exercise 5 — dissolve micro-zones into macro-regions

## What it does

Assigns each micro-zone to the macro-region it falls in, then dissolves by
`region_id`, summing population and averaging income. The geometry side is clean:
four 50 × 50 m zones become two regions of 5 000 m² each. The attribute side is the
lesson — `aggfunc='mean'` averages zone averages, so R2's 65 000 is not the regional
mean of its 3 000 people; the population-weighted figure is 56 666.67, and the listing
prints both.

## The listings

| file | what it is |
| --- | --- |
| `01_dissolve_regions.py` | the solution: sjoin, dissolve, aggregate, weighted comparison |
| `run_dissolve_regions.py` | the harness: areas, sums, both means, one region per zone |
| `prompt_sketch_exercise_5.py` | the exercise's prompt fence, kept exactly as the book prints it |

## Run it

```bash
cd chapter3/exercise_5_union_operation_for_boundary_simpl/exercise/files
python3 01_dissolve_regions.py
```

It prints the zone-to-region assignment, the dissolved regions with their summed and
averaged attributes, and the weighted income beside the plain mean; the harness
`run_dissolve_regions.py` asserts two 5 000 m² regions, populations 1 500 and 3 000 and
both income figures, and exits non-zero if a population is lost or the plain mean is
presented as the regional mean.

## What it produces

| path | what it is |
| --- | --- |
| `output/dissolve_regions.json` | region ids, areas, populations, both income measures |

```text
region_id  total_population  average_income
       R1              1500         55000.0
       R2              3000         65000.0

Region areas (m2): [5000.0, 5000.0]
Regions produced: 2 from 4 micro-zones
Population-weighted mean income: {'R1': 53333.33, 'R2': 56666.67}
```

## Notes

- Each region's two zones meet at a single corner, so the dissolve yields a
  `MultiPolygon` of two squares: a dissolve combines features by group, it does not
  merge polygons that fail to touch along an edge.
- `dissolve` is a `groupby` with a union for the geometry; everything else in
  `aggfunc` is ordinary pandas aggregation, with the same caveats.
- The `sjoin` is `how='left'` so a zone outside every region would keep its row and
  show up as a missing group rather than vanish from the total.
