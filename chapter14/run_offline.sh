#!/usr/bin/env bash
# Chapter 14 harness suite. Run from anywhere: every path is resolved from here.
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CHAPTER_DIR/.." && pwd)"
OUTPUT="$CHAPTER_DIR/output"
LOG="$OUTPUT/run_14.log"
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
  echo "skip    chapter 14:  is not installed" | tee "$LOG"
  echo "        $PYTHON -m pip install -r $ROOT/" | tee -a "$LOG"
  echo "chapter 14: ok (skipped, optional dependency absent)" | tee -a "$LOG"
  exit 0
fi

: > "$LOG"
echo "=== chapter 14: Masking and Clipping - Extracting Region of Interest" | tee -a "$LOG"
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

run_harness "2_basic_code_example_in_memory_raster_clippin/example" "run_in_memory_clip.py"
run_harness "advanced_application_script_multi_modal_geoai/example" "run_multi_modal_preparation.py"
run_harness "exercise_1/exercise" "run_clip_raster_by_vector.py"
run_harness "exercise_2_vector_clipping_with_attribute_int/exercise" "run_attribute_integrity.py"
run_harness "exercise_3_advanced_modification_challenge_co/exercise" "run_cli_preprocessor.py"
run_harness "exercise_4_interactive_challenge_dynamic_meta/exercise" "run_clean_profile.py"
run_harness "exercise_5_multi_roi_batch_clipping_simulatio/exercise" "run_batch_clip_rois.py"
echo "---" | tee -a "$LOG"
if [ "$fail" -ne 0 ]; then
  echo "chapter 14: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "chapter 14: ok" | tee -a "$LOG"
exit 0
