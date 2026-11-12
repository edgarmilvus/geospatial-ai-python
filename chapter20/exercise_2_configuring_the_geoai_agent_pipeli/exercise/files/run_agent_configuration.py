"""Harness for chapter 20, exercise 2 — fail fast, and name everything that is missing.

Four cases, in the order an operator meets them: nothing set, one variable still
missing, everything set, and a value that is present but points at the wrong kind of
file. The assertion that matters is not the success branch — it is that the failure
message lists *all* the missing names at once, so the fix is one edit and not three.
"""
import contextlib
import io
import json
import os
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 2 (agent configuration)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_agent_configuration.py", "agent_configuration")
        module.main()
    printed = log.getvalue()

    h.equal(module.REQUIRED_VARS,
            ["GEOAI_API_KEY", "DISASTER_ZONE_AOI", "SAM_MODEL_PATH"],
            "the loader names the three settings the pipeline needs")
    h.check(issubclass(module.ConfigurationError, Exception),
            "ConfigurationError is an Exception the caller can catch")

    # --- nothing set ---
    module.clear_environment()
    captured = {}

    def all_missing():
        return module.load_agent_configuration()

    try:
        all_missing()
    except module.ConfigurationError as exc:
        captured["all"] = str(exc)
    h.check("all" in captured, "with nothing set the loader raises instead of returning {}")
    for name in module.REQUIRED_VARS:
        h.contains(captured.get("all", ""), name,
                   "the message lists %s among the missing names" % name)

    # --- one still missing ---
    os.environ["GEOAI_API_KEY"] = "demo-key"
    os.environ["DISASTER_ZONE_AOI"] = "north_ridge_aoi.geojson"
    captured.clear()
    try:
        module.load_agent_configuration()
    except module.ConfigurationError as exc:
        captured["one"] = str(exc)
    h.contains(captured.get("one", ""), "SAM_MODEL_PATH",
               "the second failure names the one variable still missing")
    h.check("GEOAI_API_KEY" not in captured.get("one", ""),
            "and does not name the ones that are set")

    # --- everything set ---
    os.environ["SAM_MODEL_PATH"] = "sam_buildings_ft.pt"
    config = module.load_agent_configuration()
    h.equal(sorted(config), sorted(module.REQUIRED_VARS),
            "a complete configuration returns all three keys")
    h.equal(config["DISASTER_ZONE_AOI"], "north_ridge_aoi.geojson",
            "the returned value is the one that was exported")
    h.equal(len(config), 3, "nothing extra is added to the dictionary")

    # --- present but wrong ---
    os.environ["DISASTER_ZONE_AOI"] = "north_ridge_aoi.shp"
    captured.clear()
    try:
        module.load_agent_configuration()
    except module.ConfigurationError as exc:
        captured["wrong"] = str(exc)
    h.contains(captured.get("wrong", ""), "geojson",
               "a Shapefile path is rejected with the reason, not a stack trace")
    os.environ["DISASTER_ZONE_AOI"] = "north_ridge_aoi.geojson"
    os.environ["SAM_MODEL_PATH"] = "sam_buildings_ft.pt"

    # --- the listing cleans up after itself ---
    with contextlib.redirect_stdout(io.StringIO()):
        module.main()
    h.check(all(name not in os.environ for name in module.REQUIRED_VARS),
            "the run leaves the environment as it found it: no demo value survives")
    h.contains(printed, "GEOAI_API_KEY: ***",
               "the key is masked in the output, not printed")

    module.clear_environment()
    h.write_json("agent_configuration.json", {
        "required": module.REQUIRED_VARS,
        "all_missing_message": captured.get("all", "")[:120],
        "one_missing_message": captured.get("one", "")[:120],
        "wrong_value_message": captured.get("wrong", "")[:120],
        "loaded_keys": sorted(config),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (agent configuration)", FILES).crash())
