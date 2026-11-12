# Exercise 1 — ten survey points, styled by severity

## What it does

Turns a table of drone detections into a map a field team can triage at a glance: four
severity levels, four colours, four icons, and a popup that states the level in words.
The styling lives in one `severity_styles` dictionary, so the loop that places the
markers never contains an `if` about colour — the table is the mapping, and the loop
only looks it up.

## The listings

| file | what it is |
| --- | --- |
| `drone_severity_markers.py` | the solution: ten points, the style table, the marker loop |
| `run_drone_severity.py` | the harness: checks the table covers the data and the map follows it |

## Run it

```bash
cd chapter7/exercise_1/exercise/files
python3 drone_severity_markers.py
```

It writes `output/exercise1_drone_hotspots.html`. `run_drone_severity.py` asserts that
the four levels occur in the counts the data defines, that every level has a style so no
point falls through the lookup, that the marker colours and icons in the document match
those counts, and that each marker carries its severity popup; it exits non-zero if a
level loses its entry or the map stops following the table.

```text
Saved output/exercise1_drone_hotspots.html: 10 markers, 4 severity levels, one colour and icon per level.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/exercise1_drone_hotspots.html` | the ten styled markers around Los Angeles |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/drone_markers.json` | the severity counts, the colour each level maps to, centre and zoom |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- `folium.Icon(color='yellow')` is not one of Bootstrap's marker colours; folium warns
  and renders the marker white with a yellow-warning text of its own. The listing keeps
  the exercise's colour, and the harness silences the warning because it is the
  exercise's choice, not a defect.
- Medium and Low share the `info` glyph, so the harness counts icons by name rather than
  per level: six markers carry `info`, not three.
