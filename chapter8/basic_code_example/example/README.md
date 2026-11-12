# Example 1 — join a table onto boundaries, then colour by the column

## What it does

Builds the chapter's smallest complete choropleth: three polygons, a statistics table with
a density and a turnout for each, a left join on `RegionID`, and one `GeoDataFrame.plot()`
call whose `column=` turns boundaries into a map. The point is the join, not the drawing:
the geometry column survives the merge, and every polygon's fill is its value on the
column's own range.

## The listings

| file | what it is |
| --- | --- |
| `choropleth_density_by_region.py` | the listing: three regions, two statistics, one merge, one map |
| `run_choropleth_density.py` | the harness: the join, the ramp, the fills, the PNG |

## Run it

```bash
cd chapter8/basic_code_example/example/files
python3 choropleth_density_by_region.py
```

It merges the table onto the boundaries, prints the three densities and where each sits on
the ramp, and writes `output/basic_choropleth_density.png`. `run_choropleth_density.py`
re-checks the join, the ramp's ends and the order of the fills (25 assertions) and exits
non-zero if a region loses its statistic or the colours stop following the values.

```text
--- Merged GeoDataFrame ---
RegionID     RegionName  PopulationDensity  VoterTurnout
     A01   North Sector                150          0.65
     B02   Central Zone                450          0.78
     C03 South District                250          0.71
Rows: 3; CRS: EPSG:4326
Missing densities after the left join: 0
Planar areas (square degrees): [100, 100, 200]

--- Ramp ---
Colour range: 150 to 450 (the column's own min and max)
  A01: density 150 -> 0.00 of the ramp
  B02: density 450 -> 1.00 of the ramp
  C03: density 250 -> 0.33 of the ramp
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/basic_choropleth_density.png` | the two-panel-free map: three regions, one colour bar |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/basic_choropleth.json` | densities, turnout, areas, ramp ends, fill luminance |

## Notes

- The coordinates are 0–40 in an abstract plane, not degrees, so the areas (100, 100, 200)
  are topology. The listing says so, and silences geopandas' geographic-area warning for
  that reason.
- `plasma` runs dark to light, so the 450 region is the brightest of the three; the harness
  asserts that order rather than a colour value, because a colormap is a versioned thing
  and a ramp is not.
- The book ends on `plt.show()`. The figure is written into `output/` instead, so the same
  file can be checked by a script.
