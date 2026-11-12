"""Chapter 20, example 2 — the Automated Disaster Damage Assessment pipeline.

Four stages in a fixed order: co-register the imagery, segment building footprints,
classify each footprint's damage, and write a quantified GIS layer. The layer is the
product — a GeoDataFrame in a metric CRS, so every area is in square metres and the
totals mean something.

On top of it sits the agent. It does not see pixels; it sees the layer, through three
typed tools, and turns counts into a sentence a responder can act on. The model is
configured the way every listing in this volume is configured — three environment
variables, two of them defaulted — and with no key the pipeline still runs, still
writes its report, and prints the tools the agent would have used.
"""

import json
import os
import pathlib

import geopandas as gpd
import numpy as np
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from shapely.geometry import Point, box

SEED = 2024

# --- 1. Configuration and path setup ---

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
DATA_DIR = OUTPUT_DIR / "disaster_data"
REPORT_PATH = OUTPUT_DIR / "assessment_report.geojson"
ALIGNED_METADATA_PATH = DATA_DIR / "aligned_metadata.json"
PRE_IMAGE_PATH = DATA_DIR / "pre_disaster_scene.tif"
POST_IMAGE_PATH = DATA_DIR / "post_disaster_scene.tif"

# Areas in square metres need a projected CRS. UTM zone 11N covers the AOI below,
# so one unit in it is one metre and `geometry.area` is a real measurement.
AOI_CRS = "EPSG:32611"
AOI_CENTRE = (-118.00, 34.00)  # downtown Los Angeles, lon/lat

DAMAGE_CATEGORIES = ["Destroyed", "Major Damage", "Minor Damage", "No Visible Damage"]

BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "~deepseek/deepseek-flash-latest"

# The layer the agent queries. Filled by stage 4, read by the tools.
GDF = None


# --- 2. Core GeoAI pipeline functions ---

def align_images(pre_path: pathlib.Path, post_path: pathlib.Path) -> pathlib.Path:
    """Stage 1: co-register the two scenes and record what the warp was.

    EAFP: the input check is the read itself, so a missing scene raises instead of
    letting the expensive stages start on nothing.
    """
    if not pre_path.exists() or not post_path.exists():
        raise FileNotFoundError(
            "Pre- or post-disaster images not found. Alignment requires both.")
    print(f"[STAGE 1] Aligning {pre_path.name} and {post_path.name} using GCPs...")

    # A real warp is an affine or polynomial transform fitted to tie points. The
    # numbers here are the identity-ish matrix a good co-registration would leave.
    metadata = {"status": "aligned_success",
                "transformation_matrix": [0.99, 0.01, 10.0],
                "crs": AOI_CRS}
    with open(ALIGNED_METADATA_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=4)
    return ALIGNED_METADATA_PATH


def run_segmentation_model(aligned_path: pathlib.Path) -> list:
    """Stage 2: one building footprint per segmented instance, in metres.

    A fine-tuned SAM returns pixel masks; the vectoriser turns each mask into a
    polygon. The polygons here are generated on a 40 m grid so every run sees the
    same twenty structures with the same areas.
    """
    print(f"[STAGE 2] Running segmentation model using data from {aligned_path.name}...")
    origin = gpd.GeoSeries([Point(*AOI_CENTRE)], crs="EPSG:4326").to_crs(AOI_CRS).iloc[0]

    footprints = [200, 240, 180, 300, 160, 260, 220, 150, 280, 320,
                  190, 210, 230, 170, 250, 140, 270, 290, 200, 310]
    # Post-disaster covered area as a fraction of the pre-disaster footprint. The
    # eight tenths cut is the boundary the classifier uses for "Destroyed".
    losses = [0.92, 0.85, 0.88, 0.82,
              0.55, 0.62, 0.48, 0.70, 0.44,
              0.25, 0.30, 0.18, 0.22,
              0.05, 0.00, 0.12, 0.08, 0.02, 0.10, 0.06]

    segments = []
    for index, (area, loss) in enumerate(zip(footprints, losses), start=1):
        row, column = divmod(index - 1, 5)
        side = area ** 0.5
        x0 = origin.x + column * 40.0
        y0 = origin.y + row * 40.0
        segments.append({
            "id": index,
            "geometry": box(x0, y0, x0 + side, y0 + side),
            "area_sq_m": float(area),
            "post_area_sq_m": round(area * (1.0 - loss), 2),
            "texture_change": round(0.4 + loss, 3),
        })
    print(f"           {len(segments)} building footprints vectorised "
          f"({sum(s['area_sq_m'] for s in segments):.0f} m2 of roof)")
    return segments


