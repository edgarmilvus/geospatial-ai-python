# Exercise 4 — a queue of tile reads, not a loop of tile reads

## What it does

Writes four GeoJSON tiles under `output/tiles/`, then builds the read queue the
exercise asks for: `[partial(load_single_tile, path) for path in file_paths]`.
`functools.partial` binds a function to its argument without calling it, so the list
holds four tasks instead of four results. The listing then runs the queue to show
that the tasks were real work, deferred — the same list an executor or an event loop
would consume.

## The listings

| file | what it is |
| --- | --- |
| `01_async_task_list.py` | the solution: write four tiles, build four partials, execute them |
| `run_async_tasks.py` | the harness: four partials, one bound argument each, four tile ids |
| `prompt_sketch_a_previous_reader.py` | the book's sequential reader, kept as printed |
| `prompt_sketch_b_exercise_4.py` | the exercise's prompt fence, kept as printed |

## Run it

```bash
cd chapter2/exercise_4_advanced_modification_challenge_pr/exercise/files
python3 01_async_task_list.py
```

It writes `output/tiles/tile_01.geojson` … `tile_04.geojson`, prints the queue, and
then executes all four tasks and prints what each returned; `run_async_tasks.py`
asserts four `partial` objects with one bound argument each, four one-feature tiles
and their ids, and exits non-zero if a task stops pointing at its own tile.

## What it produces

| path | what it is |
| --- | --- |
| `output/tiles/tile_0N.geojson` | four one-feature tiles |
| `output/async_tasks.json` | task count, task type, bound arguments, tile ids |

```text
2. Type of generated task list: <class 'list'>

3. Contents of async_tasks (Conceptual Awaitables):
   functools.partial(load_single_tile, 'tile_01.geojson'), no arguments free
   tasks defined: 4
   tasks executed so far: 0 — partial() binds, it does not call
```

## Notes

- A list comprehension over `load_single_tile(path)` would read all four files before
  the next line ran; over `partial(...)` it reads none of them.
- The argument printed is the file name only, so the output does not carry this
  machine's absolute path.
- This is the shape `asyncio` and `concurrent.futures` consume; the difference between
  a task and a result is the whole concurrency argument.
