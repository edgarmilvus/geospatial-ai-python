"""Harness for the advanced script — two fields, two scenes, two index rasters.

The script is a pipeline, so the checks follow the product: the two-band scenes on
disk, the masked division that survives the shadow patch, the index raster with its
nodata value, and the statistics a consultant would read. The field means are
domain numbers — healthy corn sits near 0.75, stressed wheat near 0.25 — and the
gap between them is what the classification is for.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 2 (multi-field NDVI)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "multi_field_ndvi.py", "multi_field_ndvi")
        results = module.main_ndvi_workflow()
    printed = log.getvalue()

    import numpy as np
    import rasterio

    by_field = {r["Field"]: r for r in results}
    h.equal(sorted(by_field), ["Field_A_Healthy_Corn", "Field_B_Stressed_Wheat"],
            "both fields are processed")
    healthy = by_field["Field_A_Healthy_Corn"]
    stressed = by_field["Field_B_Stressed_Wheat"]

    # --- the scenes on disk -------------------------------------------------
    for name in ("Field_A_Healthy_Corn", "Field_B_Stressed_Wheat"):
        scene = module.OUTPUT_DIR / f"{name}_scene.tif"
        h.check(scene.exists(), f"{name}: the two-band scene is written to output/")
        if not scene.exists():
            continue
        with rasterio.open(scene) as src:
            h.equal(src.count, 2, f"{name}: Red is band 1 and NIR is band 2")
            h.equal(src.dtypes[0], "uint16", f"{name}: the scene keeps vendor DN scaling")
            h.equal(src.shape, (96, 96), f"{name}: the scene is a 96x96 tile")
            h.close(src.res[0], 10.0, f"{name}: the scene has 10 m cells")
            h.equal(src.crs.to_epsg(), 32610, f"{name}: the scene is in UTM 10N")
            red = src.read(1)
            nir = src.read(2)
        # The shadow patch carries no signal in either band: denominator zero.
        h.check(int(red[0:6, 0:6].max()) == 0 and int(nir[0:6, 0:6].max()) == 0,
                f"{name}: the 6x6 shadow patch holds no signal in either band")

    # --- the masked division ------------------------------------------------
    red_a, nir_a, profile = module.read_bands(
        module.OUTPUT_DIR / "Field_A_Healthy_Corn_scene.tif")
    ndvi_a, valid_a = module.calculate_ndvi(nir_a, red_a)
    h.equal(str(ndvi_a.dtype), "float32", "the index is float32")
    h.equal(int(valid_a.sum()), 96 * 96 - 36,
            "the 36 shadow pixels are excluded by the denominator mask, the rest kept")
    h.check(not valid_a[0:6, 0:6].any(), "every shadow pixel is marked unusable")
    h.check(float(ndvi_a[valid_a].min()) >= -1.0 and float(ndvi_a[valid_a].max()) <= 1.0,
            "every valid index value is inside [-1, 1]")
    h.check(np.isfinite(ndvi_a).all(), "the masked division produces no NaN and no Inf")

    # One pixel worked out by hand from the raster itself.
    row, col = 48, 48
    expected = (float(nir_a[row, col]) - float(red_a[row, col])) / \
               (float(nir_a[row, col]) + float(red_a[row, col]))
    h.close(float(ndvi_a[row, col]), expected,
            "pixel (48,48) is (NIR-Red)/(NIR+Red) of the bands on disk", tol=1e-6)

    # --- the index raster ---------------------------------------------------
    ndvi_file = module.OUTPUT_DIR / "Field_A_Healthy_Corn_ndvi.tif"
    h.check(ndvi_file.exists(), "the index is written as its own GeoTIFF")
    if ndvi_file.exists():
        with rasterio.open(ndvi_file) as src:
            h.equal(src.count, 1, "the index raster is a single band")
            h.equal(src.dtypes[0], "float32", "the index raster stores float32")
            h.equal(src.nodata, -9999.0, "the index raster declares nodata -9999")
            h.equal(src.crs, profile["crs"], "the index raster inherits the scene CRS")
            h.equal(src.transform, profile["transform"],
                    "the index raster inherits the scene transform")
            band = src.read(1)
        h.check((band[0:6, 0:6] == -9999.0).all(),
                "the shadow patch is written as nodata, not as a zero index")
        h.equal(int((band == -9999.0).sum()), 36,
                "exactly the 36 shadow pixels carry the nodata marker")
        h.close(float(band[48, 48]), expected,
                "the pixel on disk is the index that was computed", tol=1e-6)

    # --- the statistics a consultant reads -----------------------------------
    # Healthy corn: NIR 0.55 against Red 0.08 gives an index near 0.75. Wheat under
    # stress: 0.25 against 0.15 gives roughly 0.25. The classification has to keep
    # them apart, and that gap is the point of the report.
    h.check(0.65 <= healthy["Mean_NDVI"] <= 0.85,
            "healthy corn mean NDVI is in the 0.65-0.85 band (got %.4f)"
            % healthy["Mean_NDVI"])
    h.check(0.15 <= stressed["Mean_NDVI"] <= 0.35,
            "stressed wheat mean NDVI is in the 0.15-0.35 band (got %.4f)"
            % stressed["Mean_NDVI"])
    h.check(healthy["Mean_NDVI"] - stressed["Mean_NDVI"] > 0.40,
            "the two fields are separated by more than 0.40 of index")
    h.check(healthy["Percent_Healthy"] > 90,
            "more than 90% of the corn field classifies as healthy")
    h.check(stressed["Percent_Healthy"] < 15,
            "less than 15% of the wheat field classifies as healthy")

    for field in (healthy, stressed):
        total = sum(field[f"Percent_{label}"] for label in module.NDVI_THRESHOLDS)
        h.close(total, 100.0, "%s: the four class percentages add up to 100"
                % field["Field"], tol=1e-9)
        count = sum(field[f"Pixels_{label}"] for label in module.NDVI_THRESHOLDS)
        h.equal(count, field["Valid_Pixels"],
                "%s: every valid pixel lands in exactly one class" % field["Field"])

    h.equal(healthy["Valid_Pixels"], 9180,
            "the corn scene has 9180 usable of 9216 pixels")

    # --- reproducibility ----------------------------------------------------
    # Replaying the seed alone must rebuild the scene on disk, byte for byte.
    rng = np.random.default_rng(module.SEED)
    red = module.simulate_band_data(0.08, rng)
    nir = module.simulate_band_data(0.55, rng)
    red[0:6, 0:6] = module.SCENE_NODATA
    nir[0:6, 0:6] = module.SCENE_NODATA
    h.check(np.array_equal(red, red_a) and np.array_equal(nir, nir_a),
            "the seed alone reproduces the scene on disk")

    # Strings last: what the reader sees.
    h.contains(printed, "SERIES SUMMARY REPORT: VEGETATION HEALTH INDEX",
               "the run ends on the comparative report")
    h.contains(printed, "[START PROCESSING] Field_A_Healthy_Corn",
               "each field announces itself")
    h.contains(printed, "Valid pixels: 9180 of 9216 (36 nodata)",
               "the nodata count is reported, not hidden")
    h.contains(printed, "Healthy Area Coverage: 99.34%",
               "the corn field's healthy coverage is reported")

    h.write_json("multi_field_ndvi.json", {
        "seed": module.SEED,
        "tile": list(module.TILE_SIZE),
        "cell_size_m": module.CELL_SIZE,
        "fields": {
            name: {
                "mean_ndvi": r["Mean_NDVI"],
                "valid_pixels": r["Valid_Pixels"],
                "nodata_pixels": 96 * 96 - r["Valid_Pixels"],
                "percent": {label: r[f"Percent_{label}"] for label in module.NDVI_THRESHOLDS},
            } for name, r in by_field.items()
        },
        "separation": healthy["Mean_NDVI"] - stressed["Mean_NDVI"],
        "index_raster": {"count": 1, "dtype": "float32", "nodata": -9999.0,
                         "crs": "EPSG:32610", "cell_size_m": 10.0},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (multi-field NDVI)", FILES).crash())
