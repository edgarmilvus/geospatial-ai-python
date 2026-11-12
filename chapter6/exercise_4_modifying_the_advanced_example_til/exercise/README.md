# Exercise 4 — London, one visible layer and one that waits with its own notice

## What it does

Modifies a plain London map so that the second base layer is *not* drawn when the page
opens (`show=False`) and carries a project-specific attribution instead of the
provider's. Those are the two `TileLayer` parameters the exercise is about: visibility
decides what the reader sees first, attribution decides what the map claims about the
tiles once they do.

## The listings

| file | what it is |
| --- | --- |
| `london_custom_tiles.py` | the solution: named OSM base, hidden Toner layer, custom `attr` |
| `run_london_tiles.py` | the harness: checks the layer is listed, unattached and attributed |

## Run it

```bash
cd chapter6/exercise_4_modifying_the_advanced_example_til/exercise/files
python3 london_custom_tiles.py
```

It writes `output/london_custom_tiles.html`. `run_london_tiles.py` asserts that the
Toner layer appears in the control, that it is *not* attached to the map on load, that
the OSM layer is, and that the Toner layer's own options carry the required copyright
line; it exits non-zero if the layer becomes visible by default or loses its notice.

```text
Saved output/london_custom_tiles.html: OSM is the visible base layer, the Toner layer waits behind the layer control with its own attribution.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/london_custom_tiles.html` | the map: OSM drawn, the Toner layer one click behind |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/london_tiles.json` | the three control names, the layers drawn on load, the toner attribution |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline.
- `show=False` does not remove the layer: the `L.tileLayer(...)` object is still built
  and still registered with the control — it is simply never `.addTo(map)`. That is the
  difference the harness measures.
- Stamen Toner is a Stadia URL here, so the `attr` argument has two jobs: it replaces
  the provider's notice with the project's, and it satisfies folium's requirement that
  a custom template declare one at all.
