# Advanced example — the date a pixel lost its canopy

## What it does

Builds a sixty-month Sentinel-2 cube (2019-01 to 2023-12) of 50 × 50 pixels, injects a
clear-cut in a 10 × 10 block from month 30, converts both bands to NDVI, and then
dates the change per pixel. The first twenty-four months establish the expected
trajectory — a per-pixel mean and standard deviation (0.0245 across the block) — every later observation is
scored against that baseline, and a pixel is dated only after three consecutive
months fall below z = −2.5. The report converts the flagged pixels to hectares at
100 m² per pixel.

## The listings

| file | what it is |
| --- | --- |
| `01_deforestation_date_detection.py` | the listing: the cube, the baseline, the persistence scan, the report |
| `run_deforestation_dates.py` | the harness: 24 assertions on the block, the dates, the area and the persistence filter |

## Run it

```bash
cd chapter15/advanced_application_script/example/files
python3 01_deforestation_date_detection.py
```

It prints the baseline window, the threshold, the pixels analysed and affected, the
area in hectares and the earliest and latest detected dates; `run_deforestation_dates.py`
asserts that all one hundred pixels of the cleared block are flagged at month 29 or
30, that fewer than ten other pixels are, and that the persistence filter is what
holds the count near a hundred.

```text
Generating synthetic Sentinel-2 stack (60 monthly observations)...
Running time series anomaly detection...

--- Deforestation Tracking Report ---
Analysis Period: 2019-01-01 to 2023-12-31
Baseline Window: 24 months, 2019-01-01 to 2020-12-01
Anomaly Threshold: Z-score < -2.5
Persistence Requirement: 3 consecutive months
-----------------------------------
Total Pixels Analyzed: 2500
Total Affected Pixels: 103
Total Deforested Area: 1.03 Hectares
Earliest Detected Event Date: 2021-06-01
Latest Detected Event Date: 2023-03-01
```

## What it produces

| path | what it is |
| --- | --- |
| `output/deforestation_dates.json` | the affected count, the block's dates, the area and both NDVI levels |

## Notes

- **The baseline is the first 24 months, not the whole record.** The published
  version averaged the cube over all sixty months, which let the cleared years pull
  the mean down and the standard deviation up; the resulting z-scores never reached
  −2.5 and the report claimed zero affected pixels for a scene with a 10 × 10
  clear-cut. `BASELINE_STEPS` is the correction, and it is also what the chapter's
  theory section describes: model the expected trajectory, then look for the break.
- Three of the 103 flagged pixels lie outside the injected block. They are noise that
  survived the three-month filter in a 2 500-pixel scene, and the harness allows up to
  ten of them rather than asserting the injected hundred alone.
- A pixel's date can be month 29 rather than 30: if its last baseline month happened
  to dip below the threshold, the run of three anomalies starts one month before the
  clear-cut and the reported date follows the first dip, not the felling.
- The cube is drawn from `np.random.default_rng(15)` and the calendar from
  `freq='MS'`; `freq='M'` is deprecated in pandas 2.2 and would print a warning on
  every run.
