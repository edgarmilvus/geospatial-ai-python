#!/usr/bin/env python3
"""Run every chapter's harnesses without a POSIX shell.

`run_offline.sh` is the primary entry point on macOS and Linux. This script exists
for the machines that have no bash worth relying on — native Windows, mostly — and
for anyone who would rather not care which shell is installed.

It walks `chapter*/`, runs every `files/run_*.py` in its own project directory,
reads the `__VERDICT__` line the harness prints to stderr, and exits non-zero if any
harness fails. No network, no keys, no Docker.

    python run_offline.py
    python run_offline.py --only 1 2 16
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
MARKER = re.compile(r"^__VERDICT__ (\d) (\d+) ", re.MULTILINE)
VERDICT = re.compile(r"^[│|]?\s*ok\s.*?— (\d+) assertions? passed", re.MULTILINE)


def chapter_key(path: pathlib.Path) -> int:
    digits = re.sub(r"\D", "", path.name)
    return int(digits) if digits else 0


def projects(chapter: pathlib.Path) -> list[pathlib.Path]:
    return sorted({h.parent.parent for h in chapter.glob("*/*/files/run_*.py")})


def run_harness(script: pathlib.Path) -> tuple[bool, int, str]:
    env = dict(os.environ)
    # Windows defaults to the ANSI code page; the harnesses print UTF-8 (the em
    # dash in the verdict, place names with accents). Decode as UTF-8 on both
    # sides or subprocess raises UnicodeDecodeError while reading the pipe.
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=script.parent.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        stdin=subprocess.DEVNULL,
    )
    output = result.stdout + result.stderr
    marker = MARKER.search(output)
    if marker:
        return marker.group(1) == "0", int(marker.group(2)), output
    match = VERDICT.search(output)
    if result.returncode == 0 and match:
        return True, int(match.group(1)), output
    return False, 0, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", type=int, help="chapters to run")
    args = parser.parse_args()

    venv_python = ROOT / (".venv/Scripts/python.exe" if os.name == "nt"
                          else ".venv/bin/python")
    if venv_python.exists():
        try:
            same = pathlib.Path(sys.executable).resolve() == venv_python.resolve()
        except OSError:
            same = False
        if not same:
            print(f"warning: this is {sys.executable}")
            print(f"         the project's environment is {venv_python}")
            print(f"         run: {venv_python} run_offline.py")
            print()

    chapters = sorted((p for p in ROOT.glob("chapter*") if p.is_dir()), key=chapter_key)
    if args.only:
        chapters = [c for c in chapters if chapter_key(c) in args.only]

    failures = 0
    harnesses = 0
    assertions = 0
    started = time.time()

    for chapter in chapters:
        chapter_failures = 0
        chapter_harnesses = 0
        chapter_assertions = 0
        for project in projects(chapter):
            for script in sorted((project / "files").glob("run_*.py")):
                ok, count, output = run_harness(script)
                if ok:
                    chapter_harnesses += 1
                    chapter_assertions += count
                else:
                    chapter_failures += 1
                    print(f"FAILED  {project.relative_to(ROOT)}/{script.name}")
                    tail = [line for line in output.strip().splitlines() if line.strip()][-6:]
                    for line in tail:
                        print(f"        {line[:110]}")
        harnesses += chapter_harnesses
        assertions += chapter_assertions
        failures += chapter_failures
        status = "ok" if chapter_failures == 0 else "FAILED"
        print(f"{chapter.name}: {status} "
              f"({chapter_harnesses} harnesses, {chapter_assertions} assertions)")

    elapsed = time.time() - started
    print("-" * 60)
    print(f"{len(chapters)} chapters, {harnesses} harnesses, {assertions} assertions, "
          f"{elapsed:.1f}s")
    if failures:
        print(f"{failures} harness(es) failed")
        return 1
    print("volume: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
