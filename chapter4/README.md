# Chapter 4 — Geometric Manipulations - Calculating Areas and Distances

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script_urban_infrastruct/example/` | `01_urban_impact_assessment.py` | Measures one industrial zone twice, on purpose. |
| `basic_code_example/example/` | `01_irregular_parcel_metrics.py` | Builds an L-shaped polygon from seven vertices in a planar coordinate system where one unit is one metre, then reads the three metrics every feasibility study starts from: `area` (75 square units), `length` for the boundary a fence must follow (40 units), and `centroid` as the point a survey drone would visit. |
| `exercise_1/exercise/` | `01_parcel_metrics_starter.py` | Takes the pentagon the exercise hands the reader — (10, 20), (35, 5), (50, 30), (40, 60), (20, 50) — builds it as a `shapely.Polygon`, guards the construction with the exercise's own `InvalidGeoFeatureError`, and prints the three metrics a planner needs before any projection work starts: 1 325 square units of land, 143.92 units of boundary, and a centroid at (30.9119, 32.0440) for the first utility hookup. |
| `exercise_2_geodesic_vs_planar_distance_in_hig/exercise/` | `01_high_latitude_distance.py` | Measures Svalbard to Reykjavik twice: once as a diagonal through a plane of degrees (40.1311°), once along the WGS 84 ellipsoid (2 000.05 km), and quantifies the gap. |
| `exercise_3_geoai_proximity_agent_dynamic_faci/exercise/` | `01_proximity_assignment.py` | Puts one incident at 500000/4500000 in UTM zone 10N and five service centres around it, finds the nearest with the vectorised `GeoSeries.distance`, and turns the pair into a search radius: the nearest centre is 141.42 m away, its segment's centroid is at (500050, 4500050), and the smallest circle centred there that holds both points has a radius of 70.71 m. |
| `exercise_4_complex_feature_aggregation_and_ar/exercise/` | `01_feature_aggregation.py` | Aggregates three fragmented land-cover patches into one feature with `union_all()`: two 100-unit squares that overlap in a 25-unit square merge into a 175-unit blob, and the isolated 100-unit patch 200 units away keeps its own ring. |
| `exercise_5_interactive_challenge_the_optimal/exercise/` | `01_geofence_design.py` | Combines three proximity rules into one monitored boundary: a 50 m security buffer around a 50 000 m² six-sided building, plus a 20 m margin around each of two utility access points, merged with `union_all()`. |
| `interactive_challenge_the_optimal_geo_fence_d/exercise/` | `01_geofence_spec.py` | This folder holds the challenge, not its answer: a six-vertex building covering exactly 50 000 m², two utility access points at 400/150 and 50/450, and the two buffer distances the design must honour — 50 m around the building, 20 m around each point. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter4/run_offline.sh
```

`run_offline.sh` runs the 8 harnesses and prints one line per harness;
the log is written to `chapter4/output/run_4.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
