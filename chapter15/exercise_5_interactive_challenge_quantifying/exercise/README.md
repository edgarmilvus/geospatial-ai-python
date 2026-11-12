# Exercise 5 — hectares per year, and the line that shows the loss

## What it does

Simulates three annual boolean deforestation maps over a 500 × 500 pixel scene, at
1 %, 2 % and 3 % loss, and converts each map's `True` count into hectares at 100 m²
per pixel. `aggregate_annual_loss` walks the time axis, calls
`calculate_area_hectares` once per year and accumulates the totals with `np.cumsum`;
`plot_cumulative_loss` draws the running total into `output/annual_deforestation.png`
and closes the figure.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_5.py` | the exercise's prompt fence: the three signatures and the conceptual stack |
| `02_annual_area_plot.py` | the solution: the stack, the conversion, the cumulative sum and the figure |
| `run_annual_area.py` | the harness: 26 assertions on the counts, the arithmetic, the curve and the PNG |

## Run it

```bash
cd chapter15/exercise_5_interactive_challenge_quantifying/exercise/files
python3 02_annual_area_plot.py
```

It prints each year's area, the cumulative total and the scene size, and writes the
plot; `run_annual_area.py` asserts that each total is its pixel count times 100 m²
over 10 000, that the cumulative line is the running sum, that the three totals sit
near 25, 50 and 75 hectares, and that the PNG is a real figure.

```text
--- Annual Deforestation Quantification ---
Deforestation detected in 2020: 25.82 Hectares
Deforestation detected in 2021: 50.52 Hectares
Deforestation detected in 2022: 75.74 Hectares
Cumulative loss after 2022: 152.08 Hectares
Total pixels analysed: 250000, each 100 square metres
Plot saved to: annual_deforestation.png
```

## What it produces

| path | what it is |
| --- | --- |
| `output/annual_deforestation.png` | the cumulative-loss line, saved at 150 dpi |
| `output/annual_area.json` | the three counts, three totals, the cumulative series and the byte size |

## Notes

- The published version passed `dtype=bool` to `xr.DataArray`, which numpy-backed
  xarray rejects with `TypeError`; the array from `np.stack` of three boolean draws is
  already boolean, so the argument is simply gone.
- `plt.show()` would have blocked or drawn nothing in a headless run. The listing
  saves the figure under `output/` and closes it, and the harness asserts that
  `plt.get_fignums()` is empty afterwards so a leaked figure cannot accumulate.
- The draws are seeded, so the totals are 25.82, 50.52 and 75.74 rather than a fresh
  set of numbers on every run. The three rates still land where the simulation asks:
  within three hectares of 25, 50 and 75.
