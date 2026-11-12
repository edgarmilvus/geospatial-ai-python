"""Harness for exercise 5 — normalise, then wrap the map in a function.

Two claims to check. The normalisation: a rate that divides registered voters by the
voting-eligible population, on data where registered voters actually are a share of that
population. The functionalisation: one call, one map, one file — made twice with different
columns, which is the only way to know the function is parameterised rather than written
around one column.
"""
import contextlib
import inspect
import io
import pathlib
import sys
import traceback

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 5 (registration rate function)"


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "registration_rate_function.py", "registration_rate")
    printed = log.getvalue()

    frame = module.state_gdf

    # The normalisation.
    h.equal(len(frame), 50, "fifty states are simulated")
    h.equal(module.N_states, 50, "and the module says so")
    expected = frame["Total Registered Voters"] / frame["VEP"] * 100
    h.check((frame["RegistrationRate"] - expected).abs().max() < 1e-9,
            "the rate is registered voters over VEP, times 100")
    h.check(frame["RegistrationRate"].between(55.0, 100.0).all(),
            "every rate is a percentage between 55 and 100")
    h.check((frame["Total Registered Voters"] <= frame["VEP"]).all(),
            "no state registers more voters than it has eligible voters")
    h.equal(module.CAP, 0, "the defensive clip fires on nothing, and the listing says so")
    h.check(frame["RegistrationRate"].nunique() > 40,
            "the rates are a distribution, not one repeated number")

    # The function.
    function = getattr(module, "generate_jenks_map", None)
    h.check(function is not None, "the solution defines generate_jenks_map")
    h.equal(list(inspect.signature(function).parameters),
            ["gdf", "column_name", "k_classes"],
            "and it takes the three arguments the exercise requires")

    axis, classifier, path = module.ax, module.classifier, module.figure_path

    h.equal(classifier.k, 5, "the function was called with five classes")
    h.equal(len(classifier.bins), 5, "five classes publish five breaks")
    h.check(all(b > a for a, b in zip(classifier.bins, classifier.bins[1:])),
            "the breaks ascend")
    h.equal(int(sum(classifier.counts)), 50, "every state falls in one class")
    h.check(float(classifier.bins[-1]) <= 100.0,
            "the top break stays inside the percentage scale")
    h.equal(len(axis.get_legend().get_texts()), 5, "the legend prints five classes")
    h.contains(axis.get_title(), "RegistrationRate", "the title names the column")
    h.contains(axis.get_title(), "k=5", "and the class count")
    h.check(not axis.axison, "the axes are switched off")

    h.check(path.is_file(), "the function wrote %s" % path.name)
    payload = path.read_bytes()
    h.check(payload.startswith(b"\x89PNG\r\n\x1a\n"), "and the file is a PNG")
    h.check(len(payload) > 10_000, "carrying a drawn map (%d bytes)" % len(payload))
    h.check(path.parent == pathlib.Path(module.__file__).resolve().parent.parent / "output",
            "written into the project's own output/ folder")

    # The second call: a different column, a different number of classes, its own file.
    second_axis, second_classifier, second_path = module.ax_vep, module.classifier_vep, \
        module.figure_vep
    h.equal(second_classifier.k, 4, "the second call asks for four classes")
    h.check(list(second_classifier.bins) != list(classifier.bins),
            "and gets its own breaks, not the first call's")
    h.check(second_path != path and second_path.is_file(),
            "and its own file: %s" % second_path.name)
    h.check(len(second_path.read_bytes()) > 10_000, "which is also a drawn PNG")
    h.contains(second_axis.get_title(), "VEP", "the second title names the second column")
    h.equal(len(second_axis.get_legend().get_texts()), 4,
            "the second legend follows its own class count")

    h.contains(printed, "Map generated for column: RegistrationRate with k=5 classes.",
               "the function reports what it drew")
    h.contains(printed, "States whose rate was capped at 100%: 0",
               "the run reports the clip honestly")
    h.contains(printed, "output/jenks_registrationrate.png",
               "the run names the primary figure")
    h.contains(printed, "output/jenks_vep.png", "and the second one")
    h.check(str(pathlib.Path.home()) not in printed,
            "the printed paths carry no machine's home directory")

    h.write_json("registration_rate.json", {
        "states": len(frame),
        "rate_range": [round(float(frame["RegistrationRate"].min()), 2),
                       round(float(frame["RegistrationRate"].max()), 2)],
        "capped": module.CAP,
        "primary": {
            "column": "RegistrationRate",
            "classes": int(classifier.k),
            "breaks": [round(float(value), 2) for value in classifier.bins],
            "counts": [int(value) for value in classifier.counts],
            "file": path.name,
        },
        "second": {
            "column": "VEP",
            "classes": int(second_classifier.k),
            "breaks": [round(float(value), 1) for value in second_classifier.bins],
            "counts": [int(value) for value in second_classifier.counts],
            "file": second_path.name,
        },
        "signature": str(inspect.signature(function)),
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
