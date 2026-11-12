# Geospatial AI (GeoAI) with Python Programming — companion code

Runnable code for *Geospatial AI (GeoAI) with Python Programming*, Volume 14. Each
chapter folder holds one file per listing exactly as it appears in the book, a
harness that drives it and asserts what happened, and an `output/` folder for
whatever the run writes.

This is the code that accompanies the book: the chapters, their harnesses and the
runners.

## The chapters

| # | chapter | listings | harnesses |
| --- | --- | --- | --- |
| 1 | [Coordinate Reference Systems (CRS) - Projections Explained](chapter1/) | 7 | 7 |
| 2 | [The GeoDataFrame - Reading Shapefiles and GeoJSON](chapter2/) | 10 | 7 |
| 3 | [Spatial Operations - Intersections, Joins, and Buffers](chapter3/) | 12 | 7 |
| 4 | [Geometric Manipulations - Calculating Areas and Distances](chapter4/) | 12 | 8 |
| 5 | [Plotting Static Maps - Customizing Matplotlib for Geography](chapter5/) | 7 | 7 |
| 6 | [Introduction to Folium - Creating HTML Maps](chapter6/) | 6 | 6 |
| 7 | [Markers and Popups - Adding Data to the Map](chapter7/) | 6 | 6 |
| 8 | [Choropleth Maps - Visualizing Population and Elections](chapter8/) | 12 | 7 |
| 9 | [Heatmaps - Visualizing Density and Traffic](chapter9/) | 7 | 7 |
| 10 | [Dashboards - Combining Maps with Plotly Dash](chapter10/) | 7 | 7 |
| 11 | [Introduction to Rasterio - Reading Satellite Imagery](chapter11/) | 13 | 7 |
| 12 | [Band Math - Calculating NDVI (Vegetation Index) from Space](chapter12/) | 11 | 7 |
| 13 | [Elevation Models - Analyzing Terrain and Slopes](chapter13/) | 12 | 7 |
| 14 | [Masking and Clipping - Extracting Region of Interest](chapter14/) | 8 | 7 |
| 15 | [Time Series from Space - Tracking Deforestation over Time](chapter15/) | 12 | 7 |
| 16 | [Deep Learning on Maps - Detecting Buildings with PyTorch](chapter16/) | 12 | 7 |
| 17 | [Segment Anything (SAM) - Using Meta's AI to Segment Satellite Imagery](chapter17/) | 7 | 7 |
| 18 | [Text-to-Map - Building a LangChain Agent that Generates GeoPandas Code](chapter18/) | 9 | 7 |
| 19 | [Traffic Prediction - Using Graph Neural Networks (GNN) on Road Networks](chapter19/) | 7 | 6 |
| 20 | [Capstone Project - Automated Disaster Damage Assessment with AI](chapter20/) | 10 | 6 |

Every harness runs offline and deterministic, prints one verdict line and exits non-zero on a failed assertion. Nothing in this volume downloads data at run time: each listing generates what it reads.

## Licence

The code in this repository is released under the **MIT License** — see `LICENSE`.
You may use it, change it and ship it, including commercially, as long as the
copyright notice travels with it.

The **book itself is not MIT**: the text, the figures and the diagrams are
© 2026 Edgar Milvus, all rights reserved. Quoting a listing or a paragraph in a
review or a course is fine; redistributing the book is not.

## Setup

Python 3.11 or 3.12 — not 3.13, which several of these wheels do not have yet.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On native Windows the same commands work from PowerShell — `.venv\Scripts\activate`
instead of `source .venv/bin/activate`, and `python` where the book writes `python3`.
Nothing in this volume needs WSL.

Two things are optional, and a check that needs one of them is skipped with the
command to install it rather than failed:

```bash
python3 -m pip install -r requirements-ml.txt   # chapter 16 trains a U-Net, chapter 19 a GNN
```

Chapter 17 segments satellite chips with Meta's Segment Anything. The package and
its 375 MB weights are not part of the base install; the chapter's harness runs a
local stand-in for the segmenter and says so, and `requirements-ml.txt` gives the
two commands that install the real thing.

## Environment

Chapters 18 and 20 ask a language model to write GeoPandas code. The listings read
three variables and nothing else:

| variable | used for | default in code |
| --- | --- | --- |
| `OPENAI_COMPATIBLE_BASE_URL` | the OpenAI-compatible endpoint | `https://openrouter.ai/api/v1` |
| `OPENAI_COMPATIBLE_MODEL` | the model that answers | `~deepseek/deepseek-flash-latest` |
| `OPENAI_COMPATIBLE_API_KEY` | the key sent to that endpoint | none, required |

Set them in your shell:

```bash
export OPENAI_COMPATIBLE_API_KEY="..."
export OPENAI_COMPATIBLE_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_COMPATIBLE_MODEL="~deepseek/deepseek-flash-latest"
```

Only the key has to be set; the other two exist so a chapter can be pointed at a
different endpoint or a stronger model without editing a listing. No script here
reads a key from a file, and no listing or runner has a provider flag: the three
names are the whole surface.

## Run

From a fresh copy, end to end — clone, environment, suite:

```bash
git clone https://github.com/edgarmilvus/geospatial-ai-python.git
cd geospatial-ai-python
python3.11 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
./run_offline.sh
```

That is the whole offline suite: twenty chapters, one line each, no key and no
network — **124 harnesses and 2 985 assertions in about 90 seconds** on a base install.
Chapters 16 and 19 need the optional deep-learning stack, so they print

```
skip    chapter 16: torch is not installed
        .venv/bin/python -m pip install -r requirements-ml.txt
chapter 16: ok (skipped, optional dependency absent)
```

and the volume still ends `ok`. With `requirements-ml.txt` installed the same command
reports **137 harnesses and 3 303 assertions**: the only rows that change are the two
optional chapters.

Two sections below go past the offline suite: **Live run** for the three listings that
ask a real model, and **Run everything** for the one command that chains the suite,
the optional extras and, with `--live`, the live run.

One chapter, while you are working on it:

```bash
./chapter5/run_offline.sh
```

The same suite without a POSIX shell — native Windows, or any machine without bash:

```bash
python run_offline.py
```

It walks `chapter*/`, runs every `files/run_*.py` in its project directory, reads the
`__VERDICT__` line each harness prints to stderr, and prints the same totals as the
shell runner.

## Live run

The offline suite proves the code paths; the live run proves the prompts. It needs the
key from Environment, and it spends money — a few cents for the three rows on DeepSeek
Flash, under a minute in total:

```bash
./run_live.sh              # every row
./run_live.sh --only 18 20 # selected chapters
./run_live.sh --list       # the rows, free
```

Three listings in the volume instantiate a model: the Text-to-Map agent and its
two-tool planner in chapter 18, and the capstone pipeline in chapter 20. Each runs in
its project's `output/` with **its own timeout** (four to five minutes, measured from
the worst case), and keeps a log in `output/live/` — one file per row plus `last.log`.
The closing line says how many ran, how many were skipped and how many failed.

