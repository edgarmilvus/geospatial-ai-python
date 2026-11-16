# Security policy

This repository is the companion code for *Geospatial AI (GeoAI) with Python
Programming*: the listings, the harnesses and the runners a reader runs on their
own machine. It is not a service, it handles no user data, and it ships no
credentials.

## Reporting a problem in the code

If a listing, a harness or a runner does something unsafe — a token written into
a file, a `subprocess` call that interpolates untrusted input, a download that
trusts whatever it receives — report it privately from the **Security** tab of
this repository (*Report a vulnerability*). Please do not open a public issue for
it: the issue tracker is for readers, and a public issue would describe the
weakness before there is a fix.

## Reporting something wrong in the book

Errata belong in the public tracker. Use the **Errata** form and name the
chapter, the listing and what the book claims; a listing that does not run has
its own form. Neither is a security report.

## Out of scope

- The values the listings invent — coordinates, densities, scores, damage
  counts. They are demonstrations, not measurements.
- The Mapbox token present in the repository's early history. It is Plotly's
  public demonstration token (Mapbox user `plotlymapbox`), not a credential of
  this project; it was removed from every listing, and the listings have read
  `MAPBOX_ACCESS_TOKEN` since.
- Anything that requires changing the reader's machine rather than this code.

## What this repository does about it

Dependabot watches the pinned dependencies and opens a pull request when one of
them has a published advisory; secret scanning and push protection are on, so a
key cannot be committed by accident. A report that needs a code change gets one
in the next release, with the listing, the book and the repository updated
together.
