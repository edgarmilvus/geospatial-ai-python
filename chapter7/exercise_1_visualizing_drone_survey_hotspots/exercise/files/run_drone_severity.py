"""Harness for exercise 1 — drone anomaly markers styled by severity.

The task is a mapping table from a category to a colour and an icon. The harness
checks the table covers every category that occurs, and then checks the map agrees
with the table, category by category, so a missing branch cannot pass unnoticed.
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

NAME = "exercise 1 (drone severity markers)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    # The listing warns about a colour folium does not ship; that is the exercise's
    # own choice, and the warning is not part of what is being checked.
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(io.StringIO()):
        module = load_listing(FILES / "drone_severity_markers.py", "drone_markers")
    printed = log.getvalue()

    frame = module.df
    h.equal(len(frame), 10, "the simulated survey holds ten points")
    h.equal(list(frame.columns), ["lat", "lon", "severity"],
            "each point carries a position and a severity")

    counts = frame["severity"].value_counts().to_dict()
    h.equal(counts, {"Critical": 2, "High": 2, "Medium": 3, "Low": 3},
            "the four severity levels appear in the counts the data defines")
    h.equal(sorted(module.severity_styles), ["Critical", "High", "Low", "Medium"],
            "the style table covers every level, including the ones added first")
    h.check(set(frame["severity"]) <= set(module.severity_styles),
            "no point falls through the lookup and gets no icon")

    for level, style in module.severity_styles.items():
        h.check(style["color"] and style["icon"],
                "%s maps to both a colour and an icon" % level)

    saved = FILES.parent / "output" / "exercise1_drone_hotspots.html"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 34.05, "the map opens over the simulated survey area")
        h.close(centre[1], -118.25, "the map opens over the simulated survey area")
    h.equal(maphtml.zoom(text), 13, "the map opens at zoom 13")

    h.equal(maphtml.count(text, "L.marker("), 10, "every point becomes a marker")
    for level, style in module.severity_styles.items():
        h.equal(maphtml.count(text, '"markerColor": "%s"' % style["color"]),
                counts[level],
                "the %s points are drawn in %s" % (level, style["color"]))
    # Two levels share the 'info' icon, so the icon is counted once per name, not
    # once per branch: 3 Medium + 3 Low = 6 markers behind the same glyph.
    per_icon = {}
    for level, style in module.severity_styles.items():
        per_icon[style["icon"]] = per_icon.get(style["icon"], 0) + counts[level]
    for icon, expected in per_icon.items():
        h.equal(maphtml.count(text, '"icon": "%s"' % icon), expected,
                "the %r icon appears on %d markers" % (icon, expected))
    h.equal(maphtml.count(text, '"markerColor": "red"'), 2,
            "the two Critical points are the red ones")
    h.contains(text, "Severity: Critical", "the popup names the severity in words")
    h.equal(maphtml.count(text, "Severity: "), 10, "every marker carries a popup")
    h.contains(printed, "exercise1_drone_hotspots.html",
               "the listing names the file it wrote")

    h.write_json("drone_markers.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "points": len(frame),
        "severity_counts": counts,
        "marker_colors": {level: style["color"]
                          for level, style in module.severity_styles.items()},
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
