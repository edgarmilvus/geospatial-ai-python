# Example 2 — five base maps in one file, switched from a control panel

## What it does

Builds a map of the San Francisco Bay Area with five interchangeable base layers and
saves it with a `LayerControl` in the top right corner. The dictionary `TILE_LAYERS`
is the whole application: its keys are the names the reader sees, and its values are
what folium asks for. Every layer is added with `overlay=False`, which is what makes
Leaflet render the control as radio buttons — one base map at a time — instead of
checkboxes.

`control_scale=True` adds the scale bar, and `finalize_and_save_map` returns the size
of the file it wrote rather than printing a bare filename.

## The listings

| file | what it is |
| --- | --- |
| `tile_layer_switcher.py` | the listing: configuration, three functions, a guarded main block |
| `run_tile_switcher.py` | the harness: reads the layer control out of the HTML and checks all five |

## Run it

```bash
cd chapter6/advanced_application_script/example/files
python3 tile_layer_switcher.py
```

It builds the map, adds the four non-default layers and writes
`output/Infrastructure_Tile_Switcher.html`. `run_tile_switcher.py` calls the three
functions the main block calls, then asserts that the control holds five base layers
in the configured order, that no overlay is registered, that each name resolves to
its own tile template, and that the Toner and Terrain attributions reached the
document; it exits non-zero if any of those change.

```text
--- Starting Folium Map Generation (2026-11-03 16:59:05) ---
Base map initialized at (37.7749, -122.4194) with zoom 12.
Added 4 selectable tile layers on top of the default.

--- Process Complete ---
Map successfully saved to output/Infrastructure_Tile_Switcher.html. Size: 7.04 KB.
Open the HTML file in any web browser to view the interactive map.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/Infrastructure_Tile_Switcher.html` | the standalone map with its five-way base-layer control |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/tile_switcher.json` | centre, zoom, the five control names, their tile URLs, the size |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline. Each tile template is only a string in the
  document until a browser asks for a tile.
- The three Stamen styles left folium's built-in tile table when they moved to Stadia
  Maps, so their URLs are written out in `TILE_LAYERS` and every one of them is given
  an attribution — a custom template without one is a `ValueError`, not a warning.
- Stadia serves localhost without a key; on a public host the same URLs want one, so
  the tile images can come out blank even though the document is correct.
- Only four layers are added by `add_multiple_tile_layers`; the fifth is the map's own
  default, which is why the message counts four.
