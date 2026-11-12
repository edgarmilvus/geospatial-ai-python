#!/usr/bin/env bash
# Chapter 18 harness suite. Run from anywhere: every path is resolved from here.
set -uo pipefail

CHAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CHAPTER_DIR/.." && pwd)"
OUTPUT="$CHAPTER_DIR/output"
LOG="$OUTPUT/run_18.log"
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
  echo "skip    chapter 18:  is not installed" | tee "$LOG"
  echo "        $PYTHON -m pip install -r $ROOT/" | tee -a "$LOG"
  echo "chapter 18: ok (skipped, optional dependency absent)" | tee -a "$LOG"
  exit 0
fi

: > "$LOG"
echo "=== chapter 18: Text-to-Map - Building a LangChain Agent that Generates GeoPandas Code" | tee -a "$LOG"
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

run_harness "advanced_application_script_geopandas_text_to/example" "run_text_to_map_agent.py"
run_harness "basic_code_example/example" "run_tool_schema.py"
run_harness "exercise_1_defining_the_core_geospatial_tool/exercise" "run_executor_tool.py"
run_harness "exercise_2_enforcing_reliable_output_via_pyda/exercise" "run_structured_summary.py"
run_harness "exercise_3_the_contextual_schema_challenge/exercise" "run_contextual_schema.py"
run_harness "exercise_4_execution_environment_and_safety_m/exercise" "run_execution_safety.py"
run_harness "exercise_5_interactive_challenge_tool_orchest/exercise" "run_tool_orchestration.py"
echo "---" | tee -a "$LOG"
if [ "$fail" -ne 0 ]; then
  echo "chapter 18: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "chapter 18: ok" | tee -a "$LOG"
exit 0
