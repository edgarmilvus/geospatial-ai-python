# Exercise 4 (interactive challenge) — a threshold in days, two colours on the map

## What it does

Simulates 15 sensors with inspection dates relative to today, asks for a maximum number
of days since the last inspection, and paints every sensor red — with an exclamation
icon and an OVERDUE popup — once its date falls behind the cutoff. The arithmetic is
`current_date - timedelta(days=threshold)`, and the comparison is on `date` objects, not
strings.

With no terminal attached the listing does not wait: it takes the documented default of
30 days and says so, which is what a scheduler, a notebook cell or a test suite gets.

## The listings

| file | what it is |
| --- | --- |
| `sensor_inspection_filter.py` | the solution: dated data, guarded input, cutoff, markers |
| `run_sensor_filter.py` | the harness: recomputes the cutoff and checks the red set |

## Run it

```bash
cd chapter7/exercise_4_interactive_challenge_time_sensiti/exercise/files
python3 sensor_inspection_filter.py
```

In a terminal it prompts for the threshold; with stdin redirected it prints the default
it used, the cutoff date, and writes `output/exercise4_time_filter.html`.
`run_sensor_filter.py` drives the non-interactive branch, recomputes the cutoff from the
run's own clock, and asserts that exactly the sensors behind it are red and the others
green; it exits non-zero if the two counts stop adding up to 15.

```text
No terminal attached: using the default threshold of 30 days.

Filtering assets. Cutoff Date: 2026-10-04. Threshold: 30 days.
Saved output/exercise4_time_filter.html: 5 of 15 sensors overdue at a 30-day threshold.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/exercise4_time_filter.html` | the map with its red and green sensors |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/sensor_filter.json` | the threshold, the cutoff, the overdue/current counts, the view |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- The dates come from `datetime.now()`, so the artefact's cutoff changes from one day to
  the next — that is the point of the exercise. The counts do not: the seed fixes which
  sensors are old, so `5 of 15` is stable while `2026-10-04` is not.
- The old dates are drawn 30 to 59 days back and the recent ones 0 to 14 days back, so a
  30-day threshold separates them cleanly; a threshold of 20 would also mark some of the
  recent ones.
- The prompt is guarded with `sys.stdin.isatty()`: a listing that blocks on `input()` is
  a listing no harness can run.
