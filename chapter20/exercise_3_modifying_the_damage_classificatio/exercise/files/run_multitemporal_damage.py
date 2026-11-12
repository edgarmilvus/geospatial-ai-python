"""Harness for chapter 20, exercise 3 — two dates, two signals, three verdicts.

The scenes are written by the listing, so their NDVI values are known exactly: the
pre-disaster window is 0.600, the damaged half of the post-disaster scene is -0.304
and the intact half is 0.500. That makes every assertion here arithmetic rather than
a comparison against whatever the run happened to print.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 3 (multi-temporal damage)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_multitemporal_damage.py",
                              "multitemporal_damage")
        module.main()
    printed = log.getvalue()

    import rasterio

    agent = module.DamageClassificationAgent()

    # --- the scenes ---
    with rasterio.open(module.PRE_RASTER) as source:
        h.equal(source.count, 4, "each scene carries the four bands the NDVI proxy needs")
        h.equal(source.crs.to_epsg(), 32611, "the scenes are in the AOI's metric CRS")
        h.equal(source.res, (10.0, 10.0), "ten-metre pixels, so an area is a count of metres")
        h.equal(source.width, 32, "the scene is 32 pixels wide")
    h.check(module.POST_RASTER.exists(), "both scenes exist on disk")

    # --- the spectral measurement ---
    damaged_window = module.building_footprint(4, 6)
    intact_window = module.building_footprint(22, 6)
    pre_ndvi = agent.calculate_ndvi_proxy(str(module.PRE_RASTER), damaged_window)
    post_ndvi = agent.calculate_ndvi_proxy(str(module.POST_RASTER), damaged_window)
    intact_post = agent.calculate_ndvi_proxy(str(module.POST_RASTER), intact_window)

    h.close(pre_ndvi, 0.6, tol=1e-6, message="the pre-disaster NDVI is (200-50)/250 = 0.600")
    h.close(post_ndvi, -0.3043, tol=1e-3, message="the rubble window is (80-150)/230")
    h.close(intact_post, 0.5, tol=1e-6, message="the intact window is (180-60)/240 = 0.500")
    h.check(post_ndvi < pre_ndvi, "the damaged window lost its vegetation signal")
    h.close(abs(pre_ndvi - post_ndvi), 0.904, tol=1e-3,
            message="the NDVI change in the damaged window is 0.904")
    h.close(abs(pre_ndvi - intact_post), 0.1, tol=1e-6,
            message="the NDVI change in the intact window is 0.100")

    # --- the structural measure ---
    h.close(agent.calculate_structural_loss(100.0, 60.0), 0.40,
            message="losing 40 of 100 square metres is 40% structural loss")
    h.close(agent.calculate_structural_loss(100.0, 15.0), 0.85,
            message="a collapsed footprint keeps 15% of its area")
    h.close(agent.calculate_structural_loss(0.0, 0.0), 0.0,
            message="a zero pre-area is handled instead of dividing by zero")

    # --- the three verdicts ---
    results = []
    for _label, column, row, pre_area, post_area in module.SCENARIOS:
        footprint = module.building_footprint(column, row)
        footprint["properties"] = {"id": f"c{column}r{row}"}
        results.append(agent.classify_damage(str(module.PRE_RASTER), str(module.POST_RASTER),
                                             footprint, pre_area, post_area)["properties"])

    h.equal(results[0]["damage_class"], "Major Damage",
            "40% loss with a 0.904 spectral change is Major Damage, not moderate")
    h.equal(results[1]["damage_class"], "Moderate Damage",
            "the same 40% loss with a 0.100 change stays Moderate Damage")
    h.equal(results[2]["damage_class"], "Destroyed",
            "85% loss is Destroyed whatever the spectrum says")
    h.equal(results[0]["structural_loss_pct"], results[1]["structural_loss_pct"],
            "scenarios A and B really do have the same structural loss")
    h.check(results[0]["ndvi_change_magnitude"] > 0.4 > results[1]["ndvi_change_magnitude"],
            "the spectral term is what separates them")

    # --- geometry is honoured, not ignored ---
    h.check(abs(pre_ndvi - intact_post) > 0.09,
            "different windows return different values: the geometry is read")
    empty = {"type": "Polygon", "coordinates": [[[0.0, 0.0], [1.0, 0.0],
                                                 [1.0, 1.0], [0.0, 0.0]]]}
    h.close(agent.calculate_ndvi_proxy(str(module.PRE_RASTER), empty), 0.0,
            message="a window outside the raster returns 0.0 instead of raising")

    # --- what the reader sees ---
    h.contains(printed, "NDVI change:         0.904", "the run prints the spectral change")
    h.contains(printed, "Final classification: Major Damage", "the run prints the verdict")
    h.contains(printed, "Structural loss:     40.00%", "the run prints the structural loss")

    artefact = module.OUTPUT_DIR / "multitemporal_results.txt"
    h.check(artefact.exists(), "the run wrote its small results file")

    h.write_json("multitemporal_damage.json", {
        "pre_ndvi": round(pre_ndvi, 6),
        "post_ndvi_damaged": round(post_ndvi, 6),
        "post_ndvi_intact": round(intact_post, 6),
        "ndvi_change_damaged": round(abs(pre_ndvi - post_ndvi), 6),
        "ndvi_change_intact": round(abs(pre_ndvi - intact_post), 6),
        "classes": [row["damage_class"] for row in results],
        "structural_loss": [row["structural_loss_pct"] for row in results],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (multi-temporal damage)", FILES).crash())
