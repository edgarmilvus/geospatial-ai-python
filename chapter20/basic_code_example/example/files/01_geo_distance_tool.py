"""Chapter 20, example 1 — one Python function, exposed to an agent as a tool.

The function computes the straight-line distance between two coordinates. On its
own that is arithmetic; what the example is about is the wrapper: a Pydantic schema
that tells a model what the four arguments mean, the `@tool` decorator that turns
the function into something a model can call, and a ReAct loop that decides whether
to call it at all.

The model is configured the way every listing in this volume is configured: three
environment variables, with the endpoint and the model carrying defaults in the code
and only the key required. Without a key the listing still builds the tool, the
schema and the prompt, prints them, and exits zero.
"""

import os
import pathlib
import sys
from math import sqrt

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "~deepseek/deepseek-flash-latest"

# --- 1. The tool's input schema ---


class CoordinateInput(BaseModel):
    """The contract the model has to satisfy when it calls the tool.

    Every field carries a description, because that description is the only thing
    the model reads when it has to decide which of four numbers is the latitude.
    """

    lat1: float = Field(description="Latitude of the first point (e.g., damaged building).")
    lon1: float = Field(description="Longitude of the first point.")
    lat2: float = Field(description="Latitude of the second point (e.g., relief center).")
    lon2: float = Field(description="Longitude of the second point.")


# --- 2. The GeoAI tool ---


@tool(args_schema=CoordinateInput)
def calculate_euclidean_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the straight-line (Euclidean) distance between two coordinate pairs.

    The result is returned in degrees, the unit of the input coordinates. At this
    latitude a degree of longitude is shorter than a degree of latitude, so the
    number is a proxy for distance, not a measurement: it is enough to rank two
    relief centres, not enough to route a truck.
    """
    return sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)


GEO_TOOLS = [calculate_euclidean_distance]

# --- 3. Prompt and model ---

# A tool-calling agent needs no hand-written ReAct transcript: the framework hands
# the model the tools' JSON schemas, and the model answers with a structured call.
# The prompt therefore carries the system message, the question, and the scratchpad
# where the executor records each call and its result. Building it here rather than
# pulling one from a hub also keeps the listing runnable with no network.


SYSTEM_PROMPT = (
    "You are a specialized GeoAI Assistant tasked with rapid disaster assessment. "
    "You have access to geospatial calculation tools. Use the "
    "'calculate_euclidean_distance' tool whenever a user asks for a distance "
    "between coordinates. Be precise, and say which unit the answer is in."
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])


def build_llm():
    """The three variables: endpoint and model defaulted, key required."""
    api_key = os.environ.get("OPENAI_COMPATIBLE_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        base_url=os.environ.get("OPENAI_COMPATIBLE_BASE_URL", BASE_URL_DEFAULT),
        model=os.environ.get("OPENAI_COMPATIBLE_MODEL", MODEL_DEFAULT),
        api_key=api_key,
        temperature=0.0,
        max_tokens=600,
    )


def build_executor(llm):
    """Wire the prompt, the model and the tool into one loop."""
    agent = create_tool_calling_agent(llm, GEO_TOOLS, PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=GEO_TOOLS,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=4,
    )


# --- 4. Execution and testing ---

QUERY_WITH_TOOL = (
    "Calculate the straight-line distance between a damaged structure at "
    "(34.00, -118.00) and a relief center at (34.10, -118.10)."
)
QUERY_WITHOUT_TOOL = "Briefly describe your primary function."


def describe_tool():
    """What the model is shown, printed so the reader can see the contract."""
    schema = calculate_euclidean_distance.args
    print(f"Tool name: {calculate_euclidean_distance.name}")
    print(f"Description: {calculate_euclidean_distance.description.splitlines()[0]}")
    print(f"Arguments: {list(schema)}")
    for name, field in schema.items():
        print(f"  {name}: {field.get('description')}")
    print(f"Distance for the first query: "
          f"{calculate_euclidean_distance.invoke({'lat1': 34.0, 'lon1': -118.0, 'lat2': 34.1, 'lon2': -118.1}):.10f} degrees")


def main():
    print("--- GeoAI distance tool ---")
    describe_tool()

    llm = build_llm()
    if llm is None:
        print("\nNo OPENAI_COMPATIBLE_API_KEY in the environment, so the agent loop "
              "is not run. The tool, its schema and the prompt above are built; "
              "export the key to watch the model decide whether to call it.")
        print(f"\nQuery 1 (needs the tool): {QUERY_WITH_TOOL}")
        print(f"Query 2 (needs no tool): {QUERY_WITHOUT_TOOL}")
        return 0

    executor = build_executor(llm)

    print("\n--- Running agent query 1 (requires tool use) ---")
    result_1 = executor.invoke({"input": QUERY_WITH_TOOL})
    print(f"\n[FINAL RESPONSE 1]: {result_1['output']}")

    print("\n--- Running agent query 2 (does not require tool use) ---")
    result_2 = executor.invoke({"input": QUERY_WITHOUT_TOOL})
    print(f"\n[FINAL RESPONSE 2]: {result_2['output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
