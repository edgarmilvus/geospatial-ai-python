"""Harness for chapter 20, example 2 — the pipeline's numbers and the agent's calls.

Two halves. The first drives the four stages and checks what a damage assessment
has to get right: twenty structures, four of them destroyed, 920 m² of destroyed
roof, an area total that matches the geometry, and a layer whose CRS is metric while
its export is WGS 84. The second replaces the model with a script and checks that the
agent actually called the tools rather than producing the same numbers out of thin
air.
"""
import contextlib
import io
import json
import os
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

def main():
    h = Harness("example 2 (ADDA pipeline)", FILES)
    # The run below asserts what the listing does when *no* key is exported, so the
    # harness clears the three variables itself. A harness that reads them from the
    # shell tests the environment, and passes only on a machine that has never used
    # the book — which is the one machine that is not the reader's.
    saved = {name: os.environ.pop(name, None)
             for name in ("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL",
                          "OPENAI_COMPATIBLE_MODEL")}
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_adda_pipeline.py", "adda_pipeline")
        status = module.main()
    printed = log.getvalue()

    import geopandas as gpd

    h.equal(status, 0, "with no key the pipeline runs its stages and exits zero")

    frame = module.GDF
    h.equal(len(frame), 20, "twenty segmented footprints become twenty rows")
    h.equal(frame.crs.to_epsg(), 32611,
            "the working layer is in a metric CRS, so area is square metres")
    h.equal(frame.crs.axis_info[0].unit_name, "metre", "one unit in the layer is one metre")
    h.check(frame.geometry.is_valid.all(), "every polygon is valid geometry")

    # --- the classification the chapter defines ---
    counts = module.damage_counts()
    h.equal(counts["Destroyed"], 4, "four footprints lost at least 80% of their area")
    h.equal(counts["Major Damage"], 5, "five lost between 40% and 80%")
    h.equal(counts["Minor Damage"], 4, "four lost between 15% and 40%")
    h.equal(counts["No Visible Damage"], 7, "seven lost almost nothing")
    h.equal(sum(counts.values()), 20, "every building lands in exactly one class")

    destroyed = frame[frame["damage_class"] == "Destroyed"]
    h.close(float(destroyed["area_sq_m"].sum()), 920.0, tol=0.01,
            message="the destroyed buildings cover 920 m2 of roof")
    h.close(float(frame["area_sq_m"].sum()), 4570.0, tol=0.01,
            message="all twenty roofs cover 4 570 m2")
    h.check(bool((frame["area_sq_m"] > 0).all()), "no footprint has a zero area")
    h.check(bool((frame["structural_loss"] >= 0).all()
                 and (frame["structural_loss"] < 1).all()),
            "structural loss is a fraction in [0, 1)")
    h.check(bool((frame["confidence"] <= 0.95).all()),
            "confidence stays below certainty: a classifier that is never wrong is wrong")

    # --- the export ---
    exported = gpd.read_file(module.REPORT_PATH)
    h.equal(len(exported), 20, "the GeoJSON carries every feature")
    h.equal(exported.crs.to_epsg(), 4326, "the exported layer is WGS 84, as GIS expects")
    h.equal(list(exported["damage_class"].value_counts().sort_index()),
            [4, 5, 4, 7], "the classes survive the round trip in name order")

    # --- the tools, called directly ---
    h.equal(module.count_buildings.invoke({"damage_class": "Destroyed"}), 4,
            "the count tool agrees with the frame")
    h.close(module.total_area.invoke({"damage_class": "Destroyed"}), 920.0, tol=0.01,
            message="the area tool agrees with the frame")
    centroid = module.worst_hit_centroid.invoke({})
    latitude, longitude = (float(part) for part in centroid.split(", "))
    h.check(33.9 < latitude < 34.1, "the worst-hit centroid is at the AOI's latitude (%.5f)" % latitude)
    h.check(-118.1 < longitude < -117.9, "and at its longitude (%.5f)" % longitude)

    # --- the agent, driven by a script ---
    h.check(module.build_llm() is None, "no key in this process, so no client")
    h.check("gpt" not in module.SYSTEM_PROMPT.lower(),
            "the system prompt names no provider-specific model")

    sys.path.insert(0, str(ROOT / "tools"))
    from fake_tool_calling import ScriptedToolCallingModel

    fake = ScriptedToolCallingModel(
        [("count_buildings", {"damage_class": "Destroyed"}),
         ("total_area", {"damage_class": "Destroyed"}),
         ("worst_hit_centroid", {"damage_class": "Destroyed"})],
        final="Four buildings are Destroyed, covering 920.0 square metres of roof; "
              "the largest sits near 34.00006, -117.99992.",
    )
    executor = module.build_executor(fake)
    with contextlib.redirect_stdout(log):
        result = executor.invoke({"input": module.USER_QUESTION})
    trace = log.getvalue()
    answer = result["output"]

    h.contains(trace, "count_buildings", "the agent called the counting tool")
    h.contains(trace, "total_area", "the agent called the area tool")
    h.contains(trace, "worst_hit_centroid", "the agent called the location tool")
    h.equal(trace.count("> Entering new AgentExecutor chain"), 1,
            "one agent run: the listing skipped its own because there is no key")
    h.contains(answer, "920", "the final answer quotes the measured area")

    h.contains(printed, "SUCCESS: 20 structures assessed", "the pipeline reports its size")
    h.contains(printed, "Total roof area: 4570 m2", "the run prints the quantified total")
    h.contains(printed, "No OPENAI_COMPATIBLE_API_KEY", "the run says why it stopped")

    # Put the shell's environment back before returning; the assertions above ran
    # with it cleared, which is the state they are about.
    for name, value in saved.items():
        if value is not None:
            os.environ[name] = value

    h.write_json("adda_pipeline.json", {
        "structures": int(len(frame)),
        "crs": frame.crs.to_epsg(),
        "export_crs": exported.crs.to_epsg(),
        "counts": counts,
        "area_by_class": {name: round(float(frame.loc[frame["damage_class"] == name,
                                                      "area_sq_m"].sum()), 2)
                          for name in module.DAMAGE_CATEGORIES},
        "total_area_sq_m": round(float(frame["area_sq_m"].sum()), 2),
        "destroyed_centroid": centroid,
        "agent_answer": answer[:200],
        "tools_called": 3,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (ADDA pipeline)", FILES).crash())
