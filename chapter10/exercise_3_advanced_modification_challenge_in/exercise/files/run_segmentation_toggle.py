"""Harness for exercise 3 — one graph, two data types, one toggle.

The claims to check: the point branch draws all 200 detections as three class
traces; the polygon branch draws only the 133 detections that carry a mask, as
three GeoJSON sources whose features are the row's own coordinates; and an empty
or doubled toggle falls back to points.
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
    h = Harness("exercise 3 (segmentation toggle)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "segmentation_toggle_dashboard.py", "segmentation_toggle")
        module.build_and_report()
    printed = log.getvalue()

    data = module.data_ex3
    h.equal(len(data), 200, "two hundred detections are simulated")
    polygons = data[data['segmentation_geojson'].notna()]
    h.equal(len(polygons), 133, "133 detections carry a segmentation mask")
    h.equal(int(data['segmentation_geojson'].isna().sum()), 67,
            "67 detections have no mask")
    by_type = polygons['object_type'].value_counts()
    h.equal(int(by_type['building']), 48, "48 masks are buildings")
    h.equal(int(by_type['road']), 46, "46 masks are roads")
    h.equal(int(by_type['water']), 39, "39 masks are water")
    h.equal(int(by_type.sum()), 133, "the three classes account for every mask")

    # A mask is drawn around its own detection, not around a second random point.
    first = polygons.iloc[0]
    feature = json.loads(first['segmentation_geojson'])
    ring = feature['geometry']['coordinates'][0]
    centre_lon = sum(point[0] for point in ring[:4]) / 4
    centre_lat = sum(point[1] for point in ring[:4]) / 4
    h.close(centre_lat, first['latitude'], "the first mask is centred on its row", tol=1e-9)
    h.close(centre_lon, first['longitude'], "the first mask is centred on its row", tol=1e-9)
    h.equal(len(ring), 5, "the polygon ring closes on its first point")

    # Layout: the checklist with its two modes and the one graph.
    children = module.app.layout.children
    h.equal(len(children), 3, "header, toggle row and graph")
    checklist = children[1].children[1]
    h.equal(checklist.id, "visualization-mode-toggle", "the checklist has the required id")
    h.equal([option['value'] for option in checklist.options], ['points', 'polygons'],
            "the checklist offers points and polygons")
    h.equal(checklist.value, ['points'], "the dashboard opens in point mode")
    h.equal(children[2].id, "geoai-map-output", "the graph keeps its id")

    # Point mode: three class traces covering every detection.
    points = module.update_map_mode(['points'])
    h.equal(len(points.data), 3, "point mode draws one trace per class")
    h.equal(sum(len(trace.lat) for trace in points.data), 200,
            "point mode draws every detection")
    h.equal(sorted(trace.name for trace in points.data), ['building', 'road', 'water'],
            "the traces are named for the object types")
    h.contains(points.layout.title.text, "Point Detections",
               "point mode labels itself as points")

    # Polygon mode: three GeoJSON layers holding the masks that exist.
    polygon_fig = module.update_map_mode(['polygons'])
    layers = polygon_fig.layout.mapbox.layers
    h.equal(len(layers), 3, "polygon mode adds one layer per object type")
    h.equal([layer.name for layer in layers], ['building', 'road', 'water'],
            "the layers are named for the object types")
    h.equal([layer.type for layer in layers], ['fill', 'fill', 'fill'],
            "every layer paints filled polygons")
    h.equal([len(layer.source['features']) for layer in layers], [48, 46, 39],
            "each layer holds the masks of its own class")
    h.equal(sum(len(layer.source['features']) for layer in layers), 133,
            "the layers together hold every mask")
    h.equal(layers[0].color, "rgba(255, 0, 0, 0.5)", "buildings stay red")
    h.equal(layers[2].color, "rgba(0, 0, 255, 0.5)", "water stays blue")
    h.equal(len(polygon_fig.data), 0, "polygon mode has no scatter traces")
    h.close(polygon_fig.layout.mapbox.center.lat, float(polygons['latitude'].mean()),
            "the view centres on the masks' mean latitude", tol=1e-9)
    h.equal(polygon_fig.layout.mapbox.style, "satellite-streets",
            "the polygon view keeps the satellite base")

    # The fallbacks the requirement asks for.
    empty_toggle = module.update_map_mode([])
    h.equal(sum(len(trace.lat) for trace in empty_toggle.data), 200,
            "an empty checklist falls back to points")
    both_toggle = module.update_map_mode(['points', 'polygons'])
    h.equal(sum(len(trace.lat) for trace in both_toggle.data), 200,
            "both boxes ticked falls back to points")
    neither_trace = module.update_map_mode(None)
    h.equal(sum(len(trace.lat) for trace in neither_trace.data), 200,
            "a missing value falls back to points")

    # What the run wrote.
    summary = json.loads(
        (module.OUTPUT_DIR / "segmentation_summary.json").read_text(encoding="utf-8"))
    h.equal(summary["with_segmentation"], 133, "the summary records the 133 masks")
    h.equal(summary["polygons_by_type"]["water"], 39, "the summary records 39 water masks")
    h.contains(printed, "with a mask: 133", "the listing prints the mask count")

    h.write_json("segmentation_toggle.json", {
        "rows": len(data),
        "with_segmentation": len(polygons),
        "polygons_by_type": {str(k): int(v) for k, v in by_type.items()},
        "layers": [{"name": layer.name,
                    "features": len(layer.source['features']),
                    "color": layer.color} for layer in layers],
        "center": {"lat": round(float(polygons['latitude'].mean()), 6),
                   "lon": round(float(polygons['longitude'].mean()), 6)},
        "point_traces": [trace.name for trace in points.data],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (segmentation toggle)", FILES).crash())
