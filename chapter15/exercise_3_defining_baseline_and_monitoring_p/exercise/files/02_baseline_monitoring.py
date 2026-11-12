from datetime import date, timedelta
import numpy as np
import xarray as xr
import pandas as pd

# Simulation: Create a 3-year daily NDVI stack
def create_sample_ndvi_stack():
    start = date(2020, 1, 1)
    end = date(2022, 12, 31)
    dates = pd.to_datetime(pd.date_range(start, end, freq='D'))
    T, Y, X = len(dates), 10, 10
    # A fixed seed keeps the difference map, and the pixel count below, reproducible.
    rng = np.random.default_rng(15)
    data = rng.uniform(0.5, 0.8, size=(T, Y, X))
    # Simulate a drop (deforestation) near the end of 2022: the healthy 0.5-0.8 band
    # falls to 0.20-0.32, which is the gap the 0.3 threshold is there to catch.
    data[T-100:] *= 0.4
    return xr.DataArray(
        data=data, coords={'time': dates, 'y': np.arange(Y), 'x': np.arange(X)},
        dims=('time', 'y', 'x'), name='Interpolated_NDVI'
    )

interpolated_ndvi_stack = create_sample_ndvi_stack()
deforestation_alert_date = date(2022, 11, 1)

def define_time_windows(alert_date):
    """
    Calculates the start/end dates for the 18-month baseline and 6-month monitoring periods.
    """
    # Use average days per month (30.4375) for timedelta approximation of months
    baseline_duration = timedelta(days=18 * 30.4375)
    monitoring_duration = timedelta(days=6 * 30.4375)

    # Monitoring period
    monitoring_start = alert_date
    monitoring_end = alert_date + monitoring_duration

    # Baseline period (ends day before monitoring starts)
    baseline_end = alert_date - timedelta(days=1)
    baseline_start = baseline_end - baseline_duration
    
    # Convert to pandas datetime objects for xarray slicing
    return (pd.to_datetime(d) for d in [baseline_start, baseline_end, monitoring_start, monitoring_end])

def calculate_change_map(ndvi_stack, baseline_start, baseline_end, monitoring_start, monitoring_end):
    """
    Subsets the data, calculates the mean for each period, and computes the difference.
    """
    # 1. Subset the stack using xarray's .sel(time=slice(start, end))
    baseline_subset = ndvi_stack.sel(time=slice(baseline_start, baseline_end))
    monitoring_subset = ndvi_stack.sel(time=slice(monitoring_start, monitoring_end))
    
    # 2. Calculate the mean along the 'time' dimension.
    baseline_mean = baseline_subset.mean(dim='time')
    monitoring_mean = monitoring_subset.mean(dim='time')
    
    # 3. Calculate the difference map: Delta NDVI = Baseline_mean - Monitoring_mean
    delta_ndvi = baseline_mean - monitoring_mean
    
    # 4. Apply the threshold (Delta NDVI > 0.3)
    deforestation_map = delta_ndvi > 0.3
    
    print(f"Baseline: {baseline_start.date()} to {baseline_end.date()}")
    print(f"Monitoring: {monitoring_start.date()} to {monitoring_end.date()}")
    
    return delta_ndvi, deforestation_map

# Main execution
b_start, b_end, m_start, m_end = define_time_windows(deforestation_alert_date)
delta_ndvi_map, binary_deforestation_map = calculate_change_map(
    interpolated_ndvi_stack, b_start, b_end, m_start, m_end
)

print(f"\nDelta NDVI Mean: {delta_ndvi_map.mean().item():.4f}")
print(f"Number of Deforestation Pixels: {binary_deforestation_map.sum().item()}")
