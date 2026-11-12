# Exercise 4 — the same bandwidth, two kernels, two surfaces

## What it does

Computes two density surfaces over the cleaned feed with one fixed bandwidth of 0.008
degrees: Gaussian from `scipy.stats.gaussian_kde`, and Epanechnikov from first principles
with a `cKDTree` — the kernel is `2/π(1 − u²)` inside the radius and exactly zero outside
it. Both surfaces integrate to 1.0, and the difference between them is countable: 0 zero
cells against 6 416.

## The listings

| file | what it is |
| --- | --- |
| `kernel_comparison.py` | the solution: a noisy feed, two kernels, two heat layers, timings |
| `run_kernel_comparison.py` | the harness: the cleaning, the masses, the zeros, the peaks |

## Run it

```bash
cd chapter9/exercise_4_the_advanced_modification_challeng/exercise/files
python3 kernel_comparison.py
```

It writes a noisy feed to `output/noisy_trips.csv`, cleans it as exercise 1 does, evaluates
both surfaces on a 120 by 120 grid, prints the masses, the zeros, the peaks and the timing
ratio, then writes `output/kernel_comparison.html` with the two layers togglable.
`run_kernel_comparison.py` calls `main()` and compares the two (36 assertions); it exits
non-zero if the Epanechnikov surface stops being exactly zero outside the bandwidth or either
surface stops integrating to one.

```text
--- 3030 pings (3150 rows read, 120 rejected), 120x120 grid ---
Fixed bandwidth: 0.008 degrees (891 m of latitude)

--- Kernel Performance Comparison ---
Gaussian Kernel Calculation Time: 0.2095 seconds
Alternative (Epanechnikov) Kernel Calculation Time: 0.0985 seconds
Ratio (Gaussian / Epanechnikov): 2.1x

--- Surfaces ---
Gaussian:      peak 1048.5 at 34.0549 N, -118.2490 E; zero cells 0; mass 0.999
Epanechnikov:  peak 2436.0 at 34.0566 N, -118.2505 E; zero cells 6416; mass 0.999
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/noisy_trips.csv` | the feed: 3 000 pings plus 150 rows of noise |
| `output/kernel_comparison.html` | one map, two heat layers, one control |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/kernel_comparison.json` | masses, zero counts, peaks, timings, layer sizes |

## Notes

- The book's version does not compute an Epanechnikov surface. It times the Gaussian run and
  then sets `time_epanechnikov = time_gaussian * 0.95` — a simulated 5% improvement — because
  scipy's 2D KDE does not expose kernel choice. The listing implements the kernel, with a
  k-d tree standing in for the neighbourhood query that finite support makes possible.
- The exercise's requirement 1 is "load and clean the data as in exercise 1", so the feed is
  written and read through the same three gates: 3 150 rows in, 120 rejected. The other 30
  noise rows carry `'34.05'` and `'-118.24'`, which parse and are in bounds — the same trap
  exercise 1 is built around.
- The timing ratio is 2.1× on this machine, and timings are machine-dependent, so the harness
  asserts only that both runs completed in a plausible band. The *invariant* claim is the
  support count, which does not depend on the hardware.
- Both layers use `radius=8`. The book gives them 8 and 6.4 (1000 and 800 times the
  bandwidth), which would make the visible difference a rendering parameter rather than the
  kernel.
- The two peaks are 0.002 degrees apart: a finite-support kernel sharpens a hotspot, it does
  not move it.
