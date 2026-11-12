# Chapter 5 — Plotting Static Maps - Customizing Matplotlib for Geography

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `professional_cartography_with_crs_control/example/` | `01_professional_choropleth.py` | Draws the cartographic object the chapter is aiming at: eleven districts over California, handed to an EPSG:3857 `GeoAxes` in WGS 84 so Cartopy reprojects them, shaded with a five-stop ramp and given a colour bar, laid over a basemap built from two polygons and projected by the same axes, with a 50 km scale bar and a north arrow. |
| `basic_code_example/example/` | `01_plate_carree_world.py` | Builds a 58-polygon world in WGS 84 and plots it on a Cartopy `GeoAxes` created with `projection=ccrs.PlateCarree()`: a labelled graticule every 30 degrees of longitude and 20 of latitude, an extent of ±180° by ±90° set in the data's own CRS, and a title that states the example's claim — the data's CRS and the axes' projection are the same, so nothing is transformed and nothing is distorted. |
| `exercise_1_visualizing_projection_distortion/exercise/` | `01_projection_distortion_triptych.py` | Draws the same 58 land cells on three `GeoAxes`, one per projection: Plate Carrée where they are 34 800 square degrees of nothing in particular, Eckert IV where they measure 281 934 706 km² — the ellipsoidal answer — and Web Mercator where the same cells measure 840 665 508 km², 2.98 times as much. |
| `exercise_2_dynamic_scale_bars_and_north_arrow/exercise/` | `01_scale_bar_north_arrow.py` | Puts six regions of the Great Lakes and Saint Lawrence on a UTM 17N `GeoAxes` — so the axes' units are metres — shades them with a custom density ramp, adds a labelled Cartopy graticule, and draws the two annotations the exercise is about: a 150 km scale bar of four alternating 37.5 km segments measured in the projection's metres, and a north arrow whose label and shaft both live in axes coordinates. |
| `exercise_3_advanced_matplotlib_object_model_f/exercise/` | `01_main_map_with_inset.py` | Draws North America on an Albers Equal Area `GeoAxes` with an inset of the Aleutians on a second `GeoAxes` in an azimuthal equidistant projection, and links them: the inset's extent is converted into the main map's projection with `transform_points` and drawn there as a dashed rectangle 1 149 750 × 1 182 249 m across (1.36 million km²). |
| `exercise_4_refactoring_and_enhancing_a_multi/exercise/` | `01_refactored_annotation_layers.py` | Takes a map built from `plt.*` calls and rebuilds it from artists on a UTM 48N `GeoAxes`: `ax.set_title` plus a figure `suptitle`, a legend assembled from `Patch` handles, round metric ticks, a scatter marker at a projected coordinate, a 5 km × 5 km box around a port and an `annotate` callout. |
| `exercise_5_interactive_challenge_auto_adjusti/exercise/` | `01_dynamic_scale_and_grid.py` | Chooses the scale bar's number from the view instead of hard-coding it: at a 150 km wide extent the search returns a 25 km bar, at 800 km it returns 200 km, and the grid steps from 50 km to 100 km so its labels stay round numbers — all on a UTM 17N `GeoAxes`, whose data coordinates are metres, which is why `ax.get_xlim()` is what the search reads. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter5/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter5/output/run_5.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
