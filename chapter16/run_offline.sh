#!/usr/bin/env bash
# Chapter 16 harness suite. Run from anywhere: every path is resolved from here.
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CHAPTER_DIR/.." && pwd)"
OUTPUT="$CHAPTER_DIR/output"
LOG="$OUTPUT/run_16.log"
mkdir -p "$OUTPUT"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [ -n "${PYTHON:-}" ]; then
  PYTHON="$PYTHON"
else
  PYTHON="python3"
fi

fail=0

if [ -n "torch" ] && ! "$PYTHON" -c "import torch" >/dev/null 2>&1; then
  echo "skip    chapter 16: torch is not installed" | tee "$LOG"
  echo "        $PYTHON -m pip install -r $ROOT/requirements-ml.txt" | tee -a "$LOG"
  echo "chapter 16: ok (skipped, optional dependency absent)" | tee -a "$LOG"
  exit 0
fi

: > "$LOG"
echo "=== chapter 16: Deep Learning on Maps - Detecting Buildings with PyTorch" | tee -a "$LOG"
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

run_harness "raster_to_vector_building_detection/example" "run_raster_to_vector_pipeline.py"
run_harness "simulating_and_visualizing_segmentation_data/example" "run_simulate_segmentation_pair.py"
run_harness "exercise_1_optimized_data_pipeline_for_large/exercise" "run_tiled_dataset.py"
run_harness "exercise_2_modifying_u_net_for_enhanced_featu/exercise" "run_se_unet.py"
run_harness "exercise_3_advanced_evaluation_and_optimal_th/exercise" "run_threshold_optimization.py"
run_harness "exercise_4_vectorization_and_attribute_assign/exercise" "run_raster_to_vector.py"
run_harness "exercise_5_geoai_agent_tooling_and_database_i/exercise" "run_building_database.py"
echo "---" | tee -a "$LOG"
if [ "$fail" -ne 0 ]; then
  echo "chapter 16: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "chapter 16: ok" | tee -a "$LOG"
exit 0
