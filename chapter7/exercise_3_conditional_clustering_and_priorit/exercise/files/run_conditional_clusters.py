"""Harness for exercise 3 — a cluster that turns red when it hides a Priority 1.

The conditional logic runs in the browser, so the harness cannot execute it. What it
can do is check the contract the logic depends on: the JavaScript is attached to the
cluster group, it looks for the exact popup text the Python side writes, the CSS
class it switches to is defined, and the data behind it really does contain the
Priority 1 points the function searches for.
"""
import contextlib
import io
import pathlib
import sys
import traceback

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402
import maphtml  # noqa: E402

NAME = "exercise 3 (conditional clusters)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "conditional_cluster_icons.py", "cluster_icons")
    printed = log.getvalue()

    frame = module.df
    h.equal(len(frame), 500, "five hundred defects are simulated")
    h.equal(sorted(frame["Priority"].unique().tolist()), [1, 2, 3],
            "the three priority values all occur")
    counts = frame["Priority"].value_counts().to_dict()
    h.equal(counts[1], 29, "twenty-nine defects are Priority 1 on this seed")
    # The exercise asks for roughly 5%; 29/500 is 5.8%, which the p=[0.05, ...] draw
    # produces once the seed is fixed.
    h.check(0.02 <= counts[1] / len(frame) <= 0.10,
            "Priority 1 is a small minority, near the 5% the exercise asks for")

    saved = FILES.parent / "output" / "exercise3_conditional_clustering.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 34.0, "the map opens over the simulated grid")
        h.close(centre[1], -118.4, "the map opens over the simulated grid")
    h.equal(maphtml.zoom(text), 10, "the map opens at zoom 10")

    h.equal(maphtml.count(text, "L.marker("), 500, "every defect becomes a marker")
    h.equal(maphtml.count(text, "Defect ID: "), 500,
            "every marker keeps its own popup inside the cluster")

    # The cluster group and the hook that decides its icon.
    h.contains(text, "L.markerClusterGroup(", "the markers live in a cluster group")
    h.contains(text, "options.iconCreateFunction =", "a custom icon factory is attached")
    h.contains(text, "cluster.getAllChildMarkers()",
               "the factory inspects the markers inside the cluster")
    h.contains(text, "includes('Priority: 1')",
               "it looks for the exact text the Python side writes into the popup")
    h.contains(text, "c += 'critical'",
               "a cluster holding a Priority 1 switches to the critical class")
    h.contains(text, "L.Point(iconSize, iconSize)",
               "the critical cluster is also allowed to be larger")

    # The CSS the JavaScript relies on has to be in the same document.
    h.contains(text, ".marker-cluster-critical div", "the critical class is defined")
    h.contains(text, "#ff3333", "the critical cluster is painted red")

    # Popup integrity: one line per marker, with its own priority number.
    for priority in (1, 2, 3):
        h.equal(maphtml.count(text, "Priority: %d<" % priority), counts[priority],
                "Priority %d popups match the data" % priority)
    h.equal(maphtml.count(text, '"markerColor": "red"'), counts[1],
            "the Priority 1 markers are red even before clustering hides them")

    h.contains(printed, "exercise3_conditional_clustering.html",
               "the listing names the file it wrote")

    h.write_json("conditional_clusters.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "defects": len(frame),
        "priority_counts": {str(k): int(v) for k, v in counts.items()},
        "markers": maphtml.count(text, "L.marker("),
        "critical_css": "#ff3333",
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
