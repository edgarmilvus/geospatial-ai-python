"""Harness for exercise 3 — (A OR B) AND C, and bins computed after the filter.

The exercise has two claims to check: the mask selects exactly the counties the logical
expression names, and the classification is built on the subset rather than on the whole
state. The harness recomputes both, and reads the two collections geopandas drew - the
state behind and the subset in front - to confirm that the excluded counties are still on
the map as context.
"""
import contextlib
import io
import pathlib
import sys
import traceback
import warnings

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")

NAME = "exercise 3 (coastal filter)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "coastal_vulnerability_filter.py", "coastal_filter")
    printed = log.getvalue()

    state = module.florida_gdf
    subset = module.vulnerable_coastal_counties
    pop = module.POP_THRESHOLD
    income = module.INCOME_THRESHOLD

    h.equal(len(state), 15, "fifteen counties are simulated")
    h.equal(pop, 500_000, "the population threshold is 500 000, as the exercise asks")
    h.equal(income, 45_000, "the income threshold is 45 000")
    h.equal(int((state["Population"] == 600_000).sum()), 1,
            "the forced high-population county is in the data")

    # The mask, rebuilt from its three named conditions.
    high = state["Population"] > pop
    low = state["MedianIncome"] < income
    coastal = state["IsCoastal"]
    rebuilt = (high | low) & coastal
    h.equal(int(rebuilt.sum()), int(module.final_mask.sum()),
            "the combined mask matches (A OR B) AND C")
    h.equal(int(rebuilt.sum()), 6, "six of the fifteen counties pass the filter")

    # No county is in the subset that does not satisfy the expression, and none that does
    # is missing from it.
    h.equal(sorted(subset["County"]), state[rebuilt]["County"].sort_values().tolist(),
            "the subset is exactly the counties the mask selects")
    h.check((subset["IsCoastal"]).all(), "every selected county is coastal")
    h.check(((subset["Population"] > pop) | (subset["MedianIncome"] < income)).all(),
            "every selected county is either populous or poor")

    # The two ways to fail: populous but inland, and coastal but comfortable.
    h.check("FL_C5" not in subset["County"].values,
            "a populous inland county is excluded by the AND")
    fl_c4 = state[state["County"] == "FL_C4"].iloc[0]
    h.check(fl_c4["IsCoastal"] and fl_c4["MedianIncome"] > income
            and fl_c4["Population"] < pop,
            "the comfortable coastal county (FL_C4) fails both socio-economic tests")
    h.check("FL_C4" not in subset["County"].values, "and is not in the subset")

    # The classification is built on the subset. This is the exercise's second claim, and
    # the difference is measurable: the state's own quintiles are higher at every edge.
    breaks = [float(value) for value in module.subset_classifier.bins]
    h.equal(len(breaks), 5, "five quantile classes are computed")
    h.check(breaks[0] > float(subset["MedianIncome"].min()),
            "the first break sits inside the subset, above its poorest county")
    h.close(breaks[-1], float(subset["MedianIncome"].max()),
            "the last break is the subset's own maximum", 0.5)
    h.equal(int(sum(module.subset_classifier.counts)), len(subset),
            "every selected county falls in a class")
    h.check(all(breaks[index] < breaks[index + 1] for index in range(4)),
            "the subset's breaks ascend")

    import mapclassify
    state_breaks = mapclassify.Quantiles(state["MedianIncome"], k=5).bins
    h.check(list(breaks) != [float(value) for value in state_breaks],
            "classifying the whole state first would have moved the breaks")
    h.check(float(state["MedianIncome"].min()) < breaks[0],
            "the state's poorest county is below the subset's first break")

    # The figure: the state behind, the subset in front, both on the same axes.
    collections = module.ax.collections
    h.equal(len(collections), 2, "the background and the subset are two collections")
    h.equal(len(collections[0].get_paths()), 15,
            "all fifteen counties are drawn as context")
    h.check(abs(collections[0].get_facecolors()[0][0] - 0.827) < 0.02,
            "the context layer is light grey")
    h.equal(len(collections[1].get_paths()), 6,
            "only the six selected counties are coloured by income")
    h.equal(len(collections[1].get_facecolors()), 6,
            "and each of them carries its own income colour")
    h.equal(len(module.ax.get_legend().get_texts()), 5, "the legend prints five classes")
    h.contains(module.ax.get_title(), "n=6", "the title states how many counties passed")
    h.check(not module.ax.axison, "the axes are switched off")

    saved = FILES.parent / "output" / "vulnerable_coastal_counties.png"
    h.check(saved.is_file(), "the run wrote %s" % saved.name)
    payload = saved.read_bytes()
    h.check(payload.startswith(b"\x89PNG\r\n\x1a\n"), "the file is a PNG")
    h.check(len(payload) > 5000, "the PNG carries a drawn map (%d bytes)" % len(payload))

    h.contains(printed, "(high population OR low income) AND coastal: 6 counties",
               "the listing reports the size of the mask")
    h.contains(printed, "Selected: FL_C0, FL_C2, FL_C6, FL_C8, FL_C10, FL_C14",
               "the listing names the counties the mask kept")
    h.contains(printed, "Quantile breaks over the subset",
               "the listing prints the subset's breaks")
    h.contains(printed, "over the whole state would have been",
               "and the breaks the whole state would have produced")
    h.contains(printed, "output/vulnerable_coastal_counties.png",
               "the listing names the file it wrote")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed path carries no machine's home directory")

    h.write_json("coastal_filter.json", {
        "counties": len(state),
        "thresholds": {"population": pop, "income": income},
        "conditions": {"high_population": int(high.sum()),
                       "low_income": int(low.sum()),
                       "coastal": int(coastal.sum())},
        "selected": subset["County"].tolist(),
        "breaks_subset": [round(float(value)) for value in breaks],
        "breaks_state": [round(float(value)) for value in state_breaks],
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
