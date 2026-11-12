"""Harness for the advanced application script — the GeoAI detection report map.

The script turns a confidence score into three things at once: an icon colour, a
status badge and a tooltip. The harness rebuilds the frame, counts the three bands,
and checks the same three bands in the document — so a styling rule that silently
stops matching shows up as a mismatch between the data and the map.
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

NAME = "example 2 (GeoAI detection map)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "geoai_detection_map.py", "geoai_detections")
        # The script guards its run, so the harness makes the call it makes.
        frame = module.generate_synthetic_detections(module.DUMP_SITES_COUNT)
        module.map_geoai_detections(frame)
    printed = log.getvalue()

    # The simulated detections: 50 sites, in a box around Los Angeles.
    h.equal(len(frame), 50, "fifty detections are simulated")
    h.equal(list(frame.columns),
            ["site_id", "latitude", "longitude", "confidence", "image_link"],
            "the frame carries the columns the popup needs")
    h.equal(frame["site_id"].iloc[0], "DS_001", "identifiers are numbered from one")
    h.check(frame["latitude"].between(34.0522 - 0.5, 34.0522 + 0.5).all(),
            "every latitude is within half a degree of the city centre")
    h.check(frame["longitude"].between(-118.2437 - 0.8, -118.2437 + 0.8).all(),
            "every longitude is within 0.8 degrees of the city centre")
    h.check(frame["confidence"].between(0.60, 0.99).all(),
            "every confidence is inside the simulated 60-99% band")

    # Deterministic: the same run twice is the same map.
    again = module.generate_synthetic_detections(module.DUMP_SITES_COUNT)
    h.check(frame.equals(again), "the seed makes two runs produce the same detections")

    high = int((frame["confidence"] >= 0.90).sum())
    medium = int(((frame["confidence"] >= 0.75) & (frame["confidence"] < 0.90)).sum())
    low = int((frame["confidence"] < 0.75).sum())
    h.equal(high + medium + low, 50, "the three confidence bands cover every site")
    h.equal(high, 13, "thirteen sites clear the 90% threshold on this seed")
    h.equal(medium, 14, "fourteen sites land in the review band")
    h.equal(low, 23, "twenty-three sites fall below 75%")

    # The popup builder, driven directly at the two bands' boundaries.
    border = frame.iloc[[0]].copy()
    for score, expected in ((0.90, "Confirmed High Priority"),
                            (0.899, "Review Required"),
                            (0.75, "Review Required"),
                            (0.749, "Low Confidence/Verify")):
        border.loc[border.index[0], "confidence"] = score
        h.contains(module.create_rich_popup_html(border.iloc[0]), expected,
                   "a confidence of %r is labelled %r" % (score, expected))

    saved = FILES.parent / "output" / "geoai_detection_map.html"
    h.check(saved.is_file(), "the script wrote %s" % saved.name)
    text, tags = maphtml.read(saved)
    h.check(maphtml.is_html(text, tags), "the file is a complete HTML document")

    centre = maphtml.centre(text)
    h.check(centre is not None, "the document declares a map centre")
    if centre:
        h.close(centre[0], 34.0522, "the map opens over Los Angeles")
        h.close(centre[1], -118.2437, "the map opens over Los Angeles")
    h.equal(maphtml.zoom(text), 10, "the map opens at zoom 10")

    # Clustering: one group, named, and it stops clustering when zoomed in.
    h.contains(text, "L.markerClusterGroup(", "the markers live in a cluster group")
    h.contains(text, '"disableClusteringAtZoom": 14',
               "clustering stops at zoom 14, as the options say")
    h.contains(text, '"GeoAI Detections"', "the cluster group is named for the control")
    h.contains(text, "L.control.layers(", "a layer control is added")

    h.equal(maphtml.count(text, "L.marker("), 50, "every detection gets a marker")
    h.equal(maphtml.count(text, '"markerColor": "darkgreen"'), high,
            "the high-confidence band is dark green")
    h.equal(maphtml.count(text, '"markerColor": "orange"'), medium,
            "the review band is orange")
    h.equal(maphtml.count(text, '"markerColor": "red"'), low,
            "the low-confidence band is red")

    # The rich popups: decoded out of their iframes, one per site.
    popups = maphtml.iframe_documents(text)
    h.equal(len(popups), 50, "every marker carries an iframe popup")
    h.check(all("GeoAI Detection: DS_" in popup for popup in popups),
            "each popup is headed by its own site identifier")
    h.equal(sum("Confirmed High Priority" in popup for popup in popups), high,
            "the same band count appears in the popup badges")
    h.contains(popups[0], "Review Satellite Snippet",
               "the popup links to the satellite snippet for review")
    h.contains(popups[0], "Confidence:", "the popup reports the confidence value")

    urls = maphtml.tile_urls(text)
    h.check(urls and "light_all" in urls[0],
            "the base map is the neutral CartoDB Positron layer")
    h.contains(printed, "output/geoai_detection_map.html",
               "the script names the file it wrote")

    h.write_json("geoai_detection_map.json", {
        "file": saved.name,
        "centre": list(centre) if centre else None,
        "zoom": maphtml.zoom(text),
        "sites": len(frame),
        "bands": {"high": high, "medium": medium, "low": low},
        "markers": maphtml.count(text, "L.marker("),
        "popups": len(popups),
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
