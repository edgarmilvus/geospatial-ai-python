# Chapter 3 — Spatial Operations - Intersections, Joins, and Buffers

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `infrastructure_impact_zone_analysis/example/` | `01_highway_impact.py` | Creates a proposed four-kilometre route north of Minneapolis, two protected wetlands and five parcels in WGS 84 lon/lat, then does what the chapter insists on: reprojects to UTM zone 15N before it buffers 50 metres, joins the parcels inside the corridor, and intersects the route with the wetlands to measure how many metres of road cross protected ground. |
| `basic_code_example/example/` | `01_zoning_overlay_basics.py` | Runs the four operations the chapter introduces on two rectangles whose overlap can be checked by hand: a Development Zone spanning (0,0)–(10,8) and a Natural Reserve spanning (5,4)–(15,12). |
| `exercise_1/exercise/` | `01_pipeline_corridor_impact.py` | Buffers a 10 km pipeline by 500 m, intersects that corridor with three parcels, computes each overlap's area, joins the parcels' original areas back and reports the percentage of each parcel the corridor consumes. |
| `exercise_2_wildfire_damage_quantification_usi/exercise/` | `01_wildfire_damage.py` | Intersects three protected zones with a 10 × 10 km fire perimeter, converts the resulting areas from square metres to hectares at 10 000 m² per hectare, and groups by ecosystem to produce one summary row per damaged zone. |
| `exercise_3_attribute_aggregation_via_spatial/exercise/` | `01_residential_counts.py` | Joins ten building detections to two neighborhood polygons, filters the joined frame to `Residential`, and counts per neighborhood. |
| `exercise_4_advanced_geoai_feature_engineering/exercise/` | `01_enriched_sites.py` | Builds an enriched extraction-site layer in three moves: a 100 m buffer around the sensitive area joined back as a boolean proximity flag, a concession assignment, and the area of overlap between a 50 m buffer around each site and the sensitive area. |
| `exercise_5_union_operation_for_boundary_simpl/exercise/` | `01_dissolve_regions.py` | Assigns each micro-zone to the macro-region it falls in, then dissolves by `region_id`, summing population and averaging income. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter3/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter3/output/run_3.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
