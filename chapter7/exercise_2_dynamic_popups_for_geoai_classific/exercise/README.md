# Exercise 2 — the attribute table, reformatted into an HTML popup

## What it does

Takes five classified points and gives each one a popup built with f-strings: the class
as a heading, the confidence multiplied by 100 and rounded to one decimal, the analysis
date in italics, and the confidence coloured green above 0.8 and red at or below it. The
HTML is wrapped in an `IFrame` and then in a `Popup`, which is the chapter's recommended
way to keep custom CSS from leaking into the map.

## The listings

| file | what it is |
| --- | --- |
| `classification_popups.py` | the solution: five points, percentage formatting, HTML popup |
| `run_classification_popups.py` | the harness: decodes each popup and checks the formatted strings |

## Run it

```bash
cd chapter7/exercise_2_dynamic_popups_for_geoai_classific/exercise/files
python3 classification_popups.py
```

It writes `output/exercise2_dynamic_popups.html`. `run_classification_popups.py`
decodes every iframe, then asserts that each popup names its class, shows the score as
98.5%, 72.1%, 85.0%, 99.9% or 65.5%, quotes the date, and is coloured by the 80%
rule — four green and one red; it exits non-zero if a percentage is formatted
differently or the threshold moves.

```text
Saved output/exercise2_dynamic_popups.html: 5 markers, confidence shown as a percentage and coloured at the 80% threshold.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/exercise2_dynamic_popups.html` | the five markers with their report popups |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/classification_popups.json` | the five percentages, the green/red split, centre and zoom |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- The 80% rule is written twice — once as the colour of the number, once as the branch
  that picks it — so the harness reads both counts out of the decoded popups rather than
  trusting the source.
- `max_width=2650` in the book's listing is far wider than the 220 px iframe it wraps;
  it is harmless, and the harness does not depend on it.