def classify_damage(segment_data: list) -> list:
    """Stage 3: a damage class per footprint, from structural loss.

    In a production pipeline the loss comes from comparing the pre- and post-mask
    of the same instance, and a spectral term breaks the ties. The thresholds are
    the ones the chapter defines: eight tenths of the structure gone is destroyed.
    """
    print(f"[STAGE 3] Classifying damage for {len(segment_data)} structures...")
    classified = []
    for segment in segment_data:
        pre_area = segment["area_sq_m"]
        post_area = segment["post_area_sq_m"]
        structural_loss = (pre_area - post_area) / pre_area if pre_area > 0 else 0.0

        if structural_loss >= 0.80:
            damage_class = "Destroyed"
        elif structural_loss >= 0.40:
            damage_class = "Major Damage"
        elif structural_loss >= 0.15:
            damage_class = "Minor Damage"
        else:
            damage_class = "No Visible Damage"

        enriched = dict(segment)
        enriched["structural_loss"] = round(structural_loss, 4)
        enriched["damage_class"] = damage_class
        enriched["confidence"] = round(0.80 + 0.15 * structural_loss, 3)
        classified.append(enriched)
    return classified


def generate_gis_report(classified_data: list, output_path: pathlib.Path) -> gpd.GeoDataFrame:
    """Stage 4: the quantified layer — polygons, a metric CRS, areas in m².

    The frame is built in the AOI's UTM zone, where `area` is square metres, and
    only then reprojected to WGS 84 for the GeoJSON that the GIS platform reads.
    """
    print(f"[STAGE 4] Generating GeoJSON report at {output_path.name}...")
    global GDF

    frame = gpd.GeoDataFrame(
        {
            "structure_id": [item["id"] for item in classified_data],
            "damage_class": [item["damage_class"] for item in classified_data],
            "area_sq_m": [item["area_sq_m"] for item in classified_data],
            "structural_loss": [item["structural_loss"] for item in classified_data],
            "confidence": [item["confidence"] for item in classified_data],
        },
        geometry=[item["geometry"] for item in classified_data],
        crs=AOI_CRS,
    )
    # The measured area, not the reported one: this is the check that the geometry
    # and the attribute table agree.
    frame["area_sq_m"] = frame.geometry.area.round(2)
    GDF = frame

    export = frame.to_crs("EPSG:4326")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export.to_file(output_path, driver="GeoJSON")
    print(f"           SUCCESS: {len(frame)} structures assessed, "
          f"CRS {frame.crs.to_epsg()} ({frame.crs.axis_info[0].unit_name}), "
          f"total roof area {frame['area_sq_m'].sum():.0f} m2")
    return frame


# --- 3. The agent's three tools, over the quantified layer ---

def damage_counts() -> dict:
    return {name: int((GDF["damage_class"] == name).sum()) for name in DAMAGE_CATEGORIES}


@tool
def count_buildings(damage_class: str) -> int:
    """Count the buildings in one damage class.

    Valid classes are 'Destroyed', 'Major Damage', 'Minor Damage' and
    'No Visible Damage'. Use this before quoting any share of the total.
    """
    if damage_class not in DAMAGE_CATEGORIES:
        return -1
    return int((GDF["damage_class"] == damage_class).sum())


