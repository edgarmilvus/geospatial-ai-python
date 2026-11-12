#!/usr/bin/env bash
# Run the model-calling listings against a real API. Costs money, so it is manual.
#
# The three variables are all the runner needs and all the listings read. Nothing
# is read from a file and no provider is chosen here:
#
#   export OPENAI_COMPATIBLE_API_KEY="..."
#   export OPENAI_COMPATIBLE_BASE_URL="https://openrouter.ai/api/v1"   # the default
#   export OPENAI_COMPATIBLE_MODEL="~deepseek/deepseek-flash-latest"   # the default
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi

if [ -z "${OPENAI_COMPATIBLE_API_KEY:-}" ]; then
  echo "missing OPENAI_COMPATIBLE_API_KEY" >&2
  echo '  export OPENAI_COMPATIBLE_API_KEY="..."' >&2
  exit 2
fi

exec "$PYTHON" "$ROOT/tools/live_runner.py" "$@"
