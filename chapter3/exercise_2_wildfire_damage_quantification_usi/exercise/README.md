# Exercise 2 — burned hectares by ecosystem

## What it does

Intersects three protected zones with a 10 × 10 km fire perimeter, converts the
resulting areas from square metres to hectares at 10 000 m² per hectare, and groups by
ecosystem to produce one summary row per damaged zone. Zone 201 is fully burned
(900 ha), zone 202 contributes the 5 × 5 km the fire reaches (2 500 ha), zone 203 is
20 km away and disappears from the result.

## The listings

| file | what it is |
| --- | --- |
| `01_wildfire_damage.py` | the solution: overlay, hectares, groupby, summary table |
| `run_wildfire_damage.py` | the harness: per-zone hectares, both summary rows, the 3 400 ha total |
| `prompt_sketch_exercise_2.py` | the exercise's prompt fence, kept exactly as the book prints it |

## Run it

```bash
cd chapter3/exercise_2_wildfire_damage_quantification_usi/exercise/files
python3 01_wildfire_damage.py
```

It prints the fire's size, which zones the fire touches and the ecosystem summary
table; `run_wildfire_damage.py` asserts 900 and 2 500 ha on the right rows, a
3 400 ha total and zone 203 absent, and exits non-zero if the overlay or the
hectare conversion changes.

## What it produces

| path | what it is |
| --- | --- |
| `output/wildfire_damage.json` | fire size, burned zones, hectares per zone, the summary, the divisor |

```text
Fire perimeter: 10,000 ha
Zones touched by the fire: [201, 202]

   ecosystem_type  total_burned_hectares
Old Growth Forest                  900.0
  Wetland Habitat                 2500.0

Total burned across protected zones: 3,400.0 ha
Zones left untouched: [203]
```

## Notes

- `keep_geom_type=True` keeps the overlay to the polygon side; without it a mixed
  layer can return pieces that have no area to convert.
- The hectare step is a division by 10 000, not by 1 000: a square kilometre is
  100 hectares, and zone 201 is 3 × 3 km = 9 km² = 900 ha.
- The fire is 10 000 ha and the protected damage is 3 400 ha — a subset, which the
  harness checks so a double-counted zone cannot pass.
