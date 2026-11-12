import folium
import pandas as pd
import pathlib
import sys
from datetime import datetime, timedelta
import numpy as np

# 1. Data Structure with Dates
N_SENSORS = 15
# Used when no terminal is attached, so the listing never blocks on a keystroke.
DEFAULT_THRESHOLD_DAYS = 30
np.random.seed(42)

# Generate realistic dates: some recent, some old
current_date = datetime.now().date()
dates = []
for i in range(N_SENSORS):
    if i % 3 == 0:
        # Intentionally old dates (30 to 60 days ago)
        days_ago = np.random.randint(30, 60)
    else:
        # Recent dates (0 to 15 days ago)
        days_ago = np.random.randint(0, 15)
    
    inspection_date = current_date - timedelta(days=days_ago)
    dates.append(inspection_date.strftime('%Y-%m-%d'))

data = {
    'latitude': 34.0 + np.random.rand(N_SENSORS) * 0.1,
    'longitude': -118.3 + np.random.rand(N_SENSORS) * 0.1,
    'sensor_id': [f"S-{i+1:03}" for i in range(N_SENSORS)],
    'last_inspection_date': dates
}
df = pd.DataFrame(data)
df['last_inspection_dt'] = pd.to_datetime(df['last_inspection_date']).dt.date

# 2. Interactive Input and 5. Robustness Check
if sys.stdin.isatty():
    while True:
        try:
            threshold_days = input("Enter inspection threshold in days (e.g., 30): ")
            threshold_days = int(threshold_days)
            if threshold_days <= 0:
                print("Please enter a positive integer.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a whole number.")
else:
    # Pipeline, notebook or harness: no keyboard to wait for, so take the default.
    threshold_days = DEFAULT_THRESHOLD_DAYS
    print(f"No terminal attached: using the default threshold of {threshold_days} days.")

# 3. Date Arithmetic
# Calculate the cutoff date: any date older than this is overdue
cutoff_date = current_date - timedelta(days=threshold_days)

# 4. Conditional Filtering and Visualization
m = folium.Map(location=[34.05, -118.25], zoom_start=12)

print(f"\nFiltering assets. Cutoff Date: {cutoff_date}. Threshold: {threshold_days} days.")

for index, row in df.iterrows():
    inspection_dt = row['last_inspection_dt']
    
    if inspection_dt < cutoff_date:
        # Overdue status
        status = "OVERDUE"
        color = 'red'
        icon = 'exclamation'
    else:
        # Current status
        status = "Current"
        color = 'green'
        icon = 'check'
        
    popup_text = f"SENSOR ID: {row['sensor_id']}<br>STATUS: <b>{status}</b><br>(Last Inspected: {row['last_inspection_date']})"
    
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color=color, icon=icon, prefix='fa')
    ).add_to(m)

# The map lives in memory until it is written; save it into the project's output/.
output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "exercise4_time_filter.html"
m.save(str(output_file))

overdue = int((df['last_inspection_dt'] < cutoff_date).sum())
print(f"Saved {output_file.relative_to(output_dir.parent)}: {overdue} of {len(df)} "
      f"sensors overdue at a {threshold_days}-day threshold.")
