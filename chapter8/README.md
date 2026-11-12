# Chapter 8 — Choropleth Maps - Visualizing Population and Elections

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `analyzing_voter_disparity_via_choropleth_mapp/example/` | `voter_turnout_choropleth.py` | Simulates twelve counties with an election each, derives two comparable metrics (turnout rate and one candidate's share of the vote), and draws them twice: Jenks natural breaks on the first, quantiles on the second. |
| `basic_code_example/example/` | `choropleth_density_by_region.py` | Builds the chapter's smallest complete choropleth: three polygons, a statistics table with a density and a turnout for each, a left join on `RegionID`, and one `GeoDataFrame.plot()` call whose `column=` turns boundaries into a map. |
| `exercise_1_the_impact_of_classification_schem/exercise/` | `density_classification_bias.py` | Takes one skewed table of four counties — one urban at 1 000 000 people per square mile, three rural at 11.43, 20 and 25 — and maps it twice with `k=7`, once by equal interval and once by quantiles. |
| `exercise_2_mapping_electoral_margin_using_jen/exercise/` | `electoral_margin_jenks.py` | Turns twenty simulated districts into a signed electoral margin — `(A - B) / (A + B)`, running from −1 to +1 — and maps it with a red-to-blue ramp whose neutral colour sits exactly on zero. |
| `exercise_3_advanced_filtering_with_logical_op/exercise/` | `coastal_vulnerability_filter.py` | Simulates fifteen Florida counties with a population, a median income and a coastal flag, then keeps only those that are coastal **and** either populous (over 500 000) or poor (under 45 000). |
| `exercise_4_the_interactive_challenge_dynamic/exercise/` | `interactive_tract_choropleth.py` | Moves the same idea into Folium: thirty census tracts with a 2020 population and a 2010–2020 change, classified into six Jenks classes, drawn as a `folium.GeoJson` layer where hovering a tract opens a tooltip with its identifier, its population and its change. |
| `exercise_5_modifying_advanced_visualization_t/exercise/` | `registration_rate_function.py` | Turns a raw count into a rate — registered voters divided by the voting-eligible population — and then puts the whole mapping step inside `generate_jenks_map(gdf, column_name, k_classes)`. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter8/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter8/output/run_8.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
