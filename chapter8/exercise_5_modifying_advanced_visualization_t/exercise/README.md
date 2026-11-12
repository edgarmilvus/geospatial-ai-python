# Exercise 5 — normalise the count, then wrap the map in a function

## What it does

Turns a raw count into a rate — registered voters divided by the voting-eligible population
— and then puts the whole mapping step inside `generate_jenks_map(gdf, column_name,
k_classes)`. The function is called twice, on two different columns, and produces two maps
with two different sets of breaks; that second call is what proves it is a function and not
a script with a variable in it.

## The listings

| file | what it is |
| --- | --- |
| `registration_rate_function.py` | the solution: the rate, the function, two calls |
| `run_registration_rate.py` | the harness: the rate, the signature, both maps, both files |
| `prompt_sketch_exercise_5.py` | the exercise's own prompt fence, as the book prints it |

## Run it

```bash
cd chapter8/exercise_5_modifying_advanced_visualization_t/exercise/files
python3 registration_rate_function.py
```

It computes the rate for fifty states, calls the function on `RegistrationRate` with five
classes and again on `VEP` with four, printing the breaks, the count per class and the file
each call wrote. `run_registration_rate.py` re-derives the rate, reads the function's
signature, and checks that the two calls really produced two different classifications and
two different PNGs (33 assertions).

```text
Map generated for column: RegistrationRate with k=5 classes.
Breaks: 56.3, 66.9, 73.0, 84.1, 93.6
States per class: 5, 10, 9, 13, 13
Saved: output/jenks_registrationrate.png

--- Registration rate, before classification ---
States: 50; range 55.53 to 93.61 %
States whose rate was capped at 100%: 0
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/jenks_registrationrate.png` | the rate map, five Jenks classes |
| `output/jenks_vep.png` | the second call, four classes, its own breaks |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/registration_rate.json` | the rate range, both break sets, both file names, the signature |

## Notes

- The book draws `Total Registered Voters` and `VEP` independently, so twenty of fifty states
  register more voters than they have eligible voters. Clipping that to 100% (which the book
  does) would put twenty states in the top class and report a break that is an artefact of
  the generator. The listing draws registration as a share of VEP instead, and the clip is
  kept as a guard that fires on nothing.
- The function returns the axis, the classifier and the file it wrote. As printed in the
  book it ends with `plt.close(fig)`, so the map it built existed for one line and was then
  discarded — a "standardised map generator" with no output.
- The book's `scheme='NaturalBreaks'` string would classify inside `.plot()` with breaks the
  caller cannot see. The listing classifies once and passes the breaks as a `UserDefined`
  scheme, so the legend and the returned numbers agree.
- The `TODO` about SQLAlchemy stays: it is a comment about the production data path, not
  something the exercise asks to implement.
