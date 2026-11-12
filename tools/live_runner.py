#!/usr/bin/env python3
"""Run the volume's model-calling listings against a real API.

The offline suite proves the code paths; this proves the prompts. A listing that
passed every offline harness can still fail the first time a real model answers,
because a fake returns what the prompt invited and a model may return prose.

There is no provider to choose. The listings read three variables and the runner
passes them through unchanged:

    OPENAI_COMPATIBLE_BASE_URL   default https://openrouter.ai/api/v1
    OPENAI_COMPATIBLE_MODEL      default ~deepseek/deepseek-flash-latest
    OPENAI_COMPATIBLE_API_KEY    required, exported in the shell that runs this

A row that needs a second service is reported as skipped, never failed: nothing
is broken, the variable is simply unset.

    python3 tools/live_runner.py --list
    python3 tools/live_runner.py --only 1 4
    python3 tools/live_runner.py --slow
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "live"

BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "~deepseek/deepseek-flash-latest"

# chapter, project, listing, timeout (s), note
# A sixth element marks a row as slow: `--slow` includes it.
ROWS: list[tuple] = [
    (18, "advanced_application_script_geopandas_text_to/example",
     "01_text_to_map_agent.py", 240, "ReAct agent writes GeoPandas code"),
    (18, "exercise_5_interactive_challenge_tool_orchest/exercise",
     "01_tool_orchestration.py", 300, "two-tool planner, recovers from a bad call"),
    (20, "advanced_application_script/example",
     "01_adda_pipeline.py", 300, "capstone: three tools over one damage table"),
]

# A row whose second service is absent prints SKIP and the variable to export.
NEEDS: dict[int, tuple[str, str]] = {}

BAD_MARKERS = (
    "Traceback (most recent call last)",
    "AuthenticationError",
    "ConnectionError",
    "rate limit",
)

def env_for() -> dict[str, str]:
    """The child gets this shell's environment plus the two defaults.

    Nothing is read from a file: the key arrives the same way it does for the
    reader, exported by whoever starts the run.
    """
    env = dict(os.environ)
    env.setdefault("OPENAI_COMPATIBLE_BASE_URL", BASE_URL_DEFAULT)
    env.setdefault("OPENAI_COMPATIBLE_MODEL", MODEL_DEFAULT)
    env["PYTHONUNBUFFERED"] = "1"
    env["MPLBACKEND"] = "Agg"
    return env


def run_one(chapter: int, project: str, listing: str, timeout: int):
    folder = ROOT / ("chapter%d" % chapter) / project
    script = folder / "files" / listing
    workdir = folder / "output"
    workdir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=folder, env=env_for(), capture_output=True, text=True,
            # No terminal: a listing that would offer to prompt for a key must see
            # a closed stdin and take its non-interactive branch, not hang.
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="ignore")
        output = partial + "\n[TIMEOUT] exceeded %ds" % timeout
        code = 124
    duration = time.time() - started
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / ("ch%02d-%s.log" % (chapter, listing.replace(".py", "")))
    log.write_text(output, encoding="utf-8")
    (OUT / "last.log").write_text(output, encoding="utf-8")

    status = "PASS" if code == 0 else ("TIMEOUT" if code == 124 else "FAIL")
    if status == "PASS" and any(marker.lower() in output.lower() for marker in BAD_MARKERS):
        status = "FAIL"
    if status == "PASS" and len(output.strip()) < 40:
        status = "FAIL (silent)"
    return status, duration, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", type=int, help="chapters to run")
    parser.add_argument("--list", action="store_true", help="print the rows and exit")
    parser.add_argument("--slow", action="store_true",
                        help="include the rows that take ten minutes or more")
    args = parser.parse_args()

    rows = [row for row in ROWS
            if (not args.only or row[0] in args.only) and (args.slow or len(row) == 5)]
    if args.list:
        for chapter, project, listing, timeout, note, *_ in rows:
            print("ch%-3d %-42s %-46s %s" % (chapter, listing, project, note))
        return 0

    base = os.environ.get("OPENAI_COMPATIBLE_BASE_URL", BASE_URL_DEFAULT)
    model = os.environ.get("OPENAI_COMPATIBLE_MODEL", MODEL_DEFAULT)
    if not os.environ.get("OPENAI_COMPATIBLE_API_KEY"):
        print("missing OPENAI_COMPATIBLE_API_KEY", file=sys.stderr)
        print('  export OPENAI_COMPATIBLE_API_KEY="..."', file=sys.stderr)
        return 2

    print("endpoint: %s  model: %s" % (base, model))
    print("%-8s%-46s%-14s%7s" % ("chapter", "listing", "status", "time"))
    print("-" * 74)
    failures = 0
    ran = 0
    skipped = 0
    started = time.time()
    for chapter, project, listing, timeout, note, *_ in rows:
        need = NEEDS.get(chapter)
        if need and not os.environ.get(need[0]):
            skipped += 1
            print("ch%-6d%-46s%-14s%7s" % (chapter, listing, "SKIP", "-"))
            print("        %s" % need[1])
            continue
        status, duration, output = run_one(chapter, project, listing, timeout)
        ran += 1
        print("ch%-6d%-46s%-14s%6.1fs" % (chapter, listing, status, duration))
        if status != "PASS":
            failures += 1
            tail = [line for line in output.strip().splitlines() if line.strip()][-4:]
            for line in tail:
                print("        %s" % line[:110])
    total = time.time() - started

    print("-" * 74)
    tail = ", %d skipped" % skipped if skipped else ""
    print("%d of %d listings ran%s, %.1fs total, %d failure(s)"
          % (ran, len(rows), tail, total, failures))
    print("logs: %s/" % OUT.relative_to(ROOT))
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
