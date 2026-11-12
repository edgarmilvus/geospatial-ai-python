#!/usr/bin/env bash
# Chapter 11 harness suite. Run from anywhere: every path is resolved from here.
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CHAPTER_DIR/.." && pwd)"
OUTPUT="$CHAPTER_DIR/output"
LOG="$OUTPUT/run_11.log"
mkdir -p "$OUTPUT"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [ -n "${PYTHON:-}" ]; then
  PYTHON="$PYTHON"
else
  PYTHON="python3"
fi

fail=0

if [ -n "" ] && ! "$PYTHON" -c "import " >/dev/null 2>&1; then
  echo "skip    chapter 11:  is not installed" | tee "$LOG"
  echo "        $PYTHON -m pip install -r $ROOT/" | tee -a "$LOG"
  echo "chapter 11: ok (skipped, optional dependency absent)" | tee -a "$LOG"
  exit 0
fi

: > "$LOG"
echo "=== chapter 11: Introduction to Rasterio - Reading Satellite Imagery" | tee -a "$LOG"
echo "    python: $("$PYTHON" -V 2>&1)" | tee -a "$LOG"

run_harness() {
  local project="$1"
  local harness="$2"
  local dir="$CHAPTER_DIR/$project"
  local log="$dir/output/harness.log"
  mkdir -p "$dir/output"
  if ( cd "$dir" && "$PYTHON" "files/$harness" ) > "$log" 2>&1; then
    verdict=$(grep -E '^__VERDICT__ 0 ' "$log" | tail -n 1)
    if [ -n "$verdict" ]; then
      count=$(echo "$verdict" | awk '{print $3}')
      if [ "$count" = "0" ] && grep -qE '^skip    ' "$log"; then
        reason=$(grep -E '^skip    ' "$log" | head -n 1)
        echo "$reason" | tee -a "$LOG"
      else
        echo "ok      $project — $count assertions passed" | tee -a "$LOG"
      fi
    else
      echo "FAILED  $project (no verdict line)" | tee -a "$LOG"
      sed -n '1,20p' "$log" | sed 's/^/        /' | tee -a "$LOG"
      fail=1
    fi
  else
    echo "FAILED  $project" | tee -a "$LOG"
    sed -n '1,20p' "$log" | sed 's/^/        /' | tee -a "$LOG"
    fail=1
  fi
}

run_harness "advanced_application_script_efficient_geochip/example" "run_geochip.py"
run_harness "basic_code_example_reading_core_satellite_met/example" "run_read_scene_metadata.py"
run_harness "exercise_1/exercise" "run_metadata_deep_dive.py"
run_harness "exercise_2_efficient_windowed_reading_and_arr/exercise" "run_windowed_tile.py"
run_harness "exercise_3_advanced_modification_challenge_si/exercise" "run_downsample.py"
run_harness "exercise_4_interactive_band_selection_and_err/exercise" "run_band_selection.py"
run_harness "exercise_5_creating_a_geotiff_template_for_ge/exercise" "run_classification_template.py"
echo "---" | tee -a "$LOG"
if [ "$fail" -ne 0 ]; then
  echo "chapter 11: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "chapter 11: ok" | tee -a "$LOG"
exit 0
