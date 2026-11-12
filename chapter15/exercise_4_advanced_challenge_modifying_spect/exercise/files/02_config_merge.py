# Required Python structures: dict, dict.update()

def define_default_config():
    """
    Creates the baseline configuration dictionary for the GeoChangeModel.
    """
    return {
        "stability_threshold_ndvi": 0.15, # Default high threshold for abrupt change
        "min_observations": 12,
        "fit_method": "harmonic_regression",
        "p_value_threshold": 0.05,
        "include_evi_check": False
    }

def define_degradation_params():
    """
    Creates the custom parameters for detecting slower degradation.
    """
    return {
        "stability_threshold_ndvi": 0.075, # Lowered sensitivity (50% reduction)
        "stat_test_method": "t_test_modified", # New parameter
        "include_evi_check": True # Overwrites default False
    }

def run_geo_change_model(config):
    """
    Placeholder function demonstrating model execution with the custom configuration.
    """
    print("\n--- GeoChangeModel Execution Simulation ---")
    print(f"Model initialized using fitting method: {config['fit_method']}")
    print(f"Change detected if NDVI deviation exceeds: {config['stability_threshold_ndvi']}")
    print(f"EVI Check Status: {'Enabled' if config['include_evi_check'] else 'Disabled'}")
    return "Model execution simulated."

# Main steps:
default_config = define_default_config()
degradation_config = define_degradation_params()

print("Initial Default NDVI Threshold:", default_config["stability_threshold_ndvi"])

# 1. Merge the custom configuration into the default configuration using dict.update()
default_config.update(degradation_config)

# 2. Print the final configuration dictionary.
print("\n--- Final Merged Configuration ---")
for key, value in default_config.items():
    print(f"{key}: {value}")

# 3. Call run_geo_change_model()
run_geo_change_model(default_config)
