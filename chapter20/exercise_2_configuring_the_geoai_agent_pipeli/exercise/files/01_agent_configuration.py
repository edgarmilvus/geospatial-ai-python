"""Chapter 20, exercise 2 — configuration worth failing on.

The pipeline needs three settings before it can do any work: a key for the imagery
service, the path to the area of interest, and the path to the fine-tuned model. If
one is missing, the right moment to say so is now — not forty minutes into a
segmentation run. This listing loads them from the environment, refuses to start
when something is absent, and names every missing variable in one message so the
operator fixes them all in one pass.
"""

import os
from typing import Dict

REQUIRED_VARS = ["GEOAI_API_KEY", "DISASTER_ZONE_AOI", "SAM_MODEL_PATH"]

# Deliberately outside the three the volume defines: these configure the pipeline's
# own inputs (an imagery service, an AOI file, a checkpoint), not a chat model.
# The listing sets and clears them itself, so an exported value cannot change the run.
DEMO_VALUES = {
    "GEOAI_API_KEY": "demo-key-not-a-real-secret",
    "DISASTER_ZONE_AOI": "north_ridge_aoi.geojson",
    "SAM_MODEL_PATH": "sam_buildings_ft.pt",
}


# 1. The exception the operator sees
class ConfigurationError(Exception):
    """Raised when a required environment variable is missing or unusable."""


def load_agent_configuration() -> Dict[str, str]:
    """Read the three settings, or raise naming every one that is absent."""
    config = {}
    missing = []

    for var_name in REQUIRED_VARS:
        value = os.environ.get(var_name)
        if value is None or not value.strip():
            missing.append(var_name)
        else:
            config[var_name] = value.strip()

    if missing:
        raise ConfigurationError(
            "Missing required environment variables: " + ", ".join(missing)
            + ". Set them before starting the GeoAI pipeline.")

    # A path that no longer ends in .geojson, or a checkpoint with no suffix, is a
    # configuration mistake too, and it is cheaper to catch it here than in stage 2.
    if not config["DISASTER_ZONE_AOI"].endswith(".geojson"):
        raise ConfigurationError(
            "DISASTER_ZONE_AOI must point at a .geojson file, got "
            f"{config['DISASTER_ZONE_AOI']!r}")
    if not config["SAM_MODEL_PATH"].endswith((".pt", ".pth")):
        raise ConfigurationError(
            "SAM_MODEL_PATH must point at a .pt or .pth checkpoint, got "
            f"{config['SAM_MODEL_PATH']!r}")

    return config


def clear_environment():
    for var_name in REQUIRED_VARS:
        os.environ.pop(var_name, None)


def main():
    clear_environment()

    print("--- Test 1: nothing configured ---")
    try:
        load_agent_configuration()
    except ConfigurationError as exc:
        print(f"Expected failure caught: {exc}")

    print("\n--- Test 2: one variable still missing ---")
    os.environ["GEOAI_API_KEY"] = DEMO_VALUES["GEOAI_API_KEY"]
    os.environ["DISASTER_ZONE_AOI"] = DEMO_VALUES["DISASTER_ZONE_AOI"]
    try:
        load_agent_configuration()
    except ConfigurationError as exc:
        print(f"Expected failure caught: {exc}")

    print("\n--- Test 3: all three set ---")
    os.environ["SAM_MODEL_PATH"] = DEMO_VALUES["SAM_MODEL_PATH"]
    config = load_agent_configuration()
    print("Configuration loaded:")
    for name in REQUIRED_VARS:
        shown = "***" if name == "GEOAI_API_KEY" else config[name]
        print(f"  {name}: {shown}")

    print("\n--- Test 4: a value that is present but wrong ---")
    os.environ["DISASTER_ZONE_AOI"] = "north_ridge_aoi.shp"
    try:
        load_agent_configuration()
    except ConfigurationError as exc:
        print(f"Expected failure caught: {exc}")

    clear_environment()
    print("\nEnvironment restored: every demo variable removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
