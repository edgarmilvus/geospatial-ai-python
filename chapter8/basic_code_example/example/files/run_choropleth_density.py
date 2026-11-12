"""Harness for the chapter's basic example — merge, then colour by the column.

The example makes four claims a choropleth can be wrong about: every boundary survives
the left join, the density column is numeric, the ramp spans the column's own min and
max, and each polygon's fill is its value on that ramp. The harness checks all four on
the figure the listing left in memory, then that the PNG on disk is a PNG.
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

NAME = "example 1 (basic choropleth)"


def luminance(rgba):
    """Relative perceptual lightness of an RGBA tuple, 0 (black) to 1 (white)."""
    red, green, blue = rgba[:3]
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "choropleth_density_by_region.py", "basic_choropleth")
    printed = log.getvalue()

    merged = module.merged_df

    # The join, not the plot: three boundaries in, three rows out, nothing dropped and
    # nothing duplicated.
    h.equal(len(merged), 3, "the left join keeps every one of the three regions")
    h.equal(merged["RegionID"].tolist(), ["A01", "B02", "C03"],
            "the regions keep their identifiers and their order")
    h.equal(int(merged["PopulationDensity"].isna().sum()), 0,
            "no region is left without a statistic")

    # Domain numbers: the densities are the table's, and the plane is 10x10, 10x10, 10x20.
    h.equal(merged.set_index("RegionID")["PopulationDensity"].to_dict(),
            {"A01": 150, "B02": 450, "C03": 250},
            "the three densities arrive from the statistical table")
    h.equal(merged.set_index("RegionID")["VoterTurnout"].to_dict(),
            {"A01": 0.65, "B02": 0.78, "C03": 0.71},
            "the second statistic travels with the first")
    h.equal([int(area) for area in merged.geometry.area], [100, 100, 200],
            "areas are 10x10, 10x10 and 10x20 in the plane's own units")
    h.equal(merged["PopulationDensity"].dtype.kind, "i",
            "the colour column is integer, not an object column of strings")

    # The ramp. A choropleth maps value -> colour through the column's min and max, not
    # through an arbitrary 0-1 window.
    ramp = module.ax.collections[0]
    h.close(ramp.norm.vmin, 150.0, "the ramp starts at the column's minimum (150)")
    h.close(ramp.norm.vmax, 450.0, "the ramp ends at the column's maximum (450)")

    colours = ramp.get_facecolors()
    h.equal(len(colours), 3, "one fill colour per polygon")
    h.equal(len({tuple(colour) for colour in colours}), 3,
            "three different values produce three different colours")

    # Order on the ramp. 'plasma' runs dark -> light, so the densest region must be the
    # brightest and the sparsest the darkest: A01 < C03 < B02.
    brightness = [luminance(colour) for colour in colours]
    h.check(brightness[0] < brightness[2] < brightness[1],
            "fills follow the values: A01 %.3f < C03 %.3f < B02 %.3f"
            % (brightness[0], brightness[2], brightness[1]))
    h.check(brightness[1] - brightness[0] > 0.2,
            "the 150 -> 450 step is visible (%.3f of lightness)"
            % (brightness[1] - brightness[0]))

    # The figure itself.
    h.equal(module.ax.get_title(), "Basic Synthetic Choropleth Map: Population Density",
            "the title names the metric")
    h.check(not module.ax.axison, "the coordinate axes are switched off, as a map requires")
    h.check(len(module.fig.axes) > 1, "a colour bar axis is drawn beside the map")

    saved = FILES.parent / "output" / "basic_choropleth_density.png"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    payload = saved.read_bytes()
    h.check(payload.startswith(b"\x89PNG\r\n\x1a\n"), "the file is a PNG")
    h.check(len(payload) > 5000, "the PNG carries a drawn map (%d bytes)" % len(payload))

    h.contains(printed, "Rows: 3;", "the listing reports the join's row count")
    h.contains(printed, "Colour range: 150 to 450",
               "the listing reports the ramp it used")
    h.contains(printed, "0.00 of the ramp", "the listing places A01 at the bottom")
    h.contains(printed, "1.00 of the ramp", "and B02 at the top")
    h.contains(printed, "output/basic_choropleth_density.png",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("basic_choropleth.json", {
        "regions": merged["RegionID"].tolist(),
        "density": merged["PopulationDensity"].tolist(),
        "turnout": merged["VoterTurnout"].tolist(),
        "area_units": [int(area) for area in merged.geometry.area],
        "ramp": [ramp.norm.vmin, ramp.norm.vmax],
        "brightness": [round(value, 4) for value in brightness],
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
