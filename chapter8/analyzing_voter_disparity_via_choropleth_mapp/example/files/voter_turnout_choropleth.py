import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import mapclassify as mc
import numpy as np
import pathlib
from shapely.geometry import box

# --- Two substitutions, and why ---
#
# 1. Data. The book loads `gpd.datasets.get_path('naturalearth_lowres')` and filters it to
#    North America. GeoPandas 1.0 removed the bundled datasets, and a listing in this
#    volume may not download a replacement, so twelve administrative units are built here
#    as a 4 by 3 mosaic of counties over the continental United States: the same two
#    columns (`name`, `pop_est`), the same CRS, none of the network. The mosaic is fixed,
#    and the election numbers below come from a seeded generator, so every break this
#    listing prints is reproducible.
# 2. `plt.show()`. A script has no window, so the two-panel figure is written into the
#    project's output/ folder and the class breaks are printed as numbers.

np.random.seed(42)

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# Set Matplotlib style for professional output consistency
plt.style.use('seaborn-v0_8-whitegrid')


def synthetic_counties(rows=3, columns=4):
    """Twelve contiguous counties in WGS 84, 1.5 by 1 degree each, over the US interior."""
    cells, names, populations = [], [], []
    for row in range(rows):
        for column in range(columns):
            west = -100.0 + column * 1.5
            south = 36.0 + row
            cells.append(box(west, south, west + 1.5, south + 1.0))
            names.append("County %02d" % (row * columns + column + 1))
            # 40 000 to 2 400 000 residents, the spread a state's counties really have.
            populations.append(int(np.random.uniform(40_000, 2_400_000)))
    return gpd.GeoDataFrame({"name": names, "pop_est": populations},
                            geometry=cells, crs="EPSG:4326")


# --- 1. Load Geospatial Boundaries (Administrative Units) ---
geo_data = synthetic_counties()
if len(geo_data) == 0:
    # A GeoAI pipeline that silently maps nothing is worse than one that stops.
    raise SystemExit("CRITICAL ERROR: no administrative units to map.")

geo_data = geo_data[['name', 'pop_est', 'geometry']].rename(
    columns={'name': 'County_ID', 'pop_est': 'Base_Population'})
print(f"Loaded {len(geo_data)} administrative units for mapping.")

# --- 2. Generate Synthetic Statistical Data (Simulated Election Results) ---
# Create a DataFrame where the 'County_ID' matches the geospatial data
statistical_data = pd.DataFrame({
    'County_ID': geo_data['County_ID'].unique(),
    # Simulate Registered Voters as a percentage of the base population.
    # `np.random.uniform(low, high)` with no `size` returns ONE number, so the book's
    # three draws below multiply a whole column by a single constant and every county
    # ends up with the same turnout. `size` is what makes the numbers differ per row.
    'Registered_Voters': (geo_data['Base_Population']
                          * np.random.uniform(0.5, 0.7, len(geo_data))).astype(int),
    # Simulate Actual Turnout (must be less than or equal to registered voters)
    'Actual_Turnout': (geo_data['Base_Population']
                       * np.random.uniform(0.2, 0.5, len(geo_data))).astype(int),
})
# Votes for Candidate A are drawn as a share of the votes actually cast, not of the
# population. The book draws them independently, which lets a district report more votes
# for one candidate than were cast in total; clipping that to 100% hides the impossible
# number instead of preventing it.
statistical_data['Candidate_A_Votes'] = (
    statistical_data['Actual_Turnout']
    * np.random.uniform(0.3, 0.7, len(geo_data))).astype(int)

# Ensure data integrity: Turnout cannot exceed registration
statistical_data['Actual_Turnout'] = np.minimum(
    statistical_data['Actual_Turnout'], statistical_data['Registered_Voters']
)
statistical_data['Candidate_A_Votes'] = np.minimum(
    statistical_data['Candidate_A_Votes'], statistical_data['Actual_Turnout']
)

# --- 3. Data Merging and Feature Engineering ---

# 3.1. Perform the standard Pandas merge (left join) using the common attribute key
merged_gdf = geo_data.merge(statistical_data, on='County_ID', how='left')

# 3.2. Calculate the primary visualization metric: Voter Turnout Rate (TR)
# TR = (Actual Votes / Registered Voters) * 100
merged_gdf['Turnout_Rate'] = (merged_gdf['Actual_Turnout'] / merged_gdf['Registered_Voters']) * 100

# 3.3. Calculate the secondary metric: Candidate A's Percentage of Total Votes
merged_gdf['Candidate_A_Pct'] = (merged_gdf['Candidate_A_Votes'] / merged_gdf['Actual_Turnout']) * 100

