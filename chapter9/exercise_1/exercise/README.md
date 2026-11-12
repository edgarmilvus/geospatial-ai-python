# Exercise 1 — cleanse the logs, then draw the baseline density

## What it does

Builds the exercise's noisy taxi feed (50 000 rows, 5 per cent of them with a zero, a null
or a numeric string in a coordinate), then runs the three gates the prompt asks for: parse
to numeric, drop nulls and zeros, check the geographic bounds. The survivors become a
`GeoDataFrame` in WGS 84 and a seaborn two-dimensional KDE over the city.

## The listings

| file | what it is |
| --- | --- |
| `gps_cleansing_baseline_kde.py` | the solution: the CSV, the three filters, the density figure |
| `run_gps_cleaning.py` | the harness: the pipeline rebuilt, the dtypes, the figure as pixels |

## Run it

```bash
cd chapter9/exercise_1/exercise/files
python3 gps_cleansing_baseline_kde.py
```

It writes `output/raw_gps_logs.csv`, cleans it, prints how many rows each gate removed and
what bandwidth the density used, then saves `output/gps_density_baseline.png`.
`run_gps_cleaning.py` rebuilds the whole pipeline from the raw frame and opens the PNG as an
array to confirm it is a gradient and not a blank page (33 assertions); it exits non-zero if
the surviving count or a dtype changes.

```text
Cleaned records: 47765
--- Cleaning ---
Rows written to output/raw_gps_logs.csv: 50000
Rows whose coordinates would not parse (zero, null or text): 1370
Rows left after dropping nulls, zeros and out-of-range values: 47765
Removed: 2235 rows (4.47 %)
Latitude: 40.6000 to 40.9000
Longitude: -74.0500 to -73.8000
CRS: EPSG:4326; points: 47765
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/raw_gps_logs.csv` | the noisy feed, regenerated deterministically on every run |
| `output/gps_density_baseline.png` | the 2D KDE over the cleaned points |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/gps_cleaning.json` | rows in, coerced, removed, the ranges, the bandwidth, the image size |

## Notes

- 2 235 rows are removed: 1 370 rows had a coordinate that would not parse, and the rest are
  zeros or nulls in the other column. That is 4.47 per cent of the feed, not the 10 per cent
  the generator drew, because a row with one bad coordinate may still be dropped only once.
- The text values `'40.9'` and `'-73.8'` *parse* as numbers and are inside the bounds, so
  they survive the filters. What catches them is the `float64` enforcement — which is exactly
  the point the exercise's requirement 2 makes.
- `bw_adjust` is a multiplier on seaborn's reference bandwidth, not a bandwidth. The book's
  `H_BANDWIDTH * 200` happened to equal 1.0, so the "0.005 degrees" in its comment was never
  applied. The listing divides the target by the reference (0.0099 degrees) and prints the
  resulting factor, 0.507.
- 50 000 points through a 2D KDE take about nine seconds; that is the cost the exercise's
  "computational load" note is talking about.
