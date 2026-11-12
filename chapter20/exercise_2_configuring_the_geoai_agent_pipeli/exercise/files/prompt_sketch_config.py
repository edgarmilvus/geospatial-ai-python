# Setup for exercise 2: configuration from the environment.
import os
from typing import Dict

# 1. Define the custom ConfigurationError exception here


def load_agent_configuration() -> Dict[str, str]:
    """
    Loads critical configuration settings from environment variables.
    Raises ConfigurationError if any required variable is missing.
    """
    REQUIRED_VARS = ['GEOAI_API_KEY', 'DISASTER_ZONE_AOI', 'SAM_MODEL_PATH']
    config = {}
    missing_vars = []

    # Implementation must iterate through REQUIRED_VARS and check os.environ

    if missing_vars:
        # Raise ConfigurationError listing all missing variables
        pass

    return config


# Simulation setup (to be included in the solution for testing):
# os.environ['DISASTER_ZONE_AOI'] = 'aoi.geojson'
# os.environ['SAM_MODEL_PATH'] = 'sam_ft.pt'
# Test case 1: success (requires setting the third variable too)
# Test case 2: failure (requires deleting one variable before calling the function)
