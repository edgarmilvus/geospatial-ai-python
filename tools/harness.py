"""Assertion and artefact helper shared by the chapter harnesses.

A harness is a script that imports a listing, drives it, checks the result and
prints exactly one verdict line:

    ok      example 1 (CRS objects) — 12 assertions passed
    FAILED  example 1 (CRS objects) — 2 of 12 assertions failed

and the machine-readable twin on stderr:

    __VERDICT__ 0 12 example 1 (CRS objects)

Artefacts go to the project's `output/` folder, which is created on demand.
Nothing here writes an absolute path: artefacts record relative names only, so a
figure or a JSON file produced on this machine carries no username.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import traceback


def load_listing(path, name):
    """Import a listing as a module without running its __main__ block."""
    path = pathlib.Path(path)
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Harness:
    def __init__(self, name, files_dir):
        self.name = name
        self.files_dir = pathlib.Path(files_dir)
        self.project = self.files_dir.parent
        self.output = self.project / "output"
        self.count = 0
        self.failures = []

    # -- assertions -----------------------------------------------------
    def check(self, condition, message):
        self.count += 1
        if not condition:
            self.failures.append(message)
        return bool(condition)

    def equal(self, actual, expected, message):
        return self.check(actual == expected,
                          "%s (got %r, expected %r)" % (message, actual, expected))

    def close(self, actual, expected, message, tol=1e-9):
        try:
            ok = abs(float(actual) - float(expected)) <= tol
        except (TypeError, ValueError):
            ok = False
        return self.check(ok, "%s (got %r, expected %r +/- %g)"
                          % (message, actual, expected, tol))

    def contains(self, haystack, needle, message):
        return self.check(needle in haystack, "%s (missing %r)" % (message, needle))

    def raises(self, layer, exception, message):
        try:
            layer()
        except exception:
            return self.check(True, message)
        except Exception as exc:  # noqa: BLE001 - the wrong error is a failure too
            return self.check(False, "%s (raised %s, expected %s)"
                              % (message, type(exc).__name__, exception.__name__))
        return self.check(False, "%s (nothing was raised)" % message)

    # -- artefacts ------------------------------------------------------
    def write_json(self, name, data):
        self.output.mkdir(parents=True, exist_ok=True)
        path = self.output / name
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        return path

    def write_text(self, name, text):
        self.output.mkdir(parents=True, exist_ok=True)
        path = self.output / name
        path.write_text(text, encoding="utf-8")
        return path

    def crash(self):
        """Report a traceback as a failed run, so a crash still ends in a verdict."""
        traceback.print_exc()
        self.failures.append("the run crashed before the verdict (see traceback above)")
        self.count = max(self.count, 1)
        return self.report()

    # -- reporting ------------------------------------------------------
    def report(self):
        if self.failures:
            print("FAILED  %s — %d of %d assertions failed"
                  % (self.name, len(self.failures), self.count))
            for failure in self.failures:
                print("        %s" % failure)
            code = 1
        else:
            print("ok      %s — %d assertions passed" % (self.name, self.count))
            code = 0
        # The machine-readable verdict goes to stderr: a plotting library or a
        # dashboard prints a banner on stdout and would otherwise splice the
        # verdict into a line no anchored pattern can find.
        print("__VERDICT__ %d %d %s" % (code, self.count, self.name), file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        # Leave without running interpreter finalisation: matplotlib's font
        # cache and GDAL's driver teardown both install atexit handlers that can
        # take the stdout lock while CPython is shutting down. The verdict is
        # final, so nothing is left to clean up.
        os._exit(code)


def default_harness(name, files_dir):
    """A harness object for the crash path, so a traceback still ends in a verdict."""
    return Harness(name, files_dir)
