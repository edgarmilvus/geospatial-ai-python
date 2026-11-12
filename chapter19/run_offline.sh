#!/usr/bin/env bash
# Chapter 19 harness suite. Run from anywhere: every path is resolved from here.
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CHAPTER_DIR/.." && pwd)"
OUTPUT="$CHAPTER_DIR/output"
LOG="$OUTPUT/run_19.log"
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
  echo "skip    chapter 19: torch is not installed" | tee "$LOG"
  echo "        $PYTHON -m pip install -r $ROOT/requirements-ml.txt" | tee -a "$LOG"
  echo "chapter 19: ok (skipped, optional dependency absent)" | tee -a "$LOG"
  exit 0
fi

: > "$LOG"
echo "=== chapter 19: Traffic Prediction - Using Graph Neural Networks (GNN) on Road Networks" | tee -a "$LOG"
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

run_harness "advanced_application_script_stgcn_for_simulat/example" "run_stgcn_forward.py"
run_harness "basic_code_example_road_network_graph_initial/example" "run_road_network_graph.py"
run_harness "exercise_1/exercise" "run_graph_construction.py"
run_harness "exercise_2_implementing_the_spatio_temporal_c/exercise" "run_stconv_block.py"
run_harness "exercise_3_model_training_hyperparameter_opti/exercise" "run_train_stgcn.py"
run_harness "exercise_4_interactive_challenge_asynchronous/exercise" "run_async_stream.py"
echo "---" | tee -a "$LOG"
if [ "$fail" -ne 0 ]; then
  echo "chapter 19: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "chapter 19: ok" | tee -a "$LOG"
exit 0
