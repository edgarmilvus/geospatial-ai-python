# Chapter 12 — Band Math - Calculating NDVI (Vegetation Index) from Space

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `multi_field_ndvi_analysis_workflow/example/` | `multi_field_ndvi.py` | Simulates two agricultural scenes as real two-band GeoTIFFs (band 1 Red, band 2 NIR, uint16 digital numbers), reads them back, computes a masked NDVI, classifies it into four health bands, and writes one float32 index raster per field. |
| `calculating_ndvi_with_numpy/example/` | `ndvi_band_math.py` | Takes a 3×3 window of Red and Near-Infrared reflectance, computes the Normalized Difference Vegetation Index element-wise, and writes the result as a one-band float32 GeoTIFF in a projected CRS, so the arithmetic ends in a georeferenced product. |
| `exercise_1_isolating_the_arithmetic_core_calc/exercise/` | `ndvi_arithmetic_core.py` | Computes the numerator, the denominator and the index for a 5×5 patch of Red and NIR digital numbers, with no loop, no library beyond NumPy, and a printed denominator so a division by zero would be visible before it happened. |
| `exercise_2_geospatial_integration_reading_ban/exercise/` | `read_bands_rasterio.py` | Writes a four-band vendor-style GeoTIFF (Blue, Green, Red, NIR as uint16 digital numbers), opens it, reads only bands 3 and 4 as float32, and inspects the CRS and the affine transform the next exercise needs in order to write the product back. |
| `exercise_3_full_pipeline_execution_generating/exercise/` | `ndvi_geotiff_pipeline.py` | Generates a four-band scene with a patch of no signal, computes the index, rewrites the input profile for a single float32 band, and writes the index so it inherits the input's CRS, transform and grid. |
| `exercise_4_advanced_challenge_robustness_and/exercise/` | `robust_ndvi.py` | Builds a 256×256 scene with a 10×10 block of no signal, computes the index twice — once with `np.where` on a denominator mask, once with `errstate` plus `nan_to_num` — and writes the masked result with −9999 as its nodata value. |
| `exercise_5_interactive_challenge_translating/exercise/` | `classify_ndvi.py` | Thresholds a 100×100 index map into four integer classes with `np.select`, counts the pixels in each with `np.unique(..., return_counts=True)`, prints an interpretation drawn from the counts, and writes the class map as a single-byte GeoTIFF. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter12/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter12/output/run_12.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
