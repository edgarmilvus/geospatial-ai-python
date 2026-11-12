"""Chapter 18, example 1 — one tool, one schema, one simulated call.

A function that computes a centroid, the Pydantic model that describes its input
to a language model, and the `StructuredTool` that joins the two. Nothing here
calls a model: the script plays the model's part by handing the tool the argument
dictionary the schema defines, which is exactly what the framework does after it
has parsed the model's output.
"""

import json

import geopandas as gpd
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


# --- 1. The schema the model reads ---
class CentroidInputSchema(BaseModel):
    """The arguments `calculate_geometry_centroid` accepts, with their descriptions."""

    wkt_polygon: str = Field(
        description=(
            "A polygon in Well-Known Text, for example "
            "'POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))'."
        )
    )


# --- 2. The geospatial work ---
def calculate_geometry_centroid(wkt_polygon: str) -> str:
    """Return the centroid of a WKT polygon as a JSON string.

    The return value is JSON rather than a tuple because the next reader of it is
    a model: a string it can quote back is worth more than an object it cannot see.
    The error branch returns JSON too, so a caller parses one shape in both cases.
    """
    try:
        series = gpd.GeoSeries.from_wkt([wkt_polygon])
        centroid = series.centroid.iloc[0]
        return json.dumps({
            "input_wkt": wkt_polygon,
            "centroid_x": centroid.x,
            "centroid_y": centroid.y,
            "wkt_output": centroid.wkt,
        }, indent=2)
    except Exception as exc:  # noqa: BLE001 - the message is the observation
        return json.dumps({"error": f"Failed to calculate centroid: {exc}"})


# --- 3. The tool: function plus schema ---
centroid_tool = StructuredTool.from_function(
    func=calculate_geometry_centroid,
    name="calculate_geometry_centroid",
    description=(
        "Find the precise central point of any valid polygon given as WKT. "
        "Use this before labelling a region, not after."
    ),
    args_schema=CentroidInputSchema,
)

# --- 4. A simulated agent call ---
TEST_WKT = "POLYGON ((-74.01 40.71, -74.02 40.71, -74.02 40.72, -74.01 40.72, -74.01 40.71))"


def main():
    print("--- Text-to-Map tool definition complete ---")
    print(f"Tool name: {centroid_tool.name}")
    print(f"Description length: {len(centroid_tool.description)} characters")
    print(f"Schema fields: {list(CentroidInputSchema.model_fields)}")

    print("\n--- Simulating an agent call ---")
    result_json = centroid_tool.invoke({"wkt_polygon": TEST_WKT})
    print(result_json)

    parsed = json.loads(result_json)
    print("--- Verification ---")
    print(f"Centroid X (longitude): {parsed['centroid_x']:.6f}")
    print(f"Centroid Y (latitude):  {parsed['centroid_y']:.6f}")
    return parsed


if __name__ == "__main__":
    main()
