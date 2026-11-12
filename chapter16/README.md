# Chapter 16 — Deep Learning on Maps - Detecting Buildings with PyTorch

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `raster_to_vector_building_detection/example/` | `raster_to_vector_pipeline.py` | Runs a 512 x 512 ten-metre chip through a segmentation model, thresholds the probability map at 0.5, and turns the mask into five GeoJSON polygons whose rings are in UTM metres, carrying their area in m². |
| `simulating_and_visualizing_segmentation_data/example/` | `simulate_segmentation_pair.py` | Builds one 128 x 128 RGB patch and its 128 x 128 binary mask, paints the roof under the label it belongs to, then converts the pair to the tensors PyTorch expects: a 3 x 128 x 128 float image in [0, 1] and a 1 x 128 x 128 mask. |
| `exercise_1_optimized_data_pipeline_for_large/exercise/` | `tiled_dataset.py` | Indexes a 10 000 x 10 000 scene as 1 600 tiles of 256 pixels, reads only the window an index names, pads the last row and column back to full size, normalises with the scene's mean and deviation, and applies the same quarter turn to image and mask. |
| `exercise_2_modifying_u_net_for_enhanced_featu/exercise/` | `se_unet.py` | Implements a Squeeze-and-Excitation block — global average pool, 64 -> 4 -> 64, sigmoid, rescale — puts it between the bottleneck and the decoder of a small U-Net, and trains that U-Net for 60 full-batch steps on six synthetic 64 x 64 chips. |
| `exercise_3_advanced_evaluation_and_optimal_th/exercise/` | `threshold_optimization.py` | Scores one probability map at seventeen thresholds from 0.10 to 0.90, counting true and false positives by hand, and returns the threshold with the best F1. |
| `exercise_4_vectorization_and_attribute_assign/exercise/` | `raster_to_vector.py` | Writes a georeferenced one-metre mask with two footprints, vectorizes it with `rasterio.features.shapes`, and builds a GeoDataFrame carrying each polygon's area in m² and its centroid in projected metres, then writes that frame to a GeoPackage and reads it back to prove the CRS survived. |
| `exercise_5_geoai_agent_tooling_and_database_i/exercise/` | `building_database.py` | Defines the SQLAlchemy model the exercise asks for — id, area, centroid, WKT geometry — stores the vectorized buildings in SQLite as an agent tool, and answers the question the tool exists for: which building is largest. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter16/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter16/output/run_16.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
