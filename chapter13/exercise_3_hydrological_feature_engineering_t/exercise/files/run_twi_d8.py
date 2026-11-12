"""Harness for exercise 3 — D8 flow accumulation and the wetness index.

The scene is a uniform hillslope draining east, which is the case where the answer is
known before the run: every cell in column j drains through j+1 cells, so the
specific catchment area is (j+1)*5 m and, with tan(beta) = 0.15, the index of a cell
in column j is ln((j+1)*5/0.15). The harness checks that identity, then the flat
ground floor, then a pit, which is the case D8 has to be told about.
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
    h = Harness("exercise 3 (TWI from D8)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "twi_d8.py", "twi_d8")
    printed = log.getvalue()

    import numpy as np
    import rasterio

    source = (FILES / "twi_d8.py").read_text(encoding="utf-8")
    h.check("import richdem" not in source,
            "flow routing is written out in D8 rather than imported from richDEM")

    dem = module.dem_data
    cell = module.CELL_SIZE
    accumulation = module.d8_flow_accumulation(dem, cell)
    receiver, gradient = module.d8_receivers(dem, cell)
    twi = module.topographic_wetness_index(dem, cell)

    h.equal(dem.shape, (128, 128), "the grid is 128x128")
    h.close(cell, 5.0, "the cell is 5 m")
    h.equal(accumulation.shape, dem.shape, "the accumulation grid matches the DEM")

    # --- the identity the plane makes checkable -----------------------------
    expected_acc = np.arange(1, 129)[None, :].repeat(128, axis=0)
    h.check(bool(np.array_equal(accumulation, expected_acc)),
            "column j drains through j+1 cells: 1 at the ridge, 128 at the outlet")
    h.equal(int(accumulation[:, 0].max()), 1, "the western edge is the ridge")
    h.equal(int(accumulation[:, -1].max()), 128, "the eastern edge is the outlet")

    # Every sink is on the eastern edge, and every other cell drains one column east.
    sinks = np.argwhere(receiver < 0)
    h.equal(len(sinks), 128, "only the eastern edge has sinks, one per row")
    h.check(bool(np.all(sinks[:, 1] == 127)), "every sink is in the last column")
    interior = receiver[:, :-1]
    expected_receiver = (np.arange(128)[:, None] * 128 + np.arange(1, 128)[None, :])
    h.check(bool(np.array_equal(interior, expected_receiver)),
            "every interior cell drains to the cell directly east of it")

    # tan(beta) = 0.15 on the whole slope, so the index of column j is ln((j+1)*5/0.15).
    h.close(float(np.median(gradient)), 0.15,
            "the gradient of a 0.15 m/m hillslope is 0.15", tol=1e-9)
    expected_twi = np.log(np.arange(1, 129)[None, :] * cell / 0.15).repeat(128, axis=0)
    h.check(bool(np.allclose(twi, expected_twi, atol=1e-9)),
            "TWI is ln(Ac * cell / tan(beta)) at every cell")
    h.close(float(twi[0, 0]), np.log(cell / 0.15), "the ridge cell reads 3.5066", tol=1e-9)
    h.close(float(twi[0, 127]), np.log(128 * cell / 0.15),
            "the outlet cell reads 8.3584", tol=1e-9)
    h.check(bool(np.all(np.diff(twi, axis=1) > 0)),
            "the index rises monotonically downslope, as converging flow requires")

    # --- flat ground: the slope floor is what keeps the logarithm finite -----
    flat = np.full((16, 16), 300.0)
    flat_acc = module.d8_flow_accumulation(flat, cell)
    h.check(bool(np.all(flat_acc == 1)),
            "on flat ground nothing drains anywhere: every cell accumulates itself")
    flat_twi = module.topographic_wetness_index(flat, cell)
    h.close(float(flat_twi[8, 8]), float(np.log(cell / module.MIN_TAN_BETA)),
            "the tan(beta) floor of 0.001 gives ln(5/0.001) = 8.5172, not an infinity",
            tol=1e-9)
    h.check(bool(np.all(np.isfinite(flat_twi))), "no cell of the flat DEM is infinite")

    # --- a pit: the case D8 has to be told about -----------------------------
    pit_dem = module.synthetic_dem(32, cell)
    pit_dem = pit_dem.copy()
    pit_dem[10, 10] -= 100.0
    pit_receiver, _ = module.d8_receivers(pit_dem, cell)
    h.equal(int(pit_receiver[10, 10]), -1, "a 100 m depression is a sink")
    pit_acc = module.d8_flow_accumulation(pit_dem, cell)
    donors = np.argwhere(pit_receiver == 10 * 32 + 10)
    h.check(len(donors) >= 1, "at least one neighbour drains into the pit")
    h.equal(int(pit_acc[10, 10]),
            1 + sum(int(pit_acc[r, c]) for r, c in donors),
            "the sink accumulates itself plus everything its donors accumulated")
    # Flow conservation: every cell of the grid ends in some sink, so the
    # accumulation of the sinks adds up to the number of cells.
    h.equal(int(pit_acc[pit_receiver < 0].sum()), 32 * 32,
            "the sinks' accumulation accounts for every cell of the grid")

    # --- the product ---------------------------------------------------------
    path = module.OUTPUT_FILE
    h.check(path.exists(), "the index is written to output/twi.tif")
    if path.exists():
        with rasterio.open(path) as src:
            h.equal(src.count, 1, "the index is one band")
            h.equal(src.dtypes[0], "float32", "the index is float32")
            h.equal(src.nodata, -9999.0, "the index declares its nodata value")
            h.equal((src.width, src.height), (128, 128), "the index keeps the DEM grid")
            h.equal(src.crs.to_epsg(), 32610, "the index carries a projected CRS")
            h.close(src.res[0], 5.0, "the index keeps the 5 m cell")
            band = src.read(1)
        h.check(bool(np.allclose(band, twi, atol=1e-5)),
                "the band on disk is the index that was computed")

    h.contains(printed, "Sinks (no lower neighbour): 128",
               "the sink count is reported")
    h.contains(printed, "Largest accumulation: 128 cells",
               "the largest accumulation is reported")
    h.contains(printed, "TWI Min: 3.51", "the index minimum is reported")
    h.contains(printed, "TWI Max: 8.36", "the index maximum is reported")
    h.contains(printed, "TWI Mean: 7.38", "the index mean is reported")

    h.write_json("twi_d8.json", {
        "grid": [128, 128],
        "cell_size_m": 5.0,
        "tan_beta": 0.15,
        "slope_degrees": float(np.degrees(np.arctan(0.15))),
        "min_tan_beta_floor": module.MIN_TAN_BETA,
        "accumulation": {"ridge": 1, "outlet": 128, "sinks": int(len(sinks))},
        "twi": {"min": float(twi.min()), "max": float(twi.max()),
                "mean": float(twi.mean()),
                "ridge_expected": float(np.log(cell / 0.15)),
                "outlet_expected": float(np.log(128 * cell / 0.15))},
        "flat_ground_twi": float(np.log(cell / module.MIN_TAN_BETA)),
        "pit_detected_at": [10, 10],
        "product": {"path": "output/twi.tif", "count": 1, "dtype": "float32",
                    "crs": "EPSG:32610", "cell_size_m": 5.0},
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (TWI from D8)", FILES).crash())
