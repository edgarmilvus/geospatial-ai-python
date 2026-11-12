"""Chapter 18, exercise 4 — an executor that turns failure into instruction.

The difference between a tool an agent can recover from and one it cannot is what
happens after the first bad line. This executor catches the exception, reads the
traceback, and answers with the last frames of it plus the frames of the caller's
code — which is the part the model can act on. It also counts its own failures, so
the loop can be stopped instead of retried forever.
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
MAX_FAILURES = 3

STATE = {"attempts": 0, "failures": 0}


def build_frame():
    cells = [Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
             Polygon([(5, 0), (5, 5), (10, 5), (10, 0)])]
    frame = gpd.GeoDataFrame({"zone": ["North", "South"], "value": [12, 31]},
                             geometry=cells, crs="EPSG:4326")
    return frame


GDF = build_frame()


def summarise_traceback(text: str, keep: int = 3) -> str:
    """The last frames of a traceback, which is the part a model can fix."""
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return "\n".join(lines[-keep:])


@tool
def robust_geo_pandas_executor(code_snippet: str) -> str:
    """Run geospatial code against `gdf`; on failure, return a fixable observation."""
    STATE["attempts"] += 1
    scope = {"gdf": GDF, "plt": plt}
    try:
        exec(code_snippet, {"gpd": gpd, "__builtins__": __builtins__}, scope)
        if not plt.get_fignums():
            STATE["failures"] += 1
            return ("No figure was created. The code must call gdf.plot(...) "
                    "before it finishes.")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        target = OUTPUT_DIR / "exercise_4_recovery.png"
        plt.savefig(target, bbox_inches="tight")
        plt.close()
        STATE["failures"] = 0
        return f"Success: the map was saved to output/{target.name}."
    except Exception:  # noqa: BLE001 - the traceback is the observation
        STATE["failures"] += 1
        detail = summarise_traceback(traceback.format_exc())
        if STATE["failures"] >= MAX_FAILURES:
            return (f"Giving up after {STATE['failures']} failed attempts. "
                    f"Last error:\n{detail}")
        return (f"OBSERVATION: the code failed. Error:\n{detail}\n"
                f"FIX: use the column names from gdf ({list(GDF.columns)}) and "
                f"call gdf.plot(column=...).")


if __name__ == "__main__":
    print(f"Columns available to the model: {list(GDF.columns)}")

    bad = "gdf.plot(column='populaton', legend=True)"     # misspelled on purpose
    print("\n--- First attempt (a typo the model has to learn from) ---")
    print(robust_geo_pandas_executor.invoke({"code_snippet": bad}))

    good = "gdf.plot(column='value', legend=True, cmap='plasma')"
    print("\n--- Second attempt (corrected) ---")
    print(robust_geo_pandas_executor.invoke({"code_snippet": good}))

    print(f"\nattempts={STATE['attempts']} failures_left_counter={STATE['failures']}")
