#!/usr/bin/env bash
# Run every check the book ships, in the order that fails fastest:
#   1. the offline suite (no key, no network)
#   2. the model-free service checks, skipped when the service is absent
#   3. with --live, the live run (costs money, manual only)
#
# A check whose extra is missing prints what to install and is skipped, so this
# script is safe on a machine that has nothing optional: it reports what it could
# not run instead of failing a chapter that is not broken.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi

LIVE=0
for arg in "$@"; do
  case "$arg" in
    --live) LIVE=1 ;;
    -h|--help)
      awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *)
      echo "unknown option: $arg (try --live or --help)" >&2
      exit 2
      ;;
  esac
done

fail=0
skipped=()

section() {
  printf '\n=== %s ===\n' "$1"
}

section "1/3 offline suite"
if "$ROOT/run_offline.sh"; then
  :
else
  fail=1
fi

section "2/3 optional extras"
# Chapter 16 trains a U-Net and chapter 19 a graph network. Both are skipped, not
# failed, when torch is not installed: everything else still runs.
if "$PYTHON" -c "import torch" >/dev/null 2>&1; then
  if ! "$ROOT/chapter16/run_offline.sh" >/dev/null 2>&1; then
    echo "chapter16: FAILED under torch"
    fail=1
  else
    echo "torch present: chapter 16 and 19 ran with it"
  fi
else
  echo "skipped: torch is not installed"
  echo "  \"$PYTHON\" -m pip install -r \"$ROOT/requirements-ml.txt\""
  skipped+=("torch rows (no torch)")
fi

if [ "$LIVE" = 1 ]; then
  section "3/3 live run"
  if [ -z "${OPENAI_COMPATIBLE_API_KEY:-}" ]; then
    echo "skipped: OPENAI_COMPATIBLE_API_KEY is not set"
    echo '  export OPENAI_COMPATIBLE_API_KEY="..."  # then rerun with --live'
    skipped+=("live run (no key)")
  elif ! "$ROOT/run_live.sh"; then
    fail=1
  fi
else
  section "3/3 live run"
  echo "skipped: pass --live to run it (the rows need a key and cost money)"
  skipped+=("live run (needs --live)")
fi

printf '\n---\n'
if [ "$fail" -ne 0 ]; then
  echo "everything: FAILED"
else
  echo "everything: ok"
fi
if [ "${#skipped[@]}" -gt 0 ]; then
  printf 'not run: %s\n' "$(IFS=', '; echo "${skipped[*]}")"
fi
exit "$fail"
