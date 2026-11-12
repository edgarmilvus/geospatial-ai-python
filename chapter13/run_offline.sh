#!/usr/bin/env bash
# Chapter 13 harness suite. Run from anywhere: every path is resolved from here.
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CHAPTER_DIR/.." && pwd)"
OUTPUT="$CHAPTER_DIR/output"
LOG="$OUTPUT/run_13.log"
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
  echo "skip    chapter 13:  is not installed" | tee "$LOG"
  echo "        $PYTHON -m pip install -r $ROOT/" | tee -a "$LOG"
  echo "chapter 13: ok (skipped, optional dependency absent)" | tee -a "$LOG"
  exit 0
fi

: > "$LOG"
echo "=== chapter 13: Elevation Models - Analyzing Terrain and Slopes" | tee -a "$LOG"
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

run_harness "advanced_application_script_geoai_feature_eng/example" "run_terrain_feature_stack.py"
run_harness "basic_code_example_calculating_terrain_slope/example" "run_slope_from_dem.py"
run_harness "exercise_1/exercise" "run_resample_dem.py"
run_harness "exercise_2_comparative_analysis_of_slope_calc/exercise" "run_slope_methods.py"
run_harness "exercise_3_hydrological_feature_engineering_t/exercise" "run_twi_d8.py"
run_harness "exercise_4_the_geoai_feature_stack_modificati/exercise" "run_feature_stack.py"
run_harness "interactive_challenge_handling_cyclical_data/exercise" "run_aspect_cyclic.py"
echo "---" | tee -a "$LOG"
if [ "$fail" -ne 0 ]; then
  echo "chapter 13: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "chapter 13: ok" | tee -a "$LOG"
exit 0
