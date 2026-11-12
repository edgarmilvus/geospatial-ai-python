"""Harness for exercise 4 — two stages, one store in between.

The point of the exercise is the wiring, not the picture: stage 1 must take the
raw payload as `State` (so it is not re-sent on every keystroke) and stage 2 must
take nothing but the filtered store. The harness reads both callback specs from
`app.callback_map`, then calls the two functions in order and checks that the
figures carry exactly the rows the filter kept.
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
    h = Harness("exercise 4 (state-store dashboard)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "state_store_dashboard.py", "state_store")
        module.build_and_report()
    printed = log.getvalue()

    raw = module.large_data
    h.equal(len(raw), 100000, "one hundred thousand detections are simulated")
    counts = raw['model_run_id'].value_counts()
    h.equal(int(counts['v_prod']), 49993, "49 993 detections belong to v_prod")
    h.equal(int(counts['v_test']), 50007, "50 007 detections belong to v_test")
    h.equal(sorted(raw['classification_label'].unique().tolist()), ['A', 'B', 'C', 'D'],
            "four classes are present")
    h.check(len(module.INITIAL_RAW_DATA) > 5_000_000,
            "the serialised payload is several megabytes, not five rows")
    restored = module.deserialize_df(module.INITIAL_RAW_DATA)
    h.equal(len(restored), 100000, "the serialised payload round-trips every row")

    # The layout: two hidden stores, two controls, two graphs.
    children = module.app.layout.children
    h.equal(children[1].id, "raw-data-store", "the raw store is the first hidden component")
    h.equal(children[2].id, "filtered-data-store", "the filtered store is the second")
    h.equal(children[1].data, module.INITIAL_RAW_DATA,
            "the raw store is populated once at startup")
    controls = children[3].children
    h.equal(controls[0].children[1].id, "model-run-selector", "the dropdown is present")
    h.equal(controls[1].children[1].id, "confidence-slider", "the slider is present")
    graphs = children[4].children
    h.equal(graphs[0].id, "geoai-map-output", "the map is present")
    h.equal(graphs[1].id, "confidence-histogram", "the histogram is present")

    # Wiring: stage 1 takes the raw payload as State, stage 2 takes only the store.
    h.equal(len(module.app.callback_map), 2, "the app registers exactly two callbacks")
    stage1 = module.app.callback_map['filtered-data-store.data']
    h.equal([item['id'] for item in stage1['inputs']],
            ['model-run-selector', 'confidence-slider'],
            "stage 1 reacts to the two user controls")
    h.equal([item['id'] for item in stage1['state']], ['raw-data-store'],
            "stage 1 reads the raw data as State, never as an Input")
    stage2_key = [key for key in module.app.callback_map if 'geoai-map-output' in key][0]
    stage2 = module.app.callback_map[stage2_key]
    h.equal([item['id'] for item in stage2['inputs']], ['filtered-data-store'],
            "stage 2 takes nothing but the filtered store")
    h.equal(stage2['state'], [], "stage 2 reads no State and no control")

    # Run the two stages in order, as Dash would.
    run = module.unique_model_ids[0]
    h.equal(str(run), "v_prod", "the controls open on v_prod")
    filtered_json = module.filter_data_and_store(run, [0.8, 1.0], module.INITIAL_RAW_DATA)
    filtered = module.deserialize_df(filtered_json)
    expected = raw[(raw['model_run_id'] == run) &
                   (raw['confidence_score'].between(0.8, 1.0))]
    h.equal(len(filtered), len(expected), "stage 1 keeps the rows inside the band")
    h.equal(len(filtered), 10128, "the default filter keeps 10 128 of 100 000 rows")
    h.check(len(filtered) < len(raw), "the filtered payload is smaller than the raw one")

    map_fig, hist_fig = module.render_visualizations(filtered_json)
    h.equal(mapped(map_fig), len(expected), "stage 2 draws every filtered detection")
    h.equal(histogram_total(hist_fig), len(expected),
            "stage 2 histograms the same filtered rows")
    h.equal(len(map_fig.data), 4, "the filtered map keeps four class traces")

    # Widening the band moves stage 1 and both figures.
    wide_json = module.filter_data_and_store(run, [0.0, 1.0], module.INITIAL_RAW_DATA)
    wide_map, wide_hist = module.render_visualizations(wide_json)
    h.equal(mapped(wide_map), 49993, "a full band puts all 49 993 v_prod rows on the map")
    h.equal(histogram_total(wide_hist), 49993, "the histogram follows the wider band")
    h.check(len(wide_json) > len(filtered_json),
            "the wider band serialises to a larger payload")

    # The loading branch.
    loading_map, loading_hist = module.render_visualizations(None)
    h.equal(mapped(loading_map), 0, "a missing store renders an empty map")
    h.contains(loading_map.layout.title.text, "Loading",
               "the empty map says it is loading")

    # What the run wrote.
    summary = json.loads(
        (module.OUTPUT_DIR / "state_store_summary.json").read_text(encoding="utf-8"))
    h.equal(summary["raw_rows"], 100000, "the summary records the raw row count")
    h.equal(summary["filtered_rows_default"], 10128,
            "the summary records the filtered row count")
    h.equal(summary["raw_payload_bytes"], len(module.INITIAL_RAW_DATA),
            "the summary records the payload size")
    h.contains(printed, "keeps 10128 rows", "the listing prints the reduction")

    h.write_json("state_store.json", {
        "raw_rows": len(raw),
        "rows_per_model_run": {str(k): int(v) for k, v in counts.items()},
        "payload_bytes": len(module.INITIAL_RAW_DATA),
        "default_filtered_rows": len(filtered),
        "full_band_rows": mapped(wide_map),
        "stage1_inputs": [item['id'] for item in stage1['inputs']],
        "stage1_state": [item['id'] for item in stage1['state']],
        "stage2_inputs": [item['id'] for item in stage2['inputs']],
        "reduction_factor": round(len(raw) / len(filtered), 3),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (state-store dashboard)", FILES).crash())
