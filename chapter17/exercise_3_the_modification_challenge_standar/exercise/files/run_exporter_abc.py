"""Harness for exercise 3 — an interface Python enforces, not one a comment asks for.

The check is that the enforcement is real: the base class cannot be instantiated, the
concrete class can, the subclass that forgets `export_vector` is refused with a
TypeError that names the missing method, and the validation refuses a PNG and a
missing file before any export happens.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 3 (exporter ABC)", FILES)
    module = load_listing(FILES / "exporter_abc.py", "exporter_abc")
    measured = module.main()

    # --- the contract ---
    h.equal(measured["abstract_methods"], ["export_vector", "validate_georeference"],
            "the base class declares the two methods the exercise names")
    h.check(module.GeoAIExporter.__abstractmethods__ == {"validate_georeference",
                                                         "export_vector"},
            "and Python records them as abstract, not as empty bodies")
    h.raises(lambda: module.GeoAIExporter("base"), TypeError,
             "the base class itself cannot be instantiated")

    # --- a concrete subclass satisfies it ---
    exporter = module.StructuredSAMExporter(model_name="SAM_H_Encoder")
    h.equal(exporter.model_name, "SAM_H_Encoder", "the constructor stores the model name")
    h.check(isinstance(exporter, module.GeoAIExporter),
            "the concrete class is an instance of the interface")
    scene = module.OUTPUT_DIR / measured["validated_scene"]
    h.check(scene.exists(), "the demo GeoTIFF the validation reads is on disk")
    h.equal(exporter.validate_georeference(scene), True,
            "a real GeoTIFF passes the georeference check")

    # --- the export contract ---
    mask = np.zeros((64, 64), dtype=bool)
    mask[10:20, 10:30] = True
    summary = exporter.export_vector(mask, "EPSG:32617", "GeoJSON")
    h.equal(summary["pixels"], 200, "the export counts the 200 foreground pixels")
    h.equal(summary["format"], "GeoJSON", "the export echoes the format it was asked for")
    h.equal(summary["crs"], "EPSG:32617", "and the CRS it was handed")
    h.raises(lambda: exporter.export_vector(mask, "EPSG:32617", "shapefile"), ValueError,
             "a format outside the two supported ones is refused")
    h.raises(lambda: exporter.export_vector(mask, "EPSG:32617", "csv"), ValueError,
             "a second unsupported format is refused too")

    # --- the validation refuses what it should ---
    h.raises(lambda: exporter.validate_georeference("image.png"), ValueError,
             "a PNG is refused before anything is exported")
    h.raises(lambda: exporter.validate_georeference("output/missing.tif"), ValueError,
             "a missing GeoTIFF is refused with its own message")

    # --- the broken subclass cannot exist ---
    h.raises(lambda: module.BrokenExporter("Broken_Model"), TypeError,
             "a subclass without export_vector raises TypeError on construction")
    h.contains(measured["broken_error"], "abstract method export_vector",
               "the TypeError names the method that is missing")
    h.equal(sorted(module.BrokenExporter.__abstractmethods__), ["export_vector"],
            "the broken class still carries exactly one unimplemented method")

    # --- the two classes differ by one method, and that is the whole point ---
    h.check(module.StructuredSAMExporter.__abstractmethods__ == frozenset(),
            "the good subclass implements both, so it has nothing abstract left")

    h.write_json("exporter_abc.json", {
        "abstract_methods": measured["abstract_methods"],
        "model_name": measured["model_name"],
        "supported_formats": measured["supported_formats"],
        "export_summary": {"features": summary["features"], "pixels": summary["pixels"],
                           "crs": summary["crs"], "format": summary["format"]},
        "enforcement": {"broken_error": measured["broken_error"],
                        "broken_abstract_methods":
                            sorted(module.BrokenExporter.__abstractmethods__),
                        "good_abstract_methods":
                            sorted(module.StructuredSAMExporter.__abstractmethods__)},
        "refusals": ["image.png", "output/missing.tif", "shapefile", "csv"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (exporter ABC)", FILES).crash())