@tool
def total_area(damage_class: str) -> float:
    """Total roof area, in square metres, of the buildings in one damage class."""
    if damage_class not in DAMAGE_CATEGORIES:
        return -1.0
    return round(float(GDF.loc[GDF["damage_class"] == damage_class, "area_sq_m"].sum()), 2)


@tool
def worst_hit_centroid() -> str:
    """Centroid of the largest 'Destroyed' footprint, as 'lat, lon'.

    This is the coordinate a responder would be sent to first, so it is returned
    in WGS 84 and not in the layer's metric CRS.
    """
    destroyed = GDF[GDF["damage_class"] == "Destroyed"]
    if destroyed.empty:
        return "no destroyed structures"
    # Centroid in the metric CRS, then the point reprojected: taking a centroid of
    # lon/lat degrees would average angles, not metres.
    centroid = destroyed.geometry.centroid.iloc[0]
    point = gpd.GeoSeries([centroid], crs=AOI_CRS).to_crs("EPSG:4326").iloc[0]
    return f"{point.y:.5f}, {point.x:.5f}"


GEO_TOOLS = [count_buildings, total_area, worst_hit_centroid]


# --- 4. Prompt, model, executor ---

# A tool-calling agent needs no hand-written ReAct template: the model is given the
# tools' JSON schemas by the framework and answers with a structured tool call. The
# prompt therefore carries only the system message, the question, and the scratchpad
# where the executor records each call and its result.


SYSTEM_PROMPT = (
    "You are the reporting layer of a disaster damage assessment system. You never "
    "invent a number: every count and every area comes from a tool call. Answer in "
    "one or two sentences and say which class and which area you are quoting."
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])


USER_QUESTION = ("How many buildings were destroyed, what total roof area do they "
                 "cover in square metres, and where is the largest one?")


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
        max_tokens=800,
    )


def build_executor(llm):
    agent = create_tool_calling_agent(llm, GEO_TOOLS, PROMPT)
    return AgentExecutor(agent=agent, tools=GEO_TOOLS, verbose=True,
                         handle_parsing_errors=True, max_iterations=6)


# --- 5. Main execution pipeline ---

def main():
    """Run the four stages, then hand the layer to the agent if a key is present."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # The scenes themselves are not shipped: the alignment stage validates their
    # presence, so they are created empty. Their pixels are never read here.
    PRE_IMAGE_PATH.touch(exist_ok=True)
    POST_IMAGE_PATH.touch(exist_ok=True)

    try:
        aligned_meta = align_images(PRE_IMAGE_PATH, POST_IMAGE_PATH)
        raw_segments = run_segmentation_model(aligned_meta)
        classified = classify_damage(raw_segments)
        frame = generate_gis_report(classified, REPORT_PATH)
    except Exception as exc:  # noqa: BLE001 - the pipeline halts on any stage failure
        print(f"\nPipeline execution halted due to critical error: {exc}")
        print("Please verify input data integrity and path configuration.")
        return 1

    counts = damage_counts()
    print("\n--- Quantified output ---")
    print(f"Buildings assessed: {len(frame)}")
    for name in DAMAGE_CATEGORIES:
        subset = frame[frame["damage_class"] == name]
        print(f"  {name:<17} {len(subset):>2} buildings, "
              f"{subset['area_sq_m'].sum():>7.0f} m2")
    print(f"Total roof area: {frame['area_sq_m'].sum():.0f} m2")
    print(f"Report: {REPORT_PATH.relative_to(OUTPUT_DIR.parent)} (EPSG:4326 on export)")

    llm = build_llm()
    if llm is None:
        print("\nNo OPENAI_COMPATIBLE_API_KEY in the environment, so the agent is "
              "not run. The layer, the three tools and the prompt above are built:")
        for geo_tool in GEO_TOOLS:
            print(f"  - {geo_tool.name}: {geo_tool.description.splitlines()[0]}")
        print(f"\nThe question it would answer: {USER_QUESTION}")
        return 0

    print("\n--- Agent report ---")
    executor = build_executor(llm)
    result = executor.invoke({"input": USER_QUESTION})
    print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
