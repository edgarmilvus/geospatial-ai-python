# Chapter 2 — The GeoDataFrame - Reading Shapefiles and GeoJSON

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script/example/` | `01_ingestion_validation.py` | Simulates the municipal case the chapter describes: legacy district boundaries as a Shapefile in EPSG:4326 and proposed infrastructure zones as a GeoJSON in EPSG:3857. |
| `basic_code_example/example/` | `01_ingest_shapefile_and_geojson.py` | Writes the same three European cities to an ESRI Shapefile and to a GeoJSON file under the project's `output/` folder, then reads both back through the same `gpd.read_file()` call and checks that the frame, the geometry column and the CRS survive. |
| `exercise_1/exercise/` | `01_parks_integrity_check.py` | Creates `city_parks.shp` (three Berlin parks in EPSG:25833, where one unit is one metre), reads it, and answers the four checks the exercise asks for: is the object a `GeoDataFrame`, what is the active geometry column called, what CRS does it carry, and what do the first five rows look like. |
| `exercise_2_cloud_native_ingestion_via_url_geo/exercise/` | `01_cloud_native_geojson.py` | Shows the call the exercise is about — `gpd.read_file(source)` — where `source` may be a path, an archive or a URL. |
| `exercise_3_performance_optimization_through_s/exercise/` | `01_selective_columns.py` | Writes a road layer with seven attributes, then reads it twice: once whole, and once with `columns=['segment_id', 'road_class']`. |
| `exercise_4_advanced_modification_challenge_pr/exercise/` | `01_async_task_list.py` | Writes four GeoJSON tiles under `output/tiles/`, then builds the read queue the exercise asks for: `[partial(load_single_tile, path) for path in file_paths]`. |
| `exercise_5_interactive_challenge_crs_assignme/exercise/` | `01_assign_crs.py` | Reads three boundary points, shows a frame with no CRS, assigns WGS 84 with `set_crs('EPSG:4326')` and proves the repair by reprojecting to Web Mercator. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter2/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter2/output/run_2.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
