# Exercise 2 — masking clouds, then filling only the holes

## What it does

Builds a five-date NDVI cube and a matching QA band, one contaminated observation in
ten, and forces two interior observations of pixel (50, 50) to be cloudy so a gap
appears somewhere interpolation can reach. `apply_cloud_mask` compares the QA band
with the contamination flag, and `.where(~mask)` sets every contaminated value to
`NaN`. `interpolate_gaps` then fills along `time` with `interpolate_na`, and the
listing prints the raw, masked and filled series for that pixel side by side.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_2.py` | the exercise's prompt fence: the two signatures and the boolean logic it wants |
| `02_cloud_mask_gap_fill.py` | the solution: the QA band, the mask, the interpolation, the three series |
| `run_cloud_mask_gap_fill.py` | the harness: 17 assertions on the mask, both fills and the untouched values |

## Run it

```bash
cd chapter15/exercise_2_cloud_masking_and_temporal_gap_fil/exercise/files
python3 02_cloud_mask_gap_fill.py
```

It prints how many observations the mask removed and the raw, masked and interpolated
series of one pixel; `run_cloud_mask_gap_fill.py` asserts that exactly 5 025
observations were masked, that the two forced gaps are the ones filled, that the fill
is weighted by elapsed days, and that no clean observation moved.

```text
Contaminated observations: 5025 of 50000 (10.1%)
--- Cloud Masking and Interpolation Summary (Pixel 50, 50) ---
Raw Time Series: [0.2722 0.4773 0.398  0.7606 0.669 ]
Masked Time Series: [0.2722    nan 0.398     nan 0.669 ]
Interpolated Time Series: [0.2722 0.3348 0.398  0.5324 0.669 ]
```

## What it produces

| path | what it is |
| --- | --- |
| `output/cloud_mask.json` | the contamination count, both NaN counts, the three series, both time weights |

## Notes

- The first gap is filled at 0.3348, not at the midpoint 0.3351: January to July is
  182 days and July to January is 184, so `interpolate_na` weights the neighbours by
  date. The second gap shows the same effect three times larger — 0.5324 against an
  even average of 0.5335.
- A QA band that marks half of every pixel's observations cloudy, which is what the
  published version simulated, leaves gaps at the ends of the series that linear
  interpolation cannot fill; the demonstration then prints a filled series identical
  to the masked one. The listing contaminates one observation in ten and keeps the
  sampled pixel's end points clean.
- `nan` at the ends of a series is expected after `interpolate_na`: the method
  interpolates between observations, and there is nothing outside the record to
  interpolate from.
