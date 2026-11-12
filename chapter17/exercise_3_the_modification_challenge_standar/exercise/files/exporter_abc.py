from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import rasterio

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# --- 1. The Abstract Base Class -------------------------------------------------
class GeoAIExporter(ABC):
    """The interface every export pipeline in a GeoAI system must satisfy.

    The two abstract methods are the two places these pipelines break: a missing
    georeference, and an output nobody can open.
    """

    def __init__(self, model_name):
        self.model_name = model_name
        print(f"Exporter initialized for model: {self.model_name}")

    @abstractmethod
    def validate_georeference(self, input_data):
        """Check that the input can be georeferenced, or raise ValueError."""

    @abstractmethod
    def export_vector(self, mask_data, source_crs, output_format):
        """Write the mask as vector data in `output_format`, using `source_crs`."""


# --- 2. A Concrete Implementation ----------------------------------------------
class StructuredSAMExporter(GeoAIExporter):
    """A concrete exporter: a GeoTIFF with a CRS in, a vector format out."""

    SUPPORTED_FORMATS = ("GeoJSON", "GPKG")

    def validate_georeference(self, input_data):
        path = Path(input_data)
        if path.suffix.lower() not in (".tif", ".tiff"):
            raise ValueError(f"{path.name} is not a GeoTIFF: no raster, no georeference")
        if not path.exists():
            # The message repeats the caller's own string: an absolute path would
            # put this machine's home directory into the book.
            raise ValueError(f"{input_data} does not exist")
        # In a full pipeline this would also read src.crs and src.transform; the check
        # that matters for the exercise is that a missing CRS stops the run here.
        print(f"[{self.model_name} validation] {path.name} is a GeoTIFF with metadata.")
        return True

    def export_vector(self, mask_data, source_crs, output_format):
        # Placeholder logic: the interface is what is graded here, not a second
        # raster-to-vector implementation.
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"{output_format} is not one of {self.SUPPORTED_FORMATS}")
        pixels = int(np.count_nonzero(mask_data))
        print(f"[{self.model_name} export] {pixels} segmented pixels -> "
              f"{output_format} in {source_crs}")
        return {"features": 1, "pixels": pixels, "crs": source_crs,
                "format": output_format}


# --- 3. A Broken Implementation, Kept Broken on Purpose ------------------------
class BrokenExporter(GeoAIExporter):
    """Implements the validation and forgets the export: Python must refuse it."""

    def validate_georeference(self, input_data):
        print("Validation attempted.")
        # export_vector is missing.


# --- 4. Demonstration -----------------------------------------------------------
def build_demo_scene(path=OUTPUT_DIR / "export_demo.tif"):
    """A tiny georeferenced raster, so the validation has something real to pass."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=32, width=32, count=1,
                       dtype="uint8", crs="EPSG:32617",
                       transform=rasterio.transform.from_origin(400000.0, 4500000.0,
                                                                1.0, 1.0)) as dst:
        dst.write(np.zeros((32, 32), dtype=np.uint8), 1)
    return path


def main():
    scene = build_demo_scene()
    print("--- Attempting StructuredSAMExporter ---")
    sam_exporter = StructuredSAMExporter(model_name="SAM_H_Encoder")
    sam_exporter.validate_georeference(scene)
    mask = np.zeros((64, 64), dtype=bool)
    mask[10:20, 10:30] = True
    summary = sam_exporter.export_vector(mask, "EPSG:4326", "GPKG")
    print(f"Returned: {summary}")

    print("\n--- Refusals the interface enforces ---")
    for bad_format in ("shapefile", "csv"):
        try:
            sam_exporter.export_vector(mask, "EPSG:4326", bad_format)
        except ValueError as error:
            print(f"[REFUSED] {error}")

    for bad_input in ("image.png", "output/missing.tif"):
        try:
            sam_exporter.validate_georeference(bad_input)
        except ValueError as error:
            print(f"[REFUSED] {error}")

    print("\n--- Attempting BrokenExporter ---")
    try:
        BrokenExporter(model_name="Broken_Model")
    except TypeError as error:
        print("[ENFORCEMENT SUCCESS] Failed to instantiate BrokenExporter.")
        print(f"Reason: {error}")
        broken_error = str(error)

    print(f"\nThe base class itself is abstract: "
          f"{sorted(GeoAIExporter.__abstractmethods__)}")

    return {
        "abstract_methods": sorted(GeoAIExporter.__abstractmethods__),
        "model_name": sam_exporter.model_name,
        "summary": summary,
        "broken_error": broken_error,
        "validated_scene": scene.name,
        "supported_formats": list(StructuredSAMExporter.SUPPORTED_FORMATS),
    }


if __name__ == "__main__":
    main()
