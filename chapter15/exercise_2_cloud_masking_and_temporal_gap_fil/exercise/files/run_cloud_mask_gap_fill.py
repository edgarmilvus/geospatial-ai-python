"""Harness for exercise 2 — masking clouds, then filling only the holes.

The promise of the exercise is narrow: contaminated observations become NaN, the
interpolation restores exactly those, and nothing else moves. The harness checks
all three on the one pixel the listing prints, and checks that the fill is linear
in *time* — the dates are six months apart but not equally long, so a fill that
averages the two neighbours evenly lands a day-weighting off.
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

NAME = "exercise 2 (cloud masking and gap filling)"
PIXEL = (50, 50)


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "02_cloud_mask_gap_fill.py", "cloud_mask")
    printed = log.getvalue()

    raw = module.ndvi_stack
    masked = module.masked_ndvi
    filled = module.interpolated_ndvi
    qa = module.qa_band_data

    # -- the mask --------------------------------------------------------
    contaminated = int(qa.sum())
    h.equal(contaminated, 5025, "5025 of the 50 000 observations are contaminated")
    h.check(0.09 <= contaminated / qa.size <= 0.11,
            "that is the one-in-ten the simulation asks for")
    h.equal(int(np.isnan(masked.values).sum()), contaminated,
            "every contaminated observation became NaN, and no other")
    h.equal(tuple(module.qa_band.dims), tuple(raw.dims),
            "the QA mask carries the same dimension names as the NDVI stack")
    h.equal(module.qa_band.shape, raw.shape,
            "and the same shape, so `.where` aligns without broadcasting")

    raw_ts = raw.sel(y=PIXEL[1], x=PIXEL[0]).values
    masked_ts = masked.sel(y=PIXEL[1], x=PIXEL[0]).values
    filled_ts = filled.sel(y=PIXEL[1], x=PIXEL[0]).values
    gaps = np.isnan(masked_ts)
    h.equal(gaps.tolist(), [False, True, False, True, False],
            "the two forced observations are the two that are masked")
    h.check(np.allclose(filled_ts[~gaps], raw_ts[~gaps]),
            "the clean observations come through untouched")

    # -- the fill --------------------------------------------------------
    h.equal(int(np.isnan(filled_ts).sum()), 0,
            "both interior gaps of the sampled pixel are filled")
    times = raw.time.values.astype("datetime64[D]").astype(float)
    first_weight = (times[1] - times[0]) / (times[2] - times[0])
    first_expected = raw_ts[0] + first_weight * (raw_ts[2] - raw_ts[0])
    h.close(filled_ts[1], first_expected,
            "the first gap is weighted by elapsed days, not by index position", tol=1e-9)

    weight = (times[3] - times[2]) / (times[4] - times[2])
    expected = raw_ts[2] + weight * (raw_ts[4] - raw_ts[2])
    h.close(filled_ts[3], expected,
            "the second gap is weighted by days, not by index position", tol=1e-9)
    h.check(abs(filled_ts[3] - (raw_ts[2] + raw_ts[4]) / 2) > 1e-4,
            "an even average of the neighbours would have been wrong by more than 0.001")
    h.check(first_weight != 0.5,
            "the first interval is not half the gap: six calendar months are 182 and 184 days")

    # -- the rest of the cube ---------------------------------------------
    still_missing = int(np.isnan(filled.values).sum())
    h.check(still_missing < contaminated,
            "interpolation fills the interior gaps (%d of %d remain, at the edges)"
            % (still_missing, contaminated))
    clean = ~np.isnan(masked.values)
    h.check(np.allclose(filled.values[clean], raw.values[clean]),
            "no clean observation was changed by the interpolation")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Contaminated observations: 5025 of 50000",
               "the listing reports the size of the mask")
    h.contains(printed, "Interpolated Time Series:", "the listing prints the filled series")
    h.check(printed.count("nan") >= 1, "the printed series shows the gap before filling")

    h.write_json("cloud_mask.json", {
        "observations": int(qa.size),
        "contaminated": contaminated,
        "contaminated_fraction": round(contaminated / qa.size, 4),
        "nan_after_masking": int(np.isnan(masked.values).sum()),
        "nan_after_interpolation": still_missing,
        "pixel": {"x": PIXEL[0], "y": PIXEL[1],
                  "raw": [round(float(value), 4) for value in raw_ts],
                  "masked": [None if np.isnan(value) else round(float(value), 4)
                             for value in masked_ts],
                  "filled": [round(float(value), 4) for value in filled_ts]},
        "time_weight_used": round(float(weight), 4),
        "first_time_weight": round(float(first_weight), 4),
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
