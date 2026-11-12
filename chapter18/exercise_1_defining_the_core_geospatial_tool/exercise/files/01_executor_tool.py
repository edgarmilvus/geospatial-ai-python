"""Chapter 18, exercise 1 — the executor tool the agent is allowed to call.

The tool is the whole safety surface of a Text-to-Map agent: whatever the model
writes reaches `exec`, so the tool decides which names exist and what comes back
when the code fails. This one pre-loads a GeoDataFrame and the plotting module,
runs the snippet in a scope that holds them, and returns either a success line or
the traceback — the traceback is not an error to the agent, it is the observation
that makes its next attempt smarter.
"""

import pathlib
import traceback

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from langchain_core.tools import tool
from shapely.geometry import Polygon

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"


def build_frame():
    """Six districts with a population column, built here rather than downloaded."""
    names = ["Harbour", "Midtown", "Uptown", "Riverside", "Eastfield", "Westgate"]
    populations = [120_000, 90_000, 60_000, 150_000, 40_000, 75_000]
    cells = [
        Polygon([(0, 0), (0, 10), (10, 10), (10, 0)]),
        Polygon([(10, 0), (10, 10), (20, 10), (20, 0)]),
        Polygon([(20, 0), (20, 10), (30, 10), (30, 0)]),
        Polygon([(0, 10), (0, 20), (10, 20), (10, 10)]),
        Polygon([(10, 10), (10, 20), (20, 20), (20, 10)]),
        Polygon([(20, 10), (20, 20), (30, 20), (30, 10)]),
    ]
    frame = gpd.GeoDataFrame({"district": names, "population": populations},
                             geometry=cells, crs="EPSG:4326")
    frame["density"] = frame["population"] / frame.geometry.area
    return frame


GDF = build_frame()


@tool
def geo_pandas_executor(code_snippet: str) -> str:
    """Execute geospatial code against the frame named `gdf` and report the result.

    The model must not reload data and must not import geopandas: `gdf` and `plt`
    already exist in the scope this tool hands it. The snippet has to draw
    something — a run that returns a string without a figure is a failure here,
    because the deliverable is a map.
    """
    scope = {"gdf": GDF, "plt": plt}
    try:
        exec(code_snippet, {"gpd": gpd, "__builtins__": __builtins__}, scope)
        if not plt.get_fignums():
            return "Execution finished but no figure was created. Call gdf.plot()."
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        target = OUTPUT_DIR / "exercise_1_districts.png"
        plt.savefig(target, bbox_inches="tight")
        plt.close()
        return f"Visualization created successfully and saved to output/{target.name}."
    except Exception:  # noqa: BLE001 - the traceback is the observation
        return f"Execution failed:\n{traceback.format_exc()}"


if __name__ == "__main__":
    print(f"Frame: {len(GDF)} districts, columns {list(GDF.columns)}")
    print(f"Tool: {geo_pandas_executor.name}")
    print("\n--- What the model would send ---")
    snippet = "gdf.plot(column='density', legend=True, cmap='viridis')"
    print(snippet)
    print("\n--- What the tool returns ---")
    print(geo_pandas_executor.invoke({"code_snippet": snippet}))
