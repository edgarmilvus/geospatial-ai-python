"""Chapter 18, exercise 5 — two tools, one planner.

The complex query needs two different capabilities in order: fetch a number that
is not in the frame, then draw the frame with that number on it. One tool answers
with data, the other with a map, and the agent has to pick the order. The listing
builds the pair and the loop; it runs the loop only when a key is present.

`initialize_agent` and `AgentType` no longer exist in current LangChain, so the
orchestration uses `create_react_agent` — the same ReAct contract, explicit tools.
"""

import os
import pathlib

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from shapely.geometry import Polygon

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "~deepseek/deepseek-flash-latest"


def build_frame():
    cells = [Polygon([(0, 0), (0, 6), (6, 6), (6, 0)]),
             Polygon([(6, 0), (6, 6), (12, 6), (12, 0)])]
    return gpd.GeoDataFrame({"city": ["Tokyo", "Osaka"], "value": [42.5, 38.0]},
                            geometry=cells, crs="EPSG:4326")


GDF = build_frame()


@tool
def external_data_fetcher(query: str) -> str:
    """Look up a single scalar for a place and metric, e.g. 'Air Quality Tokyo'."""
    # A real implementation would call an API; the exercise fixes the answer so
    # the agent's behaviour, not the service, is what gets graded.
    return f"The current value for {query} is 42.5 units."


@tool
def geo_pandas_executor(code_snippet: str) -> str:
    """Run geospatial code against the frame named `gdf`; return the outcome.

    Use `gdf` as it is: do not reload it and do not import geopandas. The code must
    end in a plotting call, and the plot it draws is saved for the reader.
    """
    scope = {"gdf": GDF, "plt": plt}
    try:
        exec(code_snippet, {"gpd": gpd, "__builtins__": __builtins__}, scope)
        if not plt.get_fignums():
            return "No figure was created. End the snippet with gdf.plot(...)."
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        plt.savefig(OUTPUT_DIR / "exercise_5_orchestration.png", bbox_inches="tight")
        plt.close()
        return "Map generated and saved to output/exercise_5_orchestration.png."
    except Exception as exc:  # noqa: BLE001 - the message is the observation
        return f"Execution failed: {type(exc).__name__}: {exc}"


TOOLS = [external_data_fetcher, geo_pandas_executor]

REACT_TEMPLATE = """Answer the question with the tools available.

{tools}

Format:

Question: {input}
Thought: what to do next
Action: one of [{tool_names}]
Action Input: the argument for that tool
Observation: what the tool returned
... (repeat as needed)
Thought: I now know the final answer
Final Answer: the answer

Stop after Action Input. Never write the Observation yourself.

Question: {input}
Thought:{agent_scratchpad}"""

PROMPT = PromptTemplate.from_template(REACT_TEMPLATE)

COMPLEX_QUERY = (
    "Find the air quality for Tokyo, then map the 'value' column of gdf and put "
    "that air quality number in the map title."
)


def build_llm():
    api_key = os.environ.get("OPENAI_COMPATIBLE_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        base_url=os.environ.get("OPENAI_COMPATIBLE_BASE_URL", BASE_URL_DEFAULT),
        model=os.environ.get("OPENAI_COMPATIBLE_MODEL", MODEL_DEFAULT),
        api_key=api_key, temperature=0.0, max_tokens=900)


def build_executor(llm):
    agent = create_react_agent(llm, TOOLS, PROMPT)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=True,
                         handle_parsing_errors=True, max_iterations=6)


if __name__ == "__main__":
    print(f"Tools the planner can choose between: {[t.name for t in TOOLS]}")
    print(f"Data tool alone: {external_data_fetcher.invoke({'query': 'Air Quality Tokyo'})}")
    solo = geo_pandas_executor.invoke({"code_snippet": "gdf.plot(column='value', legend=True)"})
    print(f"Map tool alone: {solo}")

    llm = build_llm()
    if llm is None:
        print("\nNo OPENAI_COMPATIBLE_API_KEY in the environment, so the planner "
              "is not run. Export the key to see it choose between the two tools.")
    else:
        print(f"\nUser query: {COMPLEX_QUERY}")
        result = build_executor(llm).invoke({"input": COMPLEX_QUERY})
        print(f"\n--- Final answer ---\n{result['output']}")
