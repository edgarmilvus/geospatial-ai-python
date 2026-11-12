"""Harness for exercise 3 — the feed comes from the environment, the bandwidth from N.

Two things are checked, and both are behaviour rather than config: without
`GEOAI_DATA_PATH` the listing must fall back to a generated default and say so, and with it
set the listing must read that file instead. The second run is made with a 500-row fixture,
so `N` changes - and the bandwidth, which is a function of `N`, has to change with it.
"""
import contextlib
import io
import os
import pathlib
import sys
import traceback

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 3 (bandwidth from the environment)"

VARIABLE = "GEOAI_DATA_PATH"


def run(name):
    """Import the listing as `name` and return (module, printed output)."""
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "bandwidth_from_env.py", name)
    return module, log.getvalue()


def main():
    h = Harness(NAME, FILES)

    # Run 1: no variable in the environment.
    previous = os.environ.pop(VARIABLE, None)
    try:
        default, default_log = run("bandwidth_default")
    finally:
        if previous is not None:
            os.environ[VARIABLE] = previous

    h.equal(default.USING_DEFAULT, True, "with no variable set the listing uses the default")
    h.contains(default_log, f"WARNING: {VARIABLE} environment variable not set",
               "and warns before doing so")
    h.contains(default_log, "Using default path: output/default_traffic.csv",
               "naming the path it fell back to")
    h.check((FILES.parent / "output" / "default_traffic.csv").is_file(),
            "the default feed is a real file in the project, not a missing name")
    h.equal(default.N_valid, 8000, "the generated feed holds 8 000 valid pings")

    # The heuristic, recomputed. h = C * N^(-1/5) with C = 0.1.
    expected_default = 0.1 * 8000 ** (-1 / 5)
    h.check(abs(default.calculate_dynamic_bandwidth(8000) - expected_default) < 1e-12,
            "h = 0.1 * N^(-1/5) = %.6f for N = 8 000" % expected_default)
    h.check(abs(default.dynamic_h - expected_default) < 1e-12,
            "and that is the bandwidth the run used")
    h.equal(default.calculate_dynamic_bandwidth(1), 0.01,
            "a sample of one falls back to the documented 0.01 instead of dividing by zero")

    # Run 2: a fixture named in the environment, with 500 good rows and five bad ones.
    fixture = FILES.parent / "output" / "fixture_traffic.csv"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    rows = ["latitude,longitude,start_time"]
    for index in range(500):
        rows.append("%.6f,%.6f,2023-01-01 0%d:00:00"
                    % (34.05 + index * 1e-5, -118.24 + index * 1e-5, index % 10))
    # Five rows that must not survive: a zero latitude, a missing latitude, a zero
    # longitude, a latitude past the pole and a longitude past the antimeridian.
    rows += ["0.0,-118.24,2023-01-01 10:00:00",
             ",-118.24,2023-01-01 11:00:00",
             "34.05,0.0,2023-01-01 12:00:00",
             "91.0,-118.24,2023-01-01 13:00:00",
             "34.05,-181.0,2023-01-01 14:00:00"]
    fixture.write_text("\n".join(rows) + "\n", encoding="utf-8")

    os.environ[VARIABLE] = "output/fixture_traffic.csv"
    try:
        configured, configured_log = run("bandwidth_configured")
    finally:
        if previous is None:
            os.environ.pop(VARIABLE, None)
        else:
            os.environ[VARIABLE] = previous

    h.equal(configured.USING_DEFAULT, False, "with the variable set the default is not used")
    h.contains(configured_log,
               "Using data path from environment variable: output/fixture_traffic.csv",
               "the listing says which feed it read")
    h.check("WARNING" not in configured_log,
            "and warns about nothing when the variable is set")
    h.equal(configured.N_valid, 500,
            "the five bad rows are dropped and 500 valid pings remain")
    expected_configured = 0.1 * 500 ** (-1 / 5)
    h.check(abs(configured.dynamic_h - expected_configured) < 1e-12,
            "h = 0.1 * N^(-1/5) = %.6f for N = 500" % expected_configured)
    h.check(configured.dynamic_h > default.dynamic_h,
            "a smaller sample earns a wider bandwidth (%.4f > %.4f)"
            % (configured.dynamic_h, default.dynamic_h))

    # The bandwidth is not merely printed: it is what scipy was given, in its own units.
    factor = configured.dynamic_h / configured.spread
    h.contains(configured_log, "Bandwidth applied as bw_method: %.4f" % factor,
               "the factor printed is the bandwidth divided by the sample spread")
    h.check(configured.peak is not None, "the configured run evaluated a KDE surface")
    h.check(abs(configured.peak[0] - 34.05) < 0.01,
            "and its peak sits on the data (%.4f N)" % configured.peak[0])

    h.contains(configured_log, "Total valid data points (N): 500",
               "the run reports the count it used")
    h.contains(configured_log, "Final used file path: output/fixture_traffic.csv",
               "and the file it settled on")
    h.contains(configured_log, "Calculated Dynamic Bandwidth (h): 0.028",
               "and the bandwidth to six places")
    h.contains(configured_log, "KDE evaluated on a 120x120 grid",
               "the grid is reported too, so the cost is visible")
    h.check(str(pathlib.Path.home()) not in default_log + configured_log,
            "neither run prints a machine's home directory")

    h.write_json("bandwidth_env.json", {
        "variable": VARIABLE,
        "default": {
            "path": "output/default_traffic.csv",
            "points": default.N_valid,
            "bandwidth": round(default.dynamic_h, 6),
            "bw_method": round(default.dynamic_h / default.spread, 4),
            "peak": [round(value, 4) for value in default.peak],
        },
        "configured": {
            "path": "output/fixture_traffic.csv",
            "points": configured.N_valid,
            "bandwidth": round(configured.dynamic_h, 6),
            "bw_method": round(configured.dynamic_h / configured.spread, 4),
            "peak": [round(value, 4) for value in configured.peak],
        },
        "exponent": -1 / 5,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
