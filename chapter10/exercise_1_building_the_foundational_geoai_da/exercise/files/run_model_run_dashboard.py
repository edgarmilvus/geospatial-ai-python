"""Harness for exercise 1 — one dropdown, one map, one filter.

Checks the simulated frame, the layout the exercise asks for, and the callback's
behaviour for each model run: the figure must hold exactly the detections that
carry that run id, coloured by the three classes. Also checks the empty-selection
branch, which the printed solution leaves commented out.
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
    h = Harness("exercise 1 (model run dashboard)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "model_run_dashboard.py", "model_run_dashboard")
        module.build_and_report()
    printed = log.getvalue()

    data = module.data
    h.equal(len(data), 500, "the exercise simulates 500 detections")
    h.equal(sorted(data['model_run_id'].unique().tolist()),
            ['v1.0_2023', 'v1.1_2024', 'v1.2_2024'],
            "three model runs are present")
    h.equal(sorted(data['classification_label'].unique().tolist()),
            ['Forest', 'Urban', 'Water'], "three land-cover classes are present")
    h.check(data['confidence_score'].between(0.0, 1.0).all(),
            "every confidence score lies between 0 and 1")
    h.check(data['latitude'].between(34.0, 34.5).all(),
            "every latitude lies in the 34.0-34.5 band")
    h.check(data['longitude'].between(-118.5, -118.0).all(),
            "every longitude lies in the -118.5 to -118.0 band")

    counts = data['model_run_id'].value_counts()
    h.equal(int(counts['v1.0_2023']), 162, "162 detections belong to v1.0_2023")
    h.equal(int(counts['v1.1_2024']), 177, "177 detections belong to v1.1_2024")
    h.equal(int(counts['v1.2_2024']), 161, "161 detections belong to v1.2_2024")
    h.equal(int(counts.sum()), 500, "the three runs account for every detection")

    # Layout: the header, the control row and the graph, with the ids the
    # callback names.
    children = module.app.layout.children
    h.equal(len(children), 3, "the layout holds three top-level components")
    h.equal(children[0].children, "GeoAI Model Comparison Dashboard",
            "the header names the dashboard")
    dropdown = children[1].children[1]
    h.equal(dropdown.id, "model-run-selector", "the dropdown carries the required id")
    h.equal([option['value'] for option in dropdown.options],
            module.unique_model_ids.tolist(),
            "the dropdown is populated from the data, not from a literal")
    h.equal(dropdown.value, module.unique_model_ids[0],
            "the dropdown opens on the first run in the data")
    h.equal(dropdown.clearable, False, "the dropdown cannot be cleared")
    h.equal(children[2].id, "geoai-map-output", "the graph carries the required id")

    # One callback, and the figure it returns for each selection.
    h.equal(len(module.app.callback_map), 1, "a single callback is registered")
    for run_id, expected in counts.items():
        fig = module.update_map(run_id)
        expected_frame = data[data['model_run_id'] == run_id]
        plotted_lat = [value for trace in fig.data for value in trace.lat]
        h.equal(len(plotted_lat), int(expected),
                "the map for %s draws one point per detection" % run_id)
        h.equal(sorted(plotted_lat), sorted(expected_frame['latitude'].tolist()),
                "the map for %s takes its latitudes from the filtered frame" % run_id)
        h.equal(fig.layout.mapbox.style, "satellite-streets",
                "the map for %s keeps the satellite base" % run_id)

    # The classes are separate traces, so colour is a property of the data.
    fig = module.update_map('v1.1_2024')
    h.equal(len(fig.data), 3, "the map splits the detections into three class traces")
    h.equal(sorted(trace.name for trace in fig.data), ['Forest', 'Urban', 'Water'],
            "the traces are named for the classes")

    # The None branch: no selection is an empty map, not a crash.
    empty = module.update_map(None)
    h.equal(sum(0 if trace.lat is None else len(trace.lat) for trace in empty.data), 0,
            "no selection returns a figure with no points")
    h.contains(empty.layout.title.text, "Select a model run",
               "the empty map says what to do")

    # What the run wrote.
    summary = json.loads(
        (module.OUTPUT_DIR / "model_run_summary.json").read_text(encoding="utf-8"))
    h.equal(summary["rows_per_model_run"]["v1.1_2024"], 177,
            "the summary records v1.1_2024's 177 rows")
    h.equal(summary["labels"], ['Forest', 'Urban', 'Water'],
            "the summary records the three classes")
    h.check((module.OUTPUT_DIR / "dashboard_layout.json").exists(),
            "the run writes the layout JSON")
    h.contains(printed, "v1.0_2023: 162 detections",
               "the listing prints the per-run counts")

    h.write_json("model_run_dashboard.json", {
        "rows": len(data),
        "rows_per_model_run": {str(k): int(v) for k, v in counts.items()},
        "labels": sorted(data['classification_label'].unique().tolist()),
        "default_model_run": str(module.unique_model_ids[0]),
        "traces_for_default": [trace.name for trace in module.update_map(
            module.unique_model_ids[0]).data],
        "mean_confidence": round(float(data['confidence_score'].mean()), 4),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (model run dashboard)", FILES).crash())
