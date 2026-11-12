#!/usr/bin/env bash
# Run every chapter suite. One line per chapter, then the totals.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$ROOT/output"
LOG="$OUTPUT/run_offline.log"
mkdir -p "$OUTPUT"

fail=0
: > "$LOG"

echo "=== the whole volume ===" | tee -a "$LOG"

while IFS= read -r suite; do
  chapter_dir="$(dirname "$suite")"
  name="$(basename "$chapter_dir")"
  if "$suite" > /dev/null 2>&1; then
    echo "$name: ok" | tee -a "$LOG"
  else
    echo "$name: FAILED" | tee -a "$LOG"
    sed -n '1,40p' "$chapter_dir/output/run_${name#chapter}.log" 2>/dev/null \
      | sed 's/^/        /' | tee -a "$LOG"
    fail=1
  fi
done < <(ls -d "$ROOT"/chapter*/run_offline.sh | sort -V)

harnesses=$(grep -hE '^[│|]? *ok ' "$ROOT"/chapter*/output/run_*.log 2>/dev/null | wc -l | tr -d ' ')
assertions=$(grep -hoE '— [0-9]+ assertions passed' "$ROOT"/chapter*/output/run_*.log 2>/dev/null \
  | grep -oE '[0-9]+' | awk '{total += $1} END {print total + 0}')
chapters=$(ls -d "$ROOT"/chapter* | wc -l | tr -d ' ')

echo "---" | tee -a "$LOG"
echo "$chapters chapters, ${harnesses:-0} harnesses, ${assertions:-0} assertions" | tee -a "$LOG"

if [ "$fail" -ne 0 ]; then
  echo "volume: FAILED" | tee -a "$LOG"
  exit 1
fi
echo "volume: ok" | tee -a "$LOG"
exit 0
