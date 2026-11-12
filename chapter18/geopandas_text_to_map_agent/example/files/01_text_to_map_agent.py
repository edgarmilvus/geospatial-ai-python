"""Chapter 18, example 2 — the Text-to-Map agent.

The pipeline is four pieces in a fixed order: a mock municipal GeoDataFrame, a
Pydantic schema the model reads, one tool that executes the code the model writes
against that frame, and a ReAct loop that alternates between them until the tool
reports a map. The listing builds all four; it runs the loop only when a key is
present, so it is safe to import from a harness and safe to run offline.

The model is configured the way every listing in this volume is configured: three
environment variables, with the endpoint and the model carrying defaults in the
code and only the key required.
"""

import os
import pathlib

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from shapely.geometry import Polygon

# --- 1. Configuration ---
# Artefacts belong to the project, not to whatever directory the script starts in.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "~deepseek/deepseek-flash-latest"

GDF_CONTEXT = None

# --- 2. Mock geospatial data and schema extraction ---


def setup_mock_geodata():
    """Five municipalities in a 3x2 block, with the density already computed.

    The geometry is a real polygon grid rather than a table of numbers, because
    the tool the model writes calls `.plot()` on it: a frame without geometry
    would make the agent fail for a reason that has nothing to do with its code.
    """
    data = {
        "municipality_id": [101, 102, 103, 104, 105],
        "name": ["Central City", "North Suburb", "South District",
                 "East Industrial", "West Residential"],
        "population": [50000, 25000, 15000, 5000, 35000],
        "area_sq_km": [50.0, 75.0, 30.0, 100.0, 45.0],
    }
    polygons = [
        Polygon([(0, 0), (0, 10), (10, 10), (10, 0)]),
        Polygon([(10, 10), (10, 20), (20, 20), (20, 10)]),
        Polygon([(0, 10), (0, 20), (10, 20), (10, 10)]),
        Polygon([(20, 0), (20, 10), (30, 10), (30, 0)]),
        Polygon([(-10, 0), (-10, 10), (0, 10), (0, 0)]),
    ]

    global GDF_CONTEXT
    GDF_CONTEXT = gpd.GeoDataFrame(data, geometry=polygons, crs="EPSG:4326")
    GDF_CONTEXT["density"] = GDF_CONTEXT["population"] / GDF_CONTEXT["area_sq_km"]

    # The schema travels to the model as text: column names and types are what a
    # generated line gets wrong when they are not in front of it. One line per
    # column, because a table of five rows wastes tokens and teaches nothing.
    lines = [f"- {column} ({str(dtype)})"
             for column, dtype in GDF_CONTEXT.dtypes.items()]
    sample = ", ".join(GDF_CONTEXT["name"].tolist())
    return "\n".join(lines) + f"\nRows: {len(GDF_CONTEXT)} municipalities ({sample})"


SCHEMA_CONTEXT = setup_mock_geodata()

# --- 3. The one tool: execute the code the model writes ---


@tool
def execute_geopandas_code(code_string: str) -> str:
    """Execute GeoPandas code against GDF_CONTEXT and save the map it draws.

    The code must plot: the tool only reports success when a figure exists, which
    is what stops the agent from answering in prose and calling it a map.
    """
    print(f"\n[AGENT ACTION] Executing GeoPandas code:\n{code_string}\n")

    scope = {"GDF_CONTEXT": GDF_CONTEXT, "plt": plt, "gpd": gpd}

    try:
        exec(code_string, globals(), scope)

        if plt.get_fignums():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = OUTPUT_DIR / "geo_agent_density_map.png"
            plt.figure(plt.gcf().number)
            if not plt.gca().get_title():
                # Models forget the title often enough that the tool supplies one.
                plt.title("Municipal Population Density Analysis")
            plt.savefig(output_path, bbox_inches="tight")
            plt.close()
            return (f"Code executed successfully. A choropleth map was generated "
                    f"and saved to output/{output_path.name}. Analysis complete.")
        return ("Code executed, but no visualization was detected. "
                "Call GDF_CONTEXT.plot(...) and try again.")

    except Exception as exc:  # noqa: BLE001 - the traceback is the observation
        # The error is the next turn's input: type and message, on one line.
        return (f"Execution Error: the GeoPandas code failed. "
                f"Error Type: {type(exc).__name__}. Message: {str(exc)[:400]}. "
                f"Review the column names and the syntax, then try again.")


# --- 4. Prompt, model, agent ---
# The ReAct template lives in the listing instead of being pulled from a hub:
# a demo that needs the network to build its prompt cannot run in an offline suite,
# and the format it defines is the part of the chapter worth reading.

REACT_TEMPLATE = """{system_context}

You have access to the following tool:

{tools}

Use exactly this format:

Question: the input you must answer
Thought: think about what to do next
Action: one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (Thought/Action/Action Input/Observation may repeat)
Thought: I now know the final answer
Final Answer: the answer to the original question

Stop after the Action Input line. Never write the Observation yourself: the
framework appends it, and a second one breaks the parser.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""


def build_llm():
    """The three variables, with the endpoint and model defaulted in code."""
    api_key = os.environ.get("OPENAI_COMPATIBLE_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        base_url=os.environ.get("OPENAI_COMPATIBLE_BASE_URL", BASE_URL_DEFAULT),
        model=os.environ.get("OPENAI_COMPATIBLE_MODEL", MODEL_DEFAULT),
        api_key=api_key,
        temperature=0.0,
        max_tokens=1200,
    )


SYSTEM_PROMPT = f"""You are a Geospatial AI agent that turns a request into GeoPandas code.
You must use the tool `execute_geopandas_code` to run the code you write.
The frame is named `GDF_CONTEXT`; do not rename it and do not reload it.
Its columns and types:
{SCHEMA_CONTEXT}
Use the column names exactly as they appear above ('density', 'name', ...).
The code you send must end in a plotting call so a map is produced."""

PROMPT = PromptTemplate.from_template(REACT_TEMPLATE).partial(
    system_context=SYSTEM_PROMPT)


def build_executor(llm):
    """Wire the prompt, the model and the tool into one ReAct loop."""
    agent = create_react_agent(llm, [execute_geopandas_code], PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=[execute_geopandas_code],
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
    )


USER_QUERY = (
    "I need a choropleth map showing the population density across all five "
    "regions. Please use the 'viridis' colormap and ensure the legend is visible."
)


def main():
    llm = build_llm()
    print("--- Text-to-Map agent ---")
    print(f"User query: {USER_QUERY}")
    if llm is None:
        print("\nNo OPENAI_COMPATIBLE_API_KEY in the environment, so the loop is "
              "not run. The frame, the schema, the prompt and the tool above are "
              "built; export the key to see the agent use them.")
        return 0

    executor = build_executor(llm)
    result = executor.invoke({"input": USER_QUERY})
    print("\n--- Final agent response ---")
    print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
