"""Chapter 18, exercise 3 — the schema goes into the prompt, not around it.

A model cannot map "borough name" onto a column called `BoroName` unless it is told
that column exists. The exercise extracts the frame's schema as text and injects
it into a chat prompt with `.partial()`, so the prompt is built once from the data
and reused for every question. Nothing is called: the listing prints the rendered
prompt, which is the artefact the exercise is really about.
"""

import pathlib

import geopandas as gpd
from langchain_core.prompts import ChatPromptTemplate
from shapely.geometry import Polygon

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"


def build_frame():
    """Five boroughs: names, population, and a column whose name is easy to get wrong."""
    names = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    cells = [
        Polygon([(0, 0), (0, 4), (3, 4), (3, 0)]),
        Polygon([(3, 0), (3, 6), (7, 6), (7, 0)]),
        Polygon([(7, 0), (7, 7), (12, 7), (12, 0)]),
        Polygon([(0, 4), (0, 7), (3, 7), (3, 4)]),
        Polygon([(0, -3), (0, 0), (5, 0), (5, -3)]),
    ]
    frame = gpd.GeoDataFrame(
        {"BoroName": names, "BoroCode": [1, 3, 4, 2, 5],
         "Pop2020": [1_694_251, 2_736_074, 2_405_464, 1_472_654, 495_747]},
        geometry=cells, crs="EPSG:4326")
    frame["pop_density"] = frame["Pop2020"] / frame.geometry.area
    return frame


def get_gdf_schema_string(gdf: gpd.GeoDataFrame) -> str:
    """One line per column, type included: what the model needs and no more."""
    return "\n".join(f"- {column} ({str(dtype)})"
                     for column, dtype in gdf.dtypes.items())


SYSTEM_TEMPLATE = """You are a GIS agent. The frame is named `gdf`.
Its columns and types:
{gdf_schema}

Only use the columns listed above. A name that is not in this list does not exist.
"""


def build_prompt(frame: gpd.GeoDataFrame) -> ChatPromptTemplate:
    """The template plus the schema, injected before the first question is asked."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        ("user", "{input}"),
    ])
    return prompt.partial(gdf_schema=get_gdf_schema_string(frame))


def main():
    frame = build_frame()
    prompt = build_prompt(frame)
    question = "Map the population density by borough name using the 'plasma' colormap."

    print("--- Schema extracted from the frame ---")
    print(get_gdf_schema_string(frame))

    print("\n--- Rendered prompt, no model involved ---")
    messages = prompt.format_messages(input=question)
    print(f"[{messages[0].type}] {messages[0].content}")
    print(f"[{messages[1].type}] {messages[1].content}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rendered = OUTPUT_DIR / "rendered_prompt.txt"
    rendered.write_text("\n\n".join(f"[{m.type}] {m.content}" for m in messages),
                        encoding="utf-8")
    print(f"\nWrote output/{rendered.name}")
    return prompt


if __name__ == "__main__":
    main()
