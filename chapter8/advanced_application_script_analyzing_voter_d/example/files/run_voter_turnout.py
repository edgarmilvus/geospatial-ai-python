"""Harness for the advanced application script — two maps, two classification schemes.

The script's claim is statistical: twelve counties, turnout and one candidate's share,
the first cut by Jenks and the second by Quantiles, with the legend printing the breaks
that were computed rather than a second set chosen inside `.plot()`. The harness checks
the arithmetic that makes those numbers possible (turnout <= registration, votes <=
turnout), the shape of both classifications (five classes, breaks ascending, counts
summing to twelve), the class that straddles 50% on the diverging map, and only then the
figure on disk.
"""
import contextlib
import io
import pathlib
import re
import sys
import traceback

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "example 2 (voter turnout choropleth)"


def label_uppers(ax):
    """The upper edge of every class the legend prints, as floats."""
    if ax.get_legend() is None:
        return []
    uppers = []
    for text in ax.get_legend().get_texts():
        numbers = re.findall(r"-?\d+\.\d+", text.get_text())
        uppers.append(float(numbers[-1]))
    return uppers


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "voter_turnout_choropleth.py", "voter_choropleth")
    printed = log.getvalue()

    frame = module.merged_gdf

    # The join and the arithmetic the two maps rest on.
    h.equal(len(frame), 12, "twelve administrative units are mapped")
    h.equal(frame["County_ID"].nunique(), 12, "each unit appears once after the merge")
    h.equal(frame.crs.to_epsg(), 4326, "the boundaries are in WGS 84 for the web")
    h.equal(int(frame[["Turnout_Rate", "Candidate_A_Pct"]].isna().sum().sum()), 0,
            "no unit was dropped for a missing or infinite rate")
    h.check((frame["Actual_Turnout"] <= frame["Registered_Voters"]).all(),
            "turnout never exceeds registration")
    h.check((frame["Candidate_A_Votes"] <= frame["Actual_Turnout"]).all(),
            "one candidate never receives more votes than were cast")
    h.check((frame["Turnout_Rate"] > 0).all() and (frame["Turnout_Rate"] <= 100).all(),
            "every turnout rate is a percentage in (0, 100]")
    h.check((frame["Candidate_A_Pct"] > 0).all() and (frame["Candidate_A_Pct"] <= 100).all(),
            "every candidate share is a percentage in (0, 100]")

    # The defect the seeded generator would otherwise hide: `np.random.uniform(0.5, 0.7)`
    # without `size` multiplies the whole column by one constant, and every county gets
    # the same rate. Twelve identical counties are not a distribution.
    h.equal(frame["Turnout_Rate"].nunique(), 12,
            "all twelve turnout rates differ, so the draws were per row")
    h.check(frame["Turnout_Rate"].max() - frame["Turnout_Rate"].min() > 20,
            "turnout spans %.1f points, which is a map"
            % (frame["Turnout_Rate"].max() - frame["Turnout_Rate"].min()))

    # Jenks on turnout.
    turnout = module.turnout_classifier
    h.equal(turnout.k, 5, "Jenks is asked for five classes")
    h.equal(len(turnout.bins), 5, "a five-class scheme publishes five breaks")
    h.check(list(turnout.bins) == sorted(turnout.bins) and len(set(turnout.bins)) == 5,
            "the Jenks breaks strictly ascend")
    h.equal(int(sum(turnout.counts)), 12, "every county falls in exactly one Jenks class")
    h.check(turnout.bins[-1] >= frame["Turnout_Rate"].max() - 1e-9,
            "the top break covers the highest turnout")
    h.check(turnout.bins[0] > frame["Turnout_Rate"].min(),
            "the bottom break sits above the lowest turnout, so the first class is a range")
    h.check(min(turnout.counts) >= 1, "no Jenks class is empty")

    # Quantiles on the candidate's share.
    share = module.share_classifier
    h.equal(share.k, 5, "Quantiles is asked for five classes")
    h.check(int(sum(share.counts)) == 12, "every county falls in exactly one Quantile class")
    h.check(max(share.counts) - min(share.counts) <= 1,
            "Quantiles give equal counts: %s" % (share.counts,))

    # Map B is the diverging one, and k is odd so a middle class exists. The claim in
    # the listing is that this class is the one around 50% of the vote.
    h.equal(len(share.bins) % 2, 1, "an odd number of classes leaves a middle one")
    h.check(share.bins[2] < 50.0 < share.bins[3],
            "the middle class of map B straddles 50%% (%.2f to %.2f)"
            % (share.bins[2], share.bins[3]))

    # The legend is the map's own statement of its classes. It must print the breaks the
    # classifier found - the listing passes them as a UserDefined scheme for that reason.
    panel_a, panel_b = module.axes
    h.equal(len(panel_a.get_legend().get_texts()), 5, "map A prints five legend classes")
    h.equal(len(panel_b.get_legend().get_texts()), 5, "map B prints five legend classes")
    h.check([round(value, 2) for value in label_uppers(panel_a)]
            == [round(float(value), 2) for value in turnout.bins],
            "map A's legend edges are the Jenks breaks")
    h.check([round(value, 2) for value in label_uppers(panel_b)]
            == [round(float(value), 2) for value in share.bins],
            "map B's legend edges are the Quantile breaks")

    h.contains(panel_a.get_title(), "Jenks Natural Breaks", "map A names its scheme")
    h.contains(panel_b.get_title(), "Quantiles", "map B names its scheme")
    h.check(not panel_a.axison and not panel_b.axison, "both panels are maps, not charts")
    h.equal(len(panel_a.collections[0].get_facecolors()), 12,
            "one fill colour per county on map A")

    saved = FILES.parent / "output" / "voter_turnout_choropleth.png"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    payload = saved.read_bytes()
    h.check(payload.startswith(b"\x89PNG\r\n\x1a\n"), "the file is a PNG")
    h.check(len(payload) > 20_000, "the PNG carries two drawn maps (%d bytes)" % len(payload))

    h.contains(printed, "Counties per class: 2, 3, 3, 2, 2",
               "the listing reports the Jenks class counts")
    h.contains(printed, "Counties per class: 3, 2, 2, 2, 3",
               "the listing reports the Quantile class counts")
    h.contains(printed, "Loaded 12 administrative units", "the run reports what it loaded")
    h.contains(printed, "output/voter_turnout_choropleth.png",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("voter_turnout.json", {
        "units": len(frame),
        "turnout_range": [round(float(frame["Turnout_Rate"].min()), 2),
                          round(float(frame["Turnout_Rate"].max()), 2)],
        "share_range": [round(float(frame["Candidate_A_Pct"].min()), 2),
                        round(float(frame["Candidate_A_Pct"].max()), 2)],
        "jenks_breaks": [round(float(value), 2) for value in turnout.bins],
        "jenks_counts": [int(value) for value in turnout.counts],
        "quantile_breaks": [round(float(value), 2) for value in share.bins],
        "quantile_counts": [int(value) for value in share.counts],
        "legend_edges_a": [round(value, 2) for value in label_uppers(panel_a)],
        "legend_edges_b": [round(value, 2) for value in label_uppers(panel_b)],
        "png_bytes": len(payload),
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
