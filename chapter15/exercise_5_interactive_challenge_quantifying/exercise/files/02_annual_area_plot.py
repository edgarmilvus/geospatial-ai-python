import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import pathlib

# Define area constants (for Sentinel-2 10m resolution)
PIXEL_RESOLUTION_SQ_M = 100 
SQ_M_TO_HECTARES = 10000

# Everything this listing writes goes into the project's own output folder.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Data Simulation: 3 years, 500x500 pixels
Y, X = 500, 500
years = [2020, 2021, 2022]

# A fixed seed keeps the three annual totals identical on every run.
RNG = np.random.default_rng(15)

# Simulate annual deforestation with increasing rates
annual_data = np.stack([
    RNG.choice([False, True], size=(Y, X), p=[0.99, 0.01]), # 2020: 1% loss
    RNG.choice([False, True], size=(Y, X), p=[0.98, 0.02]), # 2021: 2% loss
    RNG.choice([False, True], size=(Y, X), p=[0.97, 0.03])  # 2022: 3% loss
])

annual_deforestation_stack = xr.DataArray(
    data=annual_data,
    coords={'time': years, 'y': np.arange(Y), 'x': np.arange(X)},
    dims=('time', 'y', 'x'),
    name='Annual_Deforestation'
)

def calculate_area_hectares(boolean_map, pixel_resolution_sq_m=PIXEL_RESOLUTION_SQ_M):
    """
    Converts the count of True pixels in a boolean map to area in hectares.
    """
    # 1. Count the number of True values (deforested pixels)
    deforested_pixel_count = boolean_map.sum().item()
    
    # 2. Calculate total area in square meters
    total_sq_m = deforested_pixel_count * pixel_resolution_sq_m
    
    # 3. Convert total square meters to hectares
    area_hectares = total_sq_m / SQ_M_TO_HECTARES
    
    return area_hectares

def aggregate_annual_loss(deforestation_stack, pixel_area):
    """
    Calculates the annual deforestation loss and the cumulative loss.
    """
    annual_loss_list = []
    
    # 1. Iterate through the time dimension (xarray iteration handles this)
    for year_map in deforestation_stack:
        area = calculate_area_hectares(year_map, pixel_area)
        annual_loss_list.append(area)
        
    # 2. Calculate the cumulative sum of the annual losses.
    cumulative_loss_data = np.cumsum(annual_loss_list)
    
    return annual_loss_list, cumulative_loss_data

def plot_cumulative_loss(years, cumulative_loss_data, output_path):
    """
    Generates a clear line plot of the cumulative deforestation.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(years, cumulative_loss_data, marker='o', linestyle='-', color='red', linewidth=2)
    
    plt.title('Cumulative Deforestation Rate (2020-2022)', fontsize=14)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Cumulative Area Lost (Hectares)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years)
    # Save the figure where the rest of this project's artefacts live.
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

# Main execution flow
annual_loss, cumulative_loss = aggregate_annual_loss(annual_deforestation_stack, PIXEL_RESOLUTION_SQ_M)

print("--- Annual Deforestation Quantification ---")
for year, loss in zip(years, annual_loss):
    print(f"Deforestation detected in {year}: {loss:.2f} Hectares")

print(f"Cumulative loss after {years[-1]}: {cumulative_loss[-1]:.2f} Hectares")
print(f"Total pixels analysed: {Y * X}, each {PIXEL_RESOLUTION_SQ_M} square metres")

# Visualization
plot_cumulative_loss(years, cumulative_loss, OUTPUT_DIR / "annual_deforestation.png")
print("Plot saved to: annual_deforestation.png")
