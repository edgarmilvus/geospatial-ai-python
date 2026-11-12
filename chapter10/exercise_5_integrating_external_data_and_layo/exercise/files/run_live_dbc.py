"""Harness for exercise 5 — the live store, the interval and the 12-column grid.

Three things are checked that a screenshot cannot show: cycle 1 really produces a
new payload (and a timestamp one minute later), the filtering callback has the
live store as an Input so a refresh re-filters, and the DBC columns carry the
xs/lg split the exercise asks for.
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


def mapped(fig):
    return sum(0 if trace.lat is None else len(trace.lat) for trace in fig.data)


def histogram_total(fig):
    total = 0
    for trace in fig.data:
        if trace.y is not None and len(trace.y):
            total += int(sum(trace.y))
        else:
            total += len(trace.x) if trace.x is not None else 0
    return int(total)


def main():
    h = Harness("exercise 5 (live DBC dashboard)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "live_dbc_dashboard.py", "live_dbc")
        module.build_and_report()
    printed = log.getvalue()

    initial = module.initial_df
    h.equal(len(initial), 500, "each refresh carries 500 detections")
    counts = initial['model_run_id'].value_counts()
    h.equal(int(counts['v_test']), 254, "cycle 0 has 254 v_test detections")
    h.equal(int(counts['v_prod']), 246, "cycle 0 has 246 v_prod detections")
    h.equal(str(initial['timestamp'].iloc[0]), "2024-06-01 12:00:00",
            "cycle 0 is stamped at noon")
    h.equal(sorted(initial['classification_label'].unique().tolist()),
            ['A', 'B', 'C', 'D'], "four classes are present")

    # The layout: two stores, the interval, the header, then two DBC rows.
    layout = module.app.layout
    h.equal(len(layout.children), 6, "the container holds six blocks")
    h.equal(layout.children[0].id, "live-raw-data-store", "the live store is first")
    h.equal(layout.children[1].id, "filtered-data-store", "the filtered store follows")
    interval = layout.children[2]
    h.equal(interval.id, "data-refresh-interval", "the interval has the required id")
    h.equal(interval.interval, 60000, "the interval fires every 60 seconds")
    h.equal(interval.n_intervals, 0, "the interval starts at zero")
    h.equal(layout.children[3].children, "Dynamic GeoAI Dashboard (DBC & Live Data)",
            "the header names the dashboard")
    h.equal(layout.fluid, True, "the container is fluid")

    row1, row2 = layout.children[4], layout.children[5]
    h.equal(len(row1.children), 2, "the first row holds the controls and the map")
    h.equal((row1.children[0].xs, row1.children[0].lg), (12, 3),
            "the control panel is full width on mobile and a quarter on desktop")
    h.equal((row1.children[1].xs, row1.children[1].lg), (12, 9),
            "the map takes the other three quarters on desktop")
    h.equal(row1.children[1].children.id, "geoai-map-output", "the wide column holds the map")
    h.equal(len(row2.children), 1, "the second row holds the histogram alone")
    h.equal(row2.children[0].xs, 12, "the histogram is full width")
    h.equal(row2.children[0].children.id, "confidence-histogram",
            "the second row holds the histogram")

    # The refresh: same shape, new numbers, one minute later.
    cycle0_data, cycle0_label = module.refresh_data(0)
    cycle1_data, cycle1_label = module.refresh_data(1)
    frame0 = module.deserialize_df(cycle0_data)
    frame1 = module.deserialize_df(cycle1_data)
    h.equal(len(frame0), 500, "cycle 0 serialises 500 rows")
    h.equal(len(frame1), 500, "cycle 1 keeps the row count")
    h.check(frame0['latitude'].iloc[0] != frame1['latitude'].iloc[0],
            "cycle 1 is a different draw, not the same frame relabelled")
    h.contains(cycle1_label, "2024-06-01 12:01:00",
               "cycle 1 is stamped one minute after cycle 0")
    h.contains(cycle1_label, "Interval 1", "the caption names the interval")
    h.equal(str(frame0['timestamp'].iloc[0]), "2024-06-01 12:00:00",
            "the rows carry the cycle's timestamp")

    # Wiring: refresh writes the live store, stage 1 takes it as an Input.
    h.equal(len(module.app.callback_map), 3, "the app registers three callbacks")
    refresh_key = [key for key in module.app.callback_map if 'live-raw-data-store' in key][0]
    refresh = module.app.callback_map[refresh_key]
    h.equal([item['id'] for item in refresh['inputs']], ['data-refresh-interval'],
            "the refresh callback reacts to the interval")
    stage1 = module.app.callback_map['filtered-data-store.data']
    h.equal([item['id'] for item in stage1['inputs']],
            ['model-run-selector', 'confidence-slider', 'live-raw-data-store'],
            "stage 1 re-filters whenever the live store changes")
    stage2_key = [key for key in module.app.callback_map if 'geoai-map-output' in key][0]
    h.equal([item['id'] for item in module.app.callback_map[stage2_key]['inputs']],
            ['filtered-data-store'], "stage 2 still reads only the filtered store")

    # The full chain on cycle 0.
    run = module.unique_model_ids[0]
    h.equal(str(run), "v_test", "the controls open on v_test")
    filtered_json = module.filter_data_and_store(run, [0.8, 1.0], cycle0_data)
    filtered = module.deserialize_df(filtered_json)
    h.equal(len(filtered), 62, "the default band keeps 62 of the 254 v_test rows")
    map_fig, hist_fig = module.render_visualizations(filtered_json)
    h.equal(mapped(map_fig), 62, "the map draws the 62 filtered detections")
    h.equal(histogram_total(hist_fig), 62, "the histogram counts the same 62 rows")
    h.equal(module.filter_data_and_store(run, [0.8, 1.0], None), None,
            "a missing store produces no filtered payload")

    waiting_map, _ = module.render_visualizations(None)
    h.contains(waiting_map.layout.title.text, "Waiting for data",
               "an empty store renders the waiting state")

    # What the run wrote.
    summary = json.loads(
        (module.OUTPUT_DIR / "live_dashboard_summary.json").read_text(encoding="utf-8"))
    h.equal(summary["timestamp"], "2024-06-01 12:00:00",
            "the summary records cycle 0's timestamp")
    h.equal(summary["filtered_rows_default"], 62,
            "the summary records the 62 filtered rows")
    h.equal(summary["grid"]["map"], {"xs": 12, "lg": 9},
            "the summary records the map's grid columns")
    h.contains(printed, "Grid: controls xs=12/lg=3, map xs=12/lg=9",
               "the listing prints the grid rules")

    h.write_json("live_dbc.json", {
        "rows_per_cycle": len(initial),
        "cycle_0": {"timestamp": str(initial['timestamp'].iloc[0]),
                    "counts": {str(k): int(v) for k, v in counts.items()}},
        "cycle_1": {"timestamp": str(frame1['timestamp'].iloc[0]),
                    "first_latitude": round(float(frame1['latitude'].iloc[0]), 6)},
        "interval_ms": interval.interval,
        "grid": {"controls": [12, 3], "map": [12, 9], "histogram": [12]},
        "filtered_rows_default": len(filtered),
        "callbacks": sorted(module.app.callback_map),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (live DBC dashboard)", FILES).crash())
