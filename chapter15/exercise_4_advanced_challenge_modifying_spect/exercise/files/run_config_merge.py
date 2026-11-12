"""Harness for exercise 4 — a configuration merged, not replaced.

`dict.update` overwrites the keys that collide and adds the ones that do not. The
harness checks both halves: the NDVI threshold is halved, the EVI flag is added,
the statistical test is added — and the four settings the custom dictionary never
mentions are still there with their original values.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

NAME = "exercise 4 (configuration merge)"
UNTOUCHED = {"min_observations": 12, "fit_method": "harmonic_regression",
             "p_value_threshold": 0.05}


def main():
    h = Harness(NAME, FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "02_config_merge.py", "config_merge")
        prompt = load_listing(FILES / "prompt_sketch_exercise_4.py", "config_prompt")
        merged = module.run_geo_change_model(module.default_config)
    printed = log.getvalue()

    config = module.default_config
    custom = module.degradation_config
    baseline = prompt.define_default_config()

    # -- the merge --------------------------------------------------------
    h.equal(len(baseline), 4, "the exercise's default dictionary starts with four settings")
    h.equal(len(custom), 3, "the degradation dictionary carries three")
    h.equal(sorted(config), ["fit_method", "include_evi_check", "min_observations",
                             "p_value_threshold", "stability_threshold_ndvi",
                             "stat_test_method"],
            "the merged dictionary holds the union of the two key sets")

    # -- overwritten keys -------------------------------------------------
    h.equal(config["stability_threshold_ndvi"], 0.075,
            "the NDVI threshold was overwritten by the custom value")
    h.close(config["stability_threshold_ndvi"],
            baseline["stability_threshold_ndvi"] / 2,
            "the new threshold is exactly half the default, as the prompt asks")
    h.equal(config["include_evi_check"], True,
            "the EVI check was switched on by the merge")

    # -- keys the custom dictionary adds ----------------------------------
    h.equal(config["stat_test_method"], "t_test_modified",
            "the statistical test named by the custom dictionary is present")

    # -- keys the custom dictionary never mentions ------------------------
    for key, value in UNTOUCHED.items():
        h.equal(config[key], value, "%r survived the merge unchanged" % key)

    # -- update returns None and mutates in place -------------------------
    h.equal(merged, "Model execution simulated.",
            "the placeholder model returns its confirmation string")
    h.check(all(prompt.define_default_config()[key] == value
                for key, value in UNTOUCHED.items()),
            "the prompt's default dictionary agrees with the solution's on the shared keys")

    # -- what the reader sees -------------------------------------------
    h.contains(printed, "Initial Default NDVI Threshold: 0.15",
               "the listing prints the threshold before the merge")
    h.contains(printed, "stability_threshold_ndvi: 0.075",
               "and after it")
    h.contains(printed, "EVI Check Status: Enabled", "the model reports the EVI flag it received")
    h.contains(printed, "Model initialized using fitting method: harmonic_regression",
               "the model still receives the untouched fitting method")

    h.write_json("config_merge.json", {
        "default_keys": sorted(baseline),
        "custom_keys": sorted(custom),
        "merged_keys": sorted(config),
        "threshold_before": baseline["stability_threshold_ndvi"],
        "threshold_after": config["stability_threshold_ndvi"],
        "include_evi_check": config["include_evi_check"],
        "stat_test_method": config["stat_test_method"],
        "unchanged": UNTOUCHED,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        fallback = Harness(NAME, FILES)
        fallback.check(False, "the harness ran to completion")
        fallback.report()
