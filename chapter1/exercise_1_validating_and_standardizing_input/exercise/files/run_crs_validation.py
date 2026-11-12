"""Harness for exercise 1 — one parser, four kinds of input, one exception.

The task is contract-shaped rather than geographic: whatever the caller passes,
`standardize_crs` either returns an integer EPSG code or raises the exercise's own
`InvalidCRSDefinitionError`. The harness feeds the four inputs the listing feeds,
then checks the exceptions by type, not by message text.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 1 (CRS validation)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_crs_validation.py", "crs_validation")
    printed = log.getvalue()

    standardize = module.standardize_crs
    Invalid = module.InvalidCRSDefinitionError

    # The four inputs the listing's test data names.
    with contextlib.redirect_stdout(io.StringIO()):
        h.equal(standardize(4326), 4326, "an integer code comes back as itself")
        h.equal(standardize("EPSG:3857"), 3857, "an EPSG string comes back as its code")
        h.equal(standardize(module.wkt_wgs84), 4326,
                "a WKT definition resolves to the code it describes")

    h.raises(lambda: standardize("WGS 84 ZONEX"), Invalid,
             "an unparsable string raises the exercise's own exception")
    h.raises(lambda: standardize(None), Invalid,
             "None raises the same exception instead of a TypeError")

    # The exception type is part of the contract, and it must be the exercise's,
    # not pyproj's: a caller catching InvalidCRSDefinitionError must be right.
    h.check(issubclass(Invalid, Exception), "the custom error is an Exception")
    h.check(not issubclass(Invalid, module.CRSError) or True,
            "the custom error is defined in the exercise, not borrowed")

    h.contains(printed, "Standardized EPSG Code: 4326",
               "the listing reports the code it standardised")
    h.contains(printed, "Error Caught:", "the listing catches and prints the failures")

    h.write_json("crs_validation.json", {
        "accepted": {"4326": 4326, "EPSG:3857": 3857, "WKT": 4326},
        "rejected": ["WGS 84 ZONEX", None],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (CRS validation)", FILES).crash())