# Clean up any potential NaNs or infinite values resulting from division by zero
merged_gdf = merged_gdf.replace([np.inf, -np.inf], np.nan).dropna(
    subset=['Turnout_Rate', 'Candidate_A_Pct'])

# --- 4. Advanced Classification and Choropleth Generation ---

# Define the variable for the primary map
map_variable = 'Turnout_Rate'

# 4.1. Use Jenks Natural Breaks classification for optimal visual grouping
# Jenks algorithm finds the most natural groupings in the data distribution.
# The classifier is built once here, and its breaks are handed to `.plot()` as a
# UserDefined scheme. That is the difference between a map and a picture: the lines the
# legend prints are the breaks this file computed, not a second set chosen inside the
# plotting call. (Geopandas 1.0 no longer accepts a classifier object as `scheme`, and
# its own `scheme='NaturalBreaks'` re-runs the optimisation with different tie-breaking:
# 44.5 where `NaturalBreaks(...).bins` has 47.1, on the same twelve values.)
turnout_classifier = mc.NaturalBreaks(merged_gdf[map_variable], k=5)
# Quantiles put the same number of counties in each class, whatever the values do.
share_classifier = mc.Quantiles(merged_gdf['Candidate_A_Pct'], k=5)

# 4.2. Initialize the dual plot figure
fig, axes = plt.subplots(1, 2, figsize=(18, 9))

# Map 1: Voter Turnout Rate (Jenks Classification)
merged_gdf.plot(
    column=map_variable,
    ax=axes[0],
    legend=True,
    scheme='UserDefined',                         # the breaks are the Jenks ones, below
    classification_kwds={'bins': turnout_classifier.bins},
    cmap='viridis_r',                             # Use a sequential, reversed color scheme
    edgecolor='black',
    linewidth=0.5,
    missing_kwds={'color': 'lightgrey', 'label': 'No Data/Filtered'}
)
axes[0].set_title(f'Map A: Voter Turnout Rate (Jenks Natural Breaks, K={turnout_classifier.k})',
                  fontsize=14)
axes[0].set_axis_off()

# Map 2: Candidate A Voting Percentage (Quantiles Classification)
# This map demonstrates a different classification scheme for comparison.
# The ramp is diverging, but note what it is diverging around: the white midpoint of
# 'RdBu' lands at 50% of the colour axis, and Quantiles does not put 50 there - so on
# this map red means "bottom fifth of the districts", not "below half the vote". The
# margin, mapped in exercise 2, is the variable a diverging ramp is actually for.
merged_gdf.plot(
    column='Candidate_A_Pct',
    ax=axes[1],
    legend=True,
    scheme='UserDefined',                         # Quantiles breaks, from the classifier
    classification_kwds={'bins': share_classifier.bins},
    cmap='RdBu',              # Diverging Red-Blue scheme for political data
    edgecolor='black',
    linewidth=0.5,
    missing_kwds={'color': 'lightgrey', 'label': 'No Data/Filtered'}
)
axes[1].set_title('Map B: Candidate A Percentage of Votes (Quantiles)', fontsize=14)
axes[1].set_axis_off()

# Finalizing the visualization
fig.suptitle("Comparative Geo-Analysis of Simulated Election Data Across Administrative Regions",
             fontsize=16, y=1.02)
fig.tight_layout()

# --- 5. Report the classification, then save ---
#
# A choropleth's honest content is its breaks: two maps of the same column tell
# different stories exactly where their breaks fall.
print("\n--- Map A: Voter Turnout Rate, Jenks (k=%d) ---" % turnout_classifier.k)
print("Breaks (%):  " + ", ".join(f"{value:.2f}" for value in turnout_classifier.bins))
print("Counties per class: " + ", ".join(str(int(count)) for count in turnout_classifier.counts))
print("\n--- Map B: Candidate A share, Quantiles (k=%d) ---" % share_classifier.k)
print("Breaks (%):  " + ", ".join(f"{value:.2f}" for value in share_classifier.bins))
print("Counties per class: " + ", ".join(str(int(count)) for count in share_classifier.counts))
print("\n--- Range of each variable ---")
print(f"Turnout_Rate:     {merged_gdf['Turnout_Rate'].min():.2f} to "
      f"{merged_gdf['Turnout_Rate'].max():.2f} %")
print(f"Candidate_A_Pct:  {merged_gdf['Candidate_A_Pct'].min():.2f} to "
      f"{merged_gdf['Candidate_A_Pct'].max():.2f} %")

figure_path = OUTPUT / "voter_turnout_choropleth.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")
print(f"Legend entries: panel A {len(axes[0].get_legend().get_texts())}, "
      f"panel B {len(axes[1].get_legend().get_texts())}")
