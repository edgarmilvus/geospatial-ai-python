# Exercise 3 — an interface Python enforces

## What it does

Defines an abstract `GeoAIExporter` with two abstract methods, a concrete
`StructuredSAMExporter` that implements both, and a `BrokenExporter` that forgets
`export_vector` — and shows that Python refuses to instantiate the third. The validation
refuses a PNG and a missing file before any export happens.

## The listings

| file | what it is |
| --- | --- |
| `exporter_abc.py` | the solution: the ABC, the concrete class, the broken one |
| `run_exporter_abc.py` | the harness: abstract set, instantiation, refusals |

## Run it

```bash
cd chapter17/exercise_3_the_modification_challenge_standar/exercise/files
python3 exporter_abc.py
```

It writes a tiny GeoTIFF so the validation has something real, validates it, exports a demo
mask, prints four refusals and the `TypeError` the broken class raises. `run_exporter_abc.py`
asserts the abstract set, that the concrete class instantiates and validates, that four bad
inputs are refused, and that the broken subclass cannot be built; it exits non-zero when the
interface stops being enforced.

```text
--- Attempting StructuredSAMExporter ---
Exporter initialized for model: SAM_H_Encoder
[SAM_H_Encoder validation] export_demo.tif is a GeoTIFF with metadata.
[SAM_H_Encoder export] 200 segmented pixels -> GPKG in EPSG:4326
...
[ENFORCEMENT SUCCESS] Failed to instantiate BrokenExporter.
Reason: Can't instantiate abstract class BrokenExporter with abstract method export_vector

The base class itself is abstract: ['export_vector', 'validate_georeference']
```

## What it produces

| path | what it is |
| --- | --- |
| `output/export_demo.tif` | the 32 x 32 GeoTIFF the validation is run against |
| `output/exporter_abc.json` | the abstract sets, the export summary, the refusals |

## Notes

- The draft's `BrokenExporter` really did raise on construction, but the draft printed the
  success message whether or not it did: the `except TypeError` block sat around a `try` that
  also contained the good case, so a silently-passing Python would have looked the same. The
  harness asserts the `TypeError` itself, not the sentence.
- `validate_georeference` checks the suffix and the file's existence, and the message repeats
  the caller's string rather than an absolute path. A real implementation would add
  `src.crs is None`; the exercise's point is that the check exists and stops the run.
- An unsupported output format raises `ValueError` instead of printing a warning and
  returning `None`. The draft's warning left the caller with no way to know that nothing was
  written.
- `export_vector` is placeholder logic by design — the exercise is the interface, exercise 1
  is the export — and says so in a comment. Under 0.2 s.
