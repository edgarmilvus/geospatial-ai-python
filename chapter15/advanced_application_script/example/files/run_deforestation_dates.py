"""Harness for the advanced example — where and when the forest was lost.

The listing reports three numbers: pixels analysed, pixels affected and hectares.
The harness checks them against the event that was actually simulated — a 10 x 10
block losing its canopy from month 30 — and checks that the persistence filter is
what keeps the count near 100 instead of the 837 a single-month test returns.
"""
import contextlib
import io
import pathlib
import sys

import numpy as np

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "advanced example (deforestation date detection)"
BLOCK = (slice(10, 20), slice(10, 20))


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_deforestation_date_detection.py", "deforestation")
    printed = log.getvalue()

    dod = module.date_index_of_deforestation
    ndvi = module.ndvi_stack
    ds = module.sentinel_ds

    # -- the cube --------------------------------------------------------
    h.equal(module.TIME_STEPS, 60, "the four-year window holds sixty monthly observations")
    h.equal(dict(ds.sizes)["time"], 60, "the cube's time axis carries all sixty")
    h.equal((dict(ds.sizes)["y"], dict(ds.sizes)["x"]), (50, 50),
            "the scene is fifty by fifty pixels")
    h.equal(ds.rio.crs.to_string(), "EPSG:4326", "the cube carries its CRS")
    h.check(float(ndvi.min()) >= -1.0 and float(ndvi.max()) <= 1.0,
            "every NDVI value stays inside -1..1")

    # -- the event that was injected --------------------------------------
    healthy = float(ndvi.isel(time=slice(0, 24), y=0, x=0).mean())
    blocked = float(ndvi.isel(time=slice(30, 60), y=slice(10, 20), x=slice(10, 20)).mean())
    h.check(0.60 <= healthy <= 0.67, "an undisturbed pixel sits near NDVI 0.64 (%.3f)" % healthy)
    h.check(0.05 <= blocked <= 0.18,
            "the cleared block falls to near NDVI 0.11 (%.3f)" % blocked)
    h.check(healthy - blocked > 0.45, "the drop the z-score has to see is larger than 0.45")

    # -- the detection ----------------------------------------------------
    h.equal(dod.shape, (50, 50), "one date per pixel")
    inside = dod[BLOCK]
    h.equal(int((inside != -1).sum()), 100,
            "all one hundred pixels of the cleared block are flagged")
    h.check(set(np.unique(inside).tolist()) <= {29, 30},
            "the block is dated at the month the canopy disappears (29 or 30)")
    h.equal(int((inside == 30).sum()) >= 90, True,
            "at least ninety of the hundred are dated exactly at month 30")
    h.equal(int(dod[0, 0]), -1, "an untouched pixel is reported as no change")

    affected = int((dod != -1).sum())
    h.check(affected >= 100, "the block's hundred pixels are a floor on the count")
    h.check(affected <= 110,
            "at most ten further pixels are flagged, and they are noise (got %d)" % affected)
    h.close(module.TOTAL_AREA_HECTARES, affected * 100 / 10000,
            "hectares are the pixel count times 100 m2 over 10 000")
    h.check(1.0 <= module.TOTAL_AREA_HECTARES <= 1.10,
            "one hectare is the block, and the noise adds at most a tenth")

    dates = {module.get_date_from_index(index) for index in np.unique(inside)}
    h.check(dates <= {"2021-06-01", "2021-07-01"},
            "the block's dates are the month the drop begins (got %s)" % sorted(dates))
    h.equal(module.get_date_from_index(-1), "N/A (No Change)",
            "an unflagged pixel has no date to report")

    # -- the temporal filter earns its place ------------------------------
    single = module.detect_deforestation_date(ndvi, module.Z_THRESHOLD, 1, module.BASELINE_STEPS)
    h.check(int((single != -1).sum()) > affected,
            "requiring one month instead of three flags more pixels (%d vs %d)"
            % (int((single != -1).sum()), affected))

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Total Pixels Analyzed: 2500", "the report counts the scene")
    h.contains(printed, "Total Affected Pixels: %d" % affected, "the report counts the loss")
    h.contains(printed, "Total Deforested Area: %.2f Hectares" % module.TOTAL_AREA_HECTARES,
               "the report gives the area in hectares")
    h.contains(printed, "Baseline Window: 24 months", "the report names the baseline")

    h.write_json("deforestation_dates.json", {
        "time_steps": int(module.TIME_STEPS),
        "pixels": 2500,
        "affected_pixels": affected,
        "block_pixels_flagged": int((inside != -1).sum()),
        "block_dates": sorted(dates),
        "pixels_dated_month_30": int((inside == 30).sum()),
        "affected_with_persistence_1": int((single != -1).sum()),
        "area_hectares": round(float(module.TOTAL_AREA_HECTARES), 4),
        "earliest": module.earliest_dod,
        "latest": module.latest_dod,
        "healthy_ndvi": round(healthy, 4),
        "cleared_ndvi": round(blocked, 4),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
