"""Harness for exercise 2 — the histogram must ignore the slider the map obeys.

Calls the one multi-output callback with the default filters, then with a widened
slider and with a slider that matches nothing. The histogram's total must not move
when only the confidence changes; the map's must.
"""
import contextlib
import io
import json
import pathlib
import sys

import pandas as pd

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def mapped(fig):
    return sum(0 if trace.lat is None else len(trace.lat) for trace in fig.data)


def histogram_total(fig):
    """Rows behind a histogram: binned counts when Plotly supplies them, the raw
    sample otherwise (Plotly 6 lets the browser do the binning)."""
    total = 0
    for trace in fig.data:
        if trace.y is not None and len(trace.y):
            total += int(sum(trace.y))
        else:
            total += len(trace.x) if trace.x is not None else 0
    return int(total)


def main():
    h = Harness("exercise 2 (cross-filter dashboard)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "cross_filter_dashboard.py", "cross_filter")
        module.build_and_report()
    printed = log.getvalue()

    data = module.data_ex2
    h.equal(len(data), 1000, "one thousand detections are simulated")
    counts = data['model_run_id'].value_counts()
    h.equal(int(counts['v1.0_2023']), 321, "321 detections belong to v1.0_2023")
    h.equal(int(counts['v1.1_2024']), 335, "335 detections belong to v1.1_2024")
    h.equal(int(counts['v1.2_2024']), 344, "344 detections belong to v1.2_2024")
    labels = data['classification_label'].value_counts()
    h.equal(sorted(labels.index.tolist()), ['Forest', 'Road', 'Urban', 'Water'],
            "four classes are present")
    h.equal(int(labels['Water']), 231, "231 detections are Water")
    h.equal(str(module.min_date.date()), "2024-01-01", "the window starts on 1 January 2024")
    h.equal(str(module.max_date.date()), "2024-01-30", "the window ends on 30 January 2024")

    # Layout: three controls on the first row, two graphs on the second.
    children = module.app.layout.children
    h.equal(len(children), 3, "the layout has a header and two rows")
    controls = children[1].children
    h.equal(controls[0].children[1].id, "model-run-selector", "the dropdown is the model control")
    h.equal(controls[1].children[1].id, "confidence-slider", "the range slider is present")
    h.equal(controls[1].children[1].value, [0.7, 1.0],
            "the slider opens on the 0.7-1.0 band")
    h.equal(controls[2].children[1].id, "date-range-picker", "the date picker is present")
    graphs = children[2].children
    h.equal(graphs[0].id, "geoai-map-output", "the left graph is the map")
    h.equal(graphs[1].id, "confidence-histogram", "the right graph is the histogram")
    h.equal(len(module.app.callback_map), 1, "one callback drives both outputs")

    run = module.unique_model_ids[0]
    h.equal(str(run), "v1.2_2024", "the dashboard opens on v1.2_2024")

    # The default view: histogram over the whole run, map over the high band.
    map_fig, hist_fig = module.update_outputs(
        run, [0.7, 1.0], module.min_date, module.max_date)
    in_run = data[data['model_run_id'] == run]
    expected_map_default = in_run[in_run['confidence_score'].between(0.7, 1.0)]
    h.equal(histogram_total(hist_fig), len(in_run),
            "the histogram counts every detection of the selected run")
    h.equal(mapped(map_fig), len(expected_map_default),
            "the map counts only the detections inside the confidence band")
    h.equal(mapped(map_fig), 115, "the default band leaves 115 of 344 detections")
    h.equal(len(map_fig.data), 4, "the map splits the band into four class traces")

    # Widening the slider moves the map and leaves the histogram where it was.
    wide_map, wide_hist = module.update_outputs(
        run, [0.0, 1.0], module.min_date, module.max_date)
    h.equal(mapped(wide_map), len(in_run),
            "a full confidence band puts every detection on the map")
    h.equal(histogram_total(wide_hist), len(in_run),
            "the histogram is unchanged by the confidence slider")
    h.equal(sorted(trace.name for trace in wide_map.data),
            ['Forest', 'Road', 'Urban', 'Water'],
            "the map colours every class once the band is opened")

    # A band that matches nothing empties the map but not the histogram.
    empty_map, empty_hist = module.update_outputs(
        run, [1.0, 1.0], module.min_date, module.max_date)
    h.equal(mapped(empty_map), 0, "a 1.0-1.0 band selects no detection")
    h.contains(empty_map.layout.title.text, "No data matching all criteria",
               "the empty map says why it is empty")
    h.equal(histogram_total(empty_hist), len(in_run),
            "the histogram still shows the full population behind the empty map")

    # Narrowing the date window shrinks both, because both use the dates.
    narrow_start = pd.Timestamp("2024-01-01")
    narrow_end = pd.Timestamp("2024-01-07")
    narrow_map, narrow_hist = module.update_outputs(
        run, [0.0, 1.0], narrow_start, narrow_end)
    in_week = in_run[in_run['acquisition_date'].between(narrow_start, narrow_end)]
    h.equal(histogram_total(narrow_hist), len(in_week),
            "the histogram follows the date picker")
    h.equal(mapped(narrow_map), len(in_week),
            "the map follows the date picker as well")
    h.check(len(in_week) < len(in_run), "the first week is a strict subset of the run")

    # What the run wrote.
    summary = json.loads(
        (module.OUTPUT_DIR / "cross_filter_summary.json").read_text(encoding="utf-8"))
    h.equal(summary["histogram_rows"], 344, "the summary records 344 histogram rows")
    h.equal(summary["map_rows_at_default_slider"], 115,
            "the summary records 115 map rows at the default slider")
    h.contains(printed, "map 115 rows at confidence 0.7-1.0",
               "the listing prints the default split")

    h.write_json("cross_filter.json", {
        "rows": len(data),
        "rows_per_model_run": {str(k): int(v) for k, v in counts.items()},
        "labels": {str(k): int(v) for k, v in labels.items()},
        "window": [str(module.min_date.date()), str(module.max_date.date())],
        "default_run": str(run),
        "histogram_rows": histogram_total(hist_fig),
        "map_rows_default": mapped(map_fig),
        "map_rows_full_band": mapped(wide_map),
        "first_week_rows": len(in_week),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (cross-filter dashboard)", FILES).crash())
