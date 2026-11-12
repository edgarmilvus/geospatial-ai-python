# Exercise 3 — a cluster that turns red when it hides a Priority 1

## What it does

Clusters 500 simulated utility defects and then overrides the cluster icon from inside
Leaflet: `icon_create_function` walks the markers the cluster contains, reads their
popup text, and if any of them says `Priority: 1` it swaps the default blue disc for a
red, larger one. The CSS class it switches to is injected into the document with
`folium.Element`, because folium has no first-class way to add a stylesheet.

## The listings

| file | what it is |
| --- | --- |
| `conditional_cluster_icons.py` | the solution: 500 points, the JS hook, the injected CSS, the markers |
| `run_conditional_clusters.py` | the harness: checks the data, the hook and the contract between them |

## Run it

```bash
cd chapter7/exercise_3_conditional_clustering_and_priorit/exercise/files
python3 conditional_cluster_icons.py
```

It writes `output/exercise3_conditional_clustering.html`. `run_conditional_clusters.py`
asserts that the 500 points carry 29 Priority 1 values, that 500 markers each keep their
own popup, that the icon factory and the `.marker-cluster-critical` rule both reached the
document, and that the factory looks for the exact text the Python side writes; it exits
non-zero when the popup wording and the JavaScript stop agreeing.

```text
Saved output/exercise3_conditional_clustering.html: 500 defects, 29 of them Priority 1, clustered by Leaflet at load time.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/exercise3_conditional_clustering.html` | the clustered map plus the custom cluster CSS |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/conditional_clusters.json` | the priority counts, the marker total, centre and zoom |

## Notes

- The HTML needs a browser **and an internet connection to show the basemap tiles**;
  the file itself is generated offline. The conditional styling runs in the browser, so
  the harness can check the contract but not the colour a reader finally sees.
- The contract is textual: the JavaScript searches each popup's HTML for `Priority: 1`.
  The listing therefore writes the popup with an integer priority — `iterrows()` hands
  the row back as floats once it holds coordinates, so `int(...)` is what keeps the text
  at `Priority: 1` instead of `Priority: 1.0`.
- 29 of 500 is 5.8%, the draw the fixed seed produces from `p=[0.05, 0.35, 0.60]`, not a
  round number.
