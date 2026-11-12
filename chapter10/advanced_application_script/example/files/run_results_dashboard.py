"""Harness for the advanced Dash example — one callback, two figures.

The chapter's claim is that the callback filters once and returns both a
choropleth and a time series, and that the choropleth follows the region the user
picked. The harness calls `update_dashboard` for three combinations and checks
the map's linked id, its summed area and its centre, then the chart's row count
and ordering.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def trace_values(fig):
    return fig.data[0]


def main():
    h = Harness("example 2 (Dash results monitor)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "geoai_results_dashboard.py", "results_dashboard")
        module.build_and_report()
    printed = log.getvalue()

    df = module.df
    h.equal(len(df), 100, "one hundred weekly observations are simulated")
    h.equal(sorted(df['Region'].unique().tolist()),
            ['District Alpha', 'District Beta', 'District Gamma'],
            "the three districts are present")
    h.equal(sorted(df['Feature_Type'].unique().tolist()),
            ['Deforestation', 'Infrastructure Damage', 'Urban Sprawl', 'Water Bodies'],
            "the four segmented classes are present")
    h.equal(len(module.GEOJSON_DATA['features']), 12,
            "the feature collection holds one polygon per region-class pair")

    # The counts the dashboard's default view depends on, read from the seed.
    counts = df.groupby(['Region', 'Feature_Type']).size()
    h.equal(int(counts[('District Alpha', 'Deforestation')]), 12,
            "Alpha carries 12 deforestation observations")
    h.equal(int(counts[('District Beta', 'Water Bodies')]), 11,
            "Beta carries 11 water observations")
    h.equal(int(counts[('District Gamma', 'Infrastructure Damage')]), 12,
            "Gamma carries 12 infrastructure observations")

    # The layout: two controls and two graphs, wired in that order.
    children = module.app.layout.children
    h.equal(len(children), 3, "header plus two rows make the layout")
    controls = children[1].children
    h.equal(controls[0].children[1].id, "region-selector", "the dropdown is the region control")
    h.equal(controls[1].children[1].id, "feature-selector", "the radio items are the class control")
    h.equal(controls[1].children[1].value, df['Feature_Type'].iloc[0],
            "the radio items open on the first class")
    graphs = children[2].children
    h.equal(graphs[0].children[0].id, "geoai-map", "the left graph is the map")
    h.equal(graphs[1].children[0].id, "area-chart", "the right graph is the chart")
    h.equal(len(module.app.callback_map), 1,
            "one callback drives both figures at once")

    # Call the callback directly: no server, no browser, no network.
    region, feature = 'District Beta', 'Water Bodies'
    map_fig, chart_fig = module.update_dashboard(region, feature)

    expected_rows = df[(df['Region'] == region) & (df['Feature_Type'] == feature)]
    map_trace = trace_values(map_fig)
    h.equal(len(map_trace.locations), 1, "the choropleth links one feature id")
    h.equal(map_trace.locations[0], "District Beta_Water Bodies",
            "the map id is region and class joined by an underscore")
    h.close(map_trace.z[0], round(float(expected_rows['Area_sq_km'].sum()), 6),
            "the map colours the sum of the filtered areas", tol=1e-6)
    h.equal(map_fig.layout.mapbox.style, "carto-positron", "the map keeps its base style")
    h.close(map_fig.layout.mapbox.center.lat, 40.04,
            "the view centres on Beta's latitude", tol=1e-6)
    h.close(map_fig.layout.mapbox.center.lon, -73.54,
            "the view centres on Beta's longitude", tol=1e-6)
    h.contains(map_fig.layout.title.text, "District Beta", "the map title names the district")

    chart_trace = trace_values(chart_fig)
    h.equal(len(chart_trace.x), len(expected_rows),
            "the chart plots one point per filtered observation")
    h.equal(list(chart_trace.x), list(expected_rows.sort_values('Date')['Date']),
            "the chart is ordered by acquisition date")
    h.close(sorted(chart_trace.y)[0], sorted(expected_rows['Area_sq_km'])[0],
            "the smallest plotted area is the smallest filtered area", tol=1e-9)
    h.contains(chart_fig.layout.title.text, "Water Bodies", "the chart title names the class")

    # Switching the region moves the map: the same class, another district.
    other_map, _ = module.update_dashboard('District Gamma', feature)
    h.close(other_map.layout.mapbox.center.lon, -75.04,
            "Gamma's view sits west of Beta's", tol=1e-6)
    h.equal(other_map.data[0].locations[0], "District Gamma_Water Bodies",
            "the second selection links the second district's feature")

    # The artefacts the run wrote.
    summary = json.loads(
        (module.OUTPUT_DIR / "dashboard_summary.json").read_text(encoding="utf-8"))
    h.equal(summary["rows"], 100, "the summary records the hundred rows")
    h.equal(summary["combinations"], 12, "the summary records the twelve combinations")
    h.check((module.OUTPUT_DIR / "dashboard_layout.json").exists(),
            "the run writes the layout JSON")
    h.check((module.OUTPUT_DIR / "geojson_features.json").exists(),
            "the run writes the feature collection")
    h.contains(printed, "Rows: 100; regions: 3; feature types: 4",
               "the listing reports what it simulated")

    # The seeded generator is the same generator on the next import.
    h.close(df['Area_sq_km'].iloc[0], 12.7, "the first simulated area is 12.7 sq km")
    h.close(df['Area_sq_km'].iloc[1], 29.0, "the second simulated area is 29.0 sq km")

    h.write_json("results_monitor.json", {
        "rows": len(df),
        "combinations": len(module.GEOJSON_DATA['features']),
        "selected": {"region": region, "feature": feature,
                     "rows": int(len(expected_rows)),
                     "area_sq_km": round(float(expected_rows['Area_sq_km'].sum()), 3)},
        "map_center": {"lat": round(map_fig.layout.mapbox.center.lat, 4),
                       "lon": round(map_fig.layout.mapbox.center.lon, 4)},
        "counts": counts.rename("rows").reset_index().to_dict(orient="records"),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (Dash results monitor)", FILES).crash())
