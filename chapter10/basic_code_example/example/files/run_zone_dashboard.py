"""Harness for the basic Dash example — layout, callback and served payload.

The listing builds the application and writes its layout, then returns. The
harness imports it, checks the four components and the callback the chapter
describes, calls the callback directly for each zone (a callback is a plain
function once Dash has registered it), and finally serves the same app on an
ephemeral loopback port to read what a browser would receive: `/` and
`/_dash-layout`.
"""
import contextlib
import io
import json
import pathlib
import sys
import threading
import urllib.request

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def fetch(port, path):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=10) as reply:
        return reply.status, reply.read().decode("utf-8")


def serve_and_read(app):
    """Serve the app on port 0, read two routes, shut the server down."""
    from werkzeug.serving import WSGIRequestHandler, make_server

    class QuietHandler(WSGIRequestHandler):
        def log(self, kind, message, *args):
            pass  # the harness log is for verdicts, not access lines

    server = make_server("127.0.0.1", 0, app.server, request_handler=QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, index = fetch(server.server_port, "/")
        _, raw_layout = fetch(server.server_port, "/_dash-layout")
    finally:
        server.shutdown()
        thread.join(timeout=10)
    return status, index, raw_layout


def main():
    h = Harness("example 1 (Dash zone dashboard)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "geoai_zone_dashboard.py", "zone_dashboard")
        module.build_and_report()
    printed = log.getvalue()

    # The three zones and their metric: the data the map is built from.
    h.equal(len(module.df), 3, "three zones are simulated")
    h.equal(module.df['city'].tolist(), ['Zone A', 'Zone B', 'Zone C'],
            "the zones are named A, B and C")
    h.equal(module.df['value'].tolist(), [100, 250, 50],
            "the GeoAI metric is 100, 250 and 50")
    h.close(module.df['lat'].iloc[0], 34.05, "Zone A sits at 34.05 latitude")
    h.close(module.df['lon'].iloc[2], -118.35, "Zone C sits at -118.35 longitude")

    # The figure handed to the Graph component before any callback fires.
    trace = module.initial_fig.data[0]
    h.equal(len(trace.lat), 3, "the initial map draws three points")
    h.close(trace.lat[1], 34.10, "the second point is Zone B's latitude")
    h.equal(list(trace.marker.color), [100.0, 250.0, 50.0],
            "the marker colour is the metric itself")
    h.equal(module.initial_fig.layout.mapbox.style, "carto-positron",
            "the base map is carto-positron")
    h.equal(module.initial_fig.layout.mapbox.zoom, 10, "the map opens at zoom 10")

    # The layout tree: header, dropdown, graph, details panel, in that order.
    layout = module.app.layout
    h.equal(len(layout.children), 4, "the layout holds four components")
    h.equal(layout.children[0].children, "Minimal GeoAI Zone Dashboard",
            "the header names the dashboard")
    dropdown = layout.children[1]
    h.equal(dropdown.id, "zone-selector", "the dropdown has the callback's id")
    h.equal([option['value'] for option in dropdown.options],
            ['Zone A', 'Zone B', 'Zone C'], "the dropdown offers the three zones")
    h.equal(dropdown.value, "Zone A", "the dropdown opens on Zone A")
    h.equal(dropdown.clearable, False, "the dropdown cannot be cleared")
    h.equal(layout.children[2].id, "geo-map-output", "the map has its own id")
    h.equal(layout.children[3].id, "selection-details", "the text panel has its own id")

    # The callback, called directly for two zones: no HTTP, no server.
    h.equal(len(module.app.callback_map), 1, "exactly one callback is registered")
    details_b = module.update_details("Zone B")
    h.equal(details_b.to_plotly_json()["type"], "Pre",
            "the callback returns a Preformatted block")
    text_b = details_b.children
    h.contains(text_b, "Analysis Summary for Zone B", "the summary names the zone")
    h.contains(text_b, "Coordinates: (34.10, -118.30)", "the summary repeats the coordinates")
    h.contains(text_b, "Calculated GeoAI Metric Value: 250",
               "the summary carries Zone B's metric")
    text_c = module.update_details("Zone C").children
    h.contains(text_c, "Calculated GeoAI Metric Value: 50",
               "switching the dropdown changes the metric to Zone C's 50")

    # What the run wrote, and that the layout survives a JSON round trip.
    layout_path = module.OUTPUT_DIR / "dashboard_layout.json"
    h.check(layout_path.exists(), "the run writes dashboard_layout.json")
    written = json.loads(layout_path.read_text(encoding="utf-8"))
    h.equal(written["type"], "Div", "the saved layout is the root Div")
    h.contains(module.app.index_string, "{%app_entry%}",
               "the saved index keeps Dash's entry placeholder")
    h.contains(printed, "Layout children: 4", "the listing reports its four components")

    # The served page and the layout route a browser actually requests.
    status, index, raw_layout = serve_and_read(module.app)
    h.equal(status, 200, "the served index answers 200")
    h.contains(index, "dash-renderer", "the index loads Dash's renderer")
    served = json.loads(raw_layout)
    h.equal(served["props"]["children"][0]["props"]["children"],
            "Minimal GeoAI Zone Dashboard",
            "the served layout carries the header text")
    h.equal(served["props"]["children"][1]["props"]["id"], "zone-selector",
            "the served layout carries the dropdown")

    h.write_json("zone_dashboard.json", {
        "zones": module.df.to_dict(orient="records"),
        "callback_output": text_b.splitlines(),
        "layout_children": len(layout.children),
        "served_status": status,
        "mapbox_style": module.initial_fig.layout.mapbox.style,
        "zoom": module.initial_fig.layout.mapbox.zoom,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (Dash zone dashboard)", FILES).crash())
