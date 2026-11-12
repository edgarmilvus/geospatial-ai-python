"""Harness for exercise 3 — two windows, one difference, one binary map.

The exercise is date arithmetic, so the dates are the assertions: the baseline
ends the day before the alert and reaches back 18 months, the monitoring window
starts on the alert and is asked for six months. The harness also checks the
consequence the listing does not print — the monitoring slice holds 61 observed
days, not 183, because the simulated record stops at the end of 2022.
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

NAME = "exercise 3 (baseline and monitoring windows)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "02_baseline_monitoring.py", "time_windows")
    printed = log.getvalue()

    b_start, b_end = module.b_start, module.b_end
    m_start, m_end = module.m_start, module.m_end
    stack = module.interpolated_ndvi_stack

    # -- the arithmetic ---------------------------------------------------
    h.equal(m_start.date().isoformat(), "2022-11-01", "monitoring starts on the alert date")
    h.equal(b_end.date().isoformat(), "2022-10-31", "the baseline ends the day before it")
    h.equal((m_start - b_end).days, 1, "the two windows are contiguous, not overlapping")
    h.equal(b_start.date().isoformat(), "2021-05-02",
            "eighteen months before the alert reaches back to May 2021")
    h.equal(m_end.date().isoformat(), "2023-05-02",
            "six months after the alert ends in May 2023")

    baseline_days = (b_end - b_start).days
    h.check(545 <= baseline_days <= 550,
            "the baseline spans the 547.9 days eighteen months averages to (got %d)"
            % baseline_days)
    monitoring_days = (m_end - m_start).days
    h.check(180 <= monitoring_days <= 185,
            "the monitoring window spans the 182.6 days six months averages to (got %d)"
            % monitoring_days)

    # -- the subsets ------------------------------------------------------
    baseline_subset = stack.sel(time=slice(b_start, b_end))
    monitoring_subset = stack.sel(time=slice(m_start, m_end))
    h.equal(len(baseline_subset.time), 548, "548 daily observations fall in the baseline")
    h.equal(len(monitoring_subset.time), 61,
            "only 61 fall in the monitoring window: the record ends on 2022-12-31")
    h.equal(str(stack.time.values[-1])[:10], "2022-12-31", "the record's last day")

    # -- the difference ---------------------------------------------------
    delta = module.delta_ndvi_map
    h.equal(delta.shape, (10, 10), "the difference map is one value per pixel")
    mean_delta = float(delta.mean())
    h.check(0.30 <= mean_delta <= 0.45,
            "the mean drop is a little over the 0.3 threshold (%.4f)" % mean_delta)
    h.check(float(delta.min()) > 0.3,
            "every pixel dropped by more than the threshold, so the map is saturated")

    flagged = module.binary_deforestation_map
    h.equal(flagged.dtype, np.dtype("bool"), "the threshold produces a boolean map")
    h.equal(tuple(flagged.dims), ("y", "x"), "the boolean map drops the time axis")
    h.equal(int(flagged.sum()), 100, "all one hundred pixels are flagged")
    h.equal(int((delta > 0.3).sum()), int(flagged.sum()),
            "the map is exactly the pixels above the threshold, with no extra rule")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Baseline: 2021-05-02 to 2022-10-31",
               "the listing prints the baseline it used")
    h.contains(printed, "Monitoring: 2022-11-01 to 2023-05-02",
               "the listing prints the monitoring window it used")
    h.contains(printed, "Number of Deforestation Pixels: 100",
               "the listing prints the pixel count the assertions check")

    h.write_json("time_windows.json", {
        "baseline": {"start": b_start.date().isoformat(), "end": b_end.date().isoformat(),
                     "days": baseline_days, "observations": int(len(baseline_subset.time))},
        "monitoring": {"start": m_start.date().isoformat(), "end": m_end.date().isoformat(),
                       "days": monitoring_days,
                       "observations": int(len(monitoring_subset.time))},
        "delta_mean": round(mean_delta, 4),
        "delta_min": round(float(delta.min()), 4),
        "delta_max": round(float(delta.max()), 4),
        "threshold": 0.3,
        "pixels_flagged": int(flagged.sum()),
        "pixels_total": int(flagged.size),
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
