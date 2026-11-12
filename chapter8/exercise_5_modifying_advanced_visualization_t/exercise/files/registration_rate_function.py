import matplotlib
matplotlib.use("Agg")  # the function writes a PNG; there is no interactive window to open

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import mapclassify
import pathlib
from shapely.geometry import box

# --- Three corrections to the book's solution, and why ---
#
# 1. The data is seeded: `np.random.randint` without a seed gives a different fifty states
#    on every run, so the Jenks breaks change every time the function is called.
# 2. The function saves its figure. As written it ends with `plt.close(fig)`, so the map it
#    built exists for one line and then is thrown away - the "standardised map generator"
#    has no output. It now returns the axis, the classifier and the file it wrote, which is
#    also what makes the function testable.
# 3. The classification is handed to `.plot()` as explicit breaks (geopandas 1.0 no longer
#    accepts a classifier object as `scheme`), so the legend prints exactly the breaks the
#    function returns.

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# 1. Data Normalization (Simulated State Data)
N_states = 50
state_data = {
    'State': [f'State_{i}' for i in range(N_states)],
    'VEP': np.random.randint(1500000, 15000000, N_states),
}
# Registered voters are a share of the voting-eligible population, 55% to 95%. The book
# draws the two columns independently, so twenty of its fifty states register more voters
# than they have eligible voters; clipping that to 100% would turn the error into a spike
# of twenty states in the top class, and the map would report a class break that is an
# artefact of the generator.
state_data['Total Registered Voters'] = (
    state_data['VEP'] * np.random.uniform(0.55, 0.95, N_states)).astype(int)
state_gdf = gpd.GeoDataFrame(
    state_data,
    geometry=[box(i % 10, i // 5, (i % 10) + 0.9, (i // 5) + 0.9) for i in range(N_states)],
    crs="EPSG:4326"
)

# Calculate the Registration Rate (as a percentage)
state_gdf['RegistrationRate'] = (state_gdf['Total Registered Voters'] / state_gdf['VEP']) * 100

# Cap the rate at 100% just in case of data anomalies
state_gdf['RegistrationRate'] = state_gdf['RegistrationRate'].clip(upper=100)
CAP = int(state_gdf['RegistrationRate'].eq(100).sum())


# 2. Function Definition (`generate_jenks_map`)
def generate_jenks_map(gdf, column_name, k_classes):
    """
    Standardized function to create a Jenks-classified choropleth map.
    Maps the specified column using Natural Breaks classification.
    """
    # TODO: In a production environment leveraging SQLAlchemy,
    # the initial GeoDataFrame loading would be replaced by a query
    # fetching the required geospatial data from a PostGIS enabled database.

    # Requirement 3: Jenks Classification Justification Comment
    # Jenks is used here because it identifies natural clusters of high/low performance rates
    # (e.g., states with exceptionally high or low registration performance)
    # by minimizing variance within the resulting groups, making the breaks statistically meaningful.

    classifier = mapclassify.NaturalBreaks(gdf[column_name], k=k_classes)

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Classification and plotting logic
    gdf.plot(
        column=column_name,
        ax=ax,
        legend=True,
        scheme='UserDefined',
        classification_kwds={'bins': list(classifier.bins)},
        cmap='plasma',
        edgecolor='white',
        linewidth=0.5,
        legend_kwds={'loc': 'lower left', 'fmt': "{:.1f}", 'title': f"{column_name} (%)"}
    )

    ax.set_title(f"State Analysis: {column_name} (Jenks k={k_classes})", fontsize=16)
    ax.set_axis_off()
    fig.tight_layout()

    # The map has to outlive the call that made it.
    slug = column_name.lower().replace("_", "_").replace(" ", "_")
    figure_path = OUTPUT / f"jenks_{slug}.png"
    fig.savefig(figure_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Map generated for column: {column_name} with k={k_classes} classes.")
    print(f"Breaks: " + ", ".join(f"{value:.1f}" for value in classifier.bins))
    print(f"States per class: " + ", ".join(str(int(count)) for count in classifier.counts))
    print(f"Saved: {figure_path.relative_to(OUTPUT.parent)}")
    return ax, classifier, figure_path


# 3. Function Execution and Documentation
ax, classifier, figure_path = generate_jenks_map(state_gdf, 'RegistrationRate', 5)

print("\n--- Registration rate, before classification ---")
print(f"States: {len(state_gdf)}; range "
      f"{state_gdf['RegistrationRate'].min():.2f} to "
      f"{state_gdf['RegistrationRate'].max():.2f} %")
print(f"States whose rate was capped at 100%: {CAP}")

# The function is reusable: a second column, the same call, its own map and its own breaks.
ax_vep, classifier_vep, figure_vep = generate_jenks_map(state_gdf, 'VEP', 4)

print("\n--- File ---")
print(f"Primary map: {figure_path.relative_to(OUTPUT.parent)} "
      f"({figure_path.stat().st_size} bytes)")
print(f"Second map: {figure_vep.relative_to(OUTPUT.parent)} "
      f"({figure_vep.stat().st_size} bytes)")
print(f"Titles: {ax.get_title()!r} and {ax_vep.get_title()!r}")
