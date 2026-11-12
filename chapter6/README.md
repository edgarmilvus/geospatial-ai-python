# Chapter 6 — Introduction to Folium - Creating HTML Maps

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script/example/` | `tile_layer_switcher.py` | Builds a map of the San Francisco Bay Area with five interchangeable base layers and saves it with a `LayerControl` in the top right corner. |
| `initializing_and_saving_a_folium_map/example/` | `fuji_map_initialization.py` | Instantiates a `folium.Map` and saves it as a standalone HTML file. |
| `exercise_1_the_urban_contrast_map/exercise/` | `sf_contrast_map.py` | Answers the exercise in six lines of folium: a map centred on 37.7749 N, −122.4194 W at zoom 12, OpenStreetMap on load, and a high-contrast layer named "High Contrast Roads" in the control beside it. |
| `exercise_2_the_alpine_terrain_explorer/exercise/` | `alpine_terrain_map.py` | Puts the topography first: the map is centred on 45.9766 N, 7.6585 E and loads with the Stamen Terrain template, at zoom 14 — close enough to read the contours, wide enough to keep the valleys in frame. |
| `exercise_3_the_coastal_aesthetic_switcher_int/exercise/` | `rio_aesthetic_switcher.py` | One city, three visual languages: the readable street map, the watercolour, and the dark background meant for light-coloured data. |
| `exercise_4_modifying_the_advanced_example_til/exercise/` | `london_custom_tiles.py` | Modifies a plain London map so that the second base layer is *not* drawn when the page opens (`show=False`) and carries a project-specific attribution instead of the provider's. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter6/run_offline.sh
```

`run_offline.sh` runs the 6 harnesses and prints one line per harness;
the log is written to `chapter6/output/run_6.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
