"""Harness for exercise 4 — the time-sensitive sensor filter.

The listing asks for a threshold, subtracts it from today, and paints what is older.
The harness drives the non-interactive branch (no terminal is attached when a suite
runs), then recomputes the cutoff itself and checks that the red markers are exactly
the sensors that fall behind it. Dates are taken from the run, never from the clock
of the machine reading this file.
"""
import contextlib
import io
import pathlib
import sys
import traceback
from datetime import timedelta

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402
import maphtml  # noqa: E402

NAME = "exercise 4 (sensor filter)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    # A suite has no terminal: the listing must take its documented default instead
    # of waiting for a keystroke.
    original_stdin = sys.stdin
    sys.stdin = io.StringIO("")
    try:
        with contextlib.redirect_stdout(log):
            module = load_listing(FILES / "sensor_inspection_filter.py", "sensor_filter")
    finally:
        sys.stdin = original_stdin
    printed = log.getvalue()

    h.equal(module.threshold_days, module.DEFAULT_THRESHOLD_DAYS,
            "with no terminal the threshold falls back to the default")
    h.contains(printed, "No terminal attached",
               "the listing says why it did not ask")
    h.equal(module.N_SENSORS, 15, "fifteen sensors are simulated")

    frame = module.df
    h.equal(len(frame), 15, "the frame holds every simulated sensor")
    h.equal(frame["sensor_id"].iloc[0], "S-001", "identifiers are numbered from one")
    h.equal(frame["last_inspection_date"].str.len().unique().tolist(), [10],
            "dates are stored as plain YYYY-MM-DD strings")

    # The arithmetic, recomputed here from the run's own clock.
    cutoff = module.current_date - timedelta(days=module.threshold_days)
    h.equal(module.cutoff_date, cutoff, "the cutoff is today minus the threshold")
    expected_overdue = int((frame["last_inspection_dt"] < cutoff).sum())
    h.equal(expected_overdue, 5,
            "five of the fifteen sensors fall behind a 30-day cutoff")
    h.check((frame["last_inspection_dt"] <= module.current_date).all(),
            "no inspection date is in the future")

    saved = FILES.parent / "output" / "exercise4_time_filter.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 34.05, "the map opens over the sensor field")
        h.close(centre[1], -118.25, "the map opens over the sensor field")
    h.equal(maphtml.zoom(text), 12, "the map opens at zoom 12")

    h.equal(maphtml.count(text, "L.marker("), 15,
            "every sensor gets a marker, overdue or not")
    h.equal(maphtml.count(text, '"markerColor": "red"'), expected_overdue,
            "exactly the overdue sensors are red")
    h.equal(maphtml.count(text, '"markerColor": "green"'), 15 - expected_overdue,
            "the rest are green")
    h.equal(maphtml.count(text, '"icon": "exclamation"'), expected_overdue,
            "the overdue sensors carry the exclamation icon")
    h.equal(maphtml.count(text, '"icon": "check"'), 15 - expected_overdue,
            "the current sensors carry the check icon")

    h.equal(maphtml.count(text, "STATUS: <b>OVERDUE</b>"), expected_overdue,
            "the popup states OVERDUE for the same count")
    h.equal(maphtml.count(text, "STATUS: <b>Current</b>"), 15 - expected_overdue,
            "the popup states Current for the rest")
    h.contains(text, "Last Inspected:", "the popup quotes the inspection date")
    h.contains(text, "SENSOR ID: S-001", "the popup identifies the sensor")

    h.contains(printed, f"Cutoff Date: {cutoff}", "the run reports the cutoff it used")
    h.contains(printed, "exercise4_time_filter.html", "the listing names the file it wrote")

    h.write_json("sensor_filter.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "sensors": len(frame),
        "threshold_days": module.threshold_days,
        "cutoff": str(cutoff),
        "overdue": expected_overdue,
        "current": 15 - expected_overdue,
        "interactive": False,
        "bytes": saved.stat().st_size,
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