Every row in this volume needs the three variables and nothing else. The runner reads
no key from a file and knows no provider: those three names are the whole surface.

## Run everything

`./run_everything.sh` chains the whole check:

```bash
./run_everything.sh           # suite + optional extras, live run skipped
./run_everything.sh --live    # the same, then the three live rows
```

1. the offline suite — twenty chapters;
2. the optional extras — chapters 16 and 19 under `torch`, skipped with the install
   command when the package is absent;
3. the live run — only with `--live`, and only when the key is exported.

A phase whose service or package is missing is skipped with the command that installs
it, and the closing summary lists what ran and what did not. That is why the script
ends `ok` on a machine with nothing optional, and why `--live` without a key is
skipped instead of failing.

## Windows

Native Windows works; there is no WSL step. Use Python 3.11 or 3.12, not 3.13: several
pinned geospatial packages have no wheels for it.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

.venv\Scripts\python run_offline.py            # the suite, same totals as run_offline.sh
.venv\Scripts\python run_offline.py --only 5 10

.venv\Scripts\python tools\live_runner.py      # the live run, needs the key
.venv\Scripts\python tools\live_runner.py --list
```

`run_everything.sh` is a bash script. On Windows, run the two commands it would chain —
`run_offline.py` and `tools\live_runner.py` — and install the optional extras only if
you want them. Three differences worth knowing: `torch` is optional (chapters 16 and 19
skip themselves), chapter 17's real segmenter needs a package that is not on PyPI and a
375 MB checkpoint (the stand-in says so), and no listing needs a POSIX shell — paths
come from `pathlib` and artefacts go to the project's `output/`.

## What a run writes

Every project has an `output/` folder, created on demand. A listing writes there and
nowhere else, and records relative names only, so a figure or a GeoPackage produced
on your machine carries no absolute path and no username. Those folders are not in
this archive; the first run recreates them.

Each chapter's suite writes its log to `chapterN/output/run_N.log`, and the live
runner writes one log per listing under `output/live/`.

## Layout

```
chapterN/
  README.md            index of the chapter's projects
  run_offline.sh       one line per harness
  <section>/<example|exercise>/
    README.md          what it is, its listings, how to run them, what they produce
    files/             the listing, byte-identical to the book, plus its harness
    output/            everything the run wrote
tools/                 harness helper, folium reader, tool-calling fake, live runner
run_offline.sh         the suite, POSIX shell
run_offline.py         the suite, shell-free twin
run_everything.sh      suite + optional phases, skipping what is absent
run_live.sh            the model-calling listings, manual only
LICENSE                MIT, for the code; the book is not
requirements.txt       pinned stack
requirements-ml.txt    the optional deep-learning extras
```

## When something does not start

| message | what it means |
| --- | --- |
| `ModuleNotFoundError: No module named 'geopandas'` | the virtual environment is not active, or `pip install -r requirements.txt` was never run in it |
| `ERROR: No matching distribution found for rasterio` | the interpreter is too old or too new — 3.13 has no wheels for this stack; use 3.11 or 3.12 |
| `zsh: permission denied: ./run_offline.sh` | the executable bit is missing after unzipping: `chmod +x run_offline.sh chapter*/run_offline.sh` |
| `FAILED … no verdict line` | a harness died before its verdict; the log under `chapterN/output/harness.log` has the traceback |
| `SKIP … OPENAI_COMPATIBLE_API_KEY` | not a failure: the live row needs the key exported, the offline suite does not |
| `[SAM] segment_anything is not installed` | chapter 17 falling back to the stand-in — expected, and it says so in the book |
| `ModuleNotFoundError: No module named 'torch'` | chapters 16 and 19 need the optional extras: `pip install -r requirements-ml.txt` |

## Checks

The four runners, each described once above: `run_offline.sh` (the suite),
`run_offline.py` (the same, shell-free), `run_everything.sh` (suite, extras and the
live run) and `run_live.sh` (the live rows alone, manual). `python tools/live_runner.py
--list` prints the live rows without running them.

The tools under `tools/` are what the listings and the runners need at run time: the harness
helper, the two fakes, the folium reader and the live runner. Nothing else is required to run
anything in this repository.
