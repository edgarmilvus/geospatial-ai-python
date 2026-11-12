import matplotlib
matplotlib.use("Agg")  # the listing writes a PNG; there is no interactive window to open

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import mapclassify as mc
import pathlib
from matplotlib.colors import Normalize
from shapely.geometry import box

# --- Four corrections to the book's solution, and why ---
#
# 1. The margin expression stops mid-line in the book:
#        district_gdf['Margin'] = np.where(district_gdf['Total_Votes'] > 0,
#            (district_gdf['Votes_A'] - district_gdf['Votes_B']) / district_gdf['Total_Votes'],
#    with neither the `else` branch nor the closing parenthesis, so the block does not even
#    parse. The else branch is NaN: a district that cast no votes has no margin, and the
#    chapter's own pitfall section says to draw missing data as missing, not as zero.
# 2. The breaks are symmetric, and zero is one of them. The book asks for k=9 and then
#    re-plots with `vmin=-abs_max, vmax=abs_max` for "perfect centering". Neither works
#    with a `scheme`: geopandas colours by class, so vmin/vmax changes nothing about the
#    fills, and Jenks on the signed margin puts its middle class wherever the data
#    happens to cluster (here one class to the left of zero). Classifying the distance
#    from zero with Jenks and mirroring those breaks makes both sides use the same cut
#    points, and puts zero on the central edge.
# 3. `cmap='RdBu_r'`. 'RdBu' already runs red -> white -> blue, so a Republican margin
#    (negative) is red and a Democratic one (positive) is blue. Reversing it, as the book
#    does, paints a Republican landslide blue - the opposite of the stated intention.
# 4. `plt.show()`. A script has no window, so the figure is written into output/.
#
# The ramp is sampled at i/k rather than at i/(k-1) so that the neutral colour falls on the
# edge between class 4 and class 5, which is zero; with the default normalisation the
# white would land on the centre of a class, and no class is centred on zero.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# 1. Data Calculation and Transformation (Simulated Data)
# Create dummy GeoDataFrame for districts
N = 20
districts_data = {
    'District_ID': range(N),
    'Votes_A': np.random.randint(5000, 15000, N),
    'Votes_B': np.random.randint(5000, 15000, N)
}
# Simulate some natural clustering (e.g., 5 strong D, 5 strong R, 10 competitive)
districts_data['Votes_A'][:5] += 5000
districts_data['Votes_B'][5:10] += 5000
# And one district where nobody voted: the division guard has to hold.
districts_data['Votes_A'][-1] = 0
districts_data['Votes_B'][-1] = 0

district_gdf = gpd.GeoDataFrame(
    districts_data,
    geometry=[box(i, 0, i + 1, 1) for i in range(N)],
    crs="EPSG:4326"
)

# Calculate Total Votes, handling zero division
district_gdf['Total_Votes'] = district_gdf['Votes_A'] + district_gdf['Votes_B']
# Use np.where to prevent division by zero: no votes cast means no margin, not a zero one.
district_gdf['Margin'] = np.where(
    district_gdf['Total_Votes'] > 0,
    (district_gdf['Votes_A'] - district_gdf['Votes_B']) / district_gdf['Total_Votes'],
    np.nan
)

# 2. Symmetric breaks: Jenks on the distance from zero, mirrored, zero included
K_PER_SIDE = 4  # four breaks each side of zero, plus zero itself: nine edges, nine classes
distances = mc.NaturalBreaks(np.abs(district_gdf['Margin'].dropna()), k=K_PER_SIDE)
classes = [-value for value in distances.bins][::-1] + [0.0] + list(distances.bins)
classifier = mc.UserDefined(district_gdf['Margin'].dropna(), classes)
district_gdf['Margin_Class'] = np.nan
district_gdf.loc[district_gdf['Margin'].notna(), 'Margin_Class'] = classifier.yb
K_CLASSES = len(classes)
ZERO_EDGE = K_PER_SIDE  # classes[4] is zero: classes 0..3 are negative, 5..8 positive

# 3. Diverging color ramp, centred on zero by construction
fig, ax = plt.subplots(1, 1, figsize=(12, 6))

# Use RdBu: Red (Republican/Negative Margin) to Blue (Democrat/Positive Margin).
district_gdf.plot(
    column='Margin',
    ax=ax,
    legend=True,
    scheme='UserDefined',
    classification_kwds={'bins': classes},
    cmap='RdBu',
    edgecolor='white',
    linewidth=0.5,
    # i / k, not i / (k-1): the neutral midpoint then sits on the zero edge, with equal
    # distance to the last negative class and the first positive one.
    norm=Normalize(0, K_CLASSES),
    missing_kwds={'color': 'lightgrey', 'label': 'No votes cast'},
    legend_kwds={'loc': 'lower left', 'fmt': "{:.2f}", 'title': "Normalized Margin (A - B)"}
)

# 4. Visualization and Interpretation
ax.set_title(f"Election Margin: Jenks Natural Breaks (k={K_CLASSES}, centred on zero)",
             fontsize=16)
ax.set_axis_off()
fig.tight_layout()

print(f"--- Margin over {len(district_gdf)} districts ---")
print(f"Range: {district_gdf['Margin'].min():+.3f} to {district_gdf['Margin'].max():+.3f} "
      f"(-1.0 is a unanimous Republican district, +1.0 unanimous Democrat)")
print(f"Districts with no votes cast: "
      f"{int(district_gdf['Margin'].isna().sum())} (margin left missing, drawn grey)")
print("\nDistances from zero, classified by Jenks (k=%d): " % K_PER_SIDE +
      ", ".join(f"{value:.3f}" for value in distances.bins))
print("Class edges, mirrored around zero: " +
      ", ".join(f"{value:+.3f}" for value in classes))
print(f"Zero is edge {ZERO_EDGE}: {classes[ZERO_EDGE] == 0.0}; "
      f"edges are symmetric: "
      f"{all(abs(classes[i] + classes[K_CLASSES - 1 - i]) < 1e-12 for i in range(K_CLASSES))}")
print("\nCounts per class: " + ", ".join(str(int(count)) for count in classifier.counts))
print(f"Districts left of zero: "
      f"{int((district_gdf['Margin'] < 0).sum())}; right of zero: "
      f"{int((district_gdf['Margin'] > 0).sum())}")

figure_path = OUTPUT / "electoral_margin_jenks.png"
fig.savefig(figure_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print("\n--- Figure ---")
print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
print(f"Bytes: {figure_path.stat().st_size}")
print(f"Legend entries: {len(ax.get_legend().get_texts())}")
