"""Chapter 19, exercise 4 — an inference loop that does not block the event loop.

The stream is an asynchronous context manager and an asynchronous iterator: the
connection is acquired by `async with`, and the batches arrive through `async for`.
Between two batches the loop yields control, which is the whole point — a health
check runs *while* the pipeline is waiting for data, and the interleaved log below
is the proof.

The delays are milliseconds rather than seconds so the demonstration runs inside a
test suite, but the shape of the code is the shape of a production deployment. A
second run, with a stream that raises, shows the connection closing anyway.
"""

import asyncio
import pathlib
from typing import AsyncGenerator, Optional, Type, Any

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# The delays a real socket would impose: connection setup, teardown, per-batch I/O.
CONNECT_DELAY = 0.05
TEARDOWN_DELAY = 0.01
BATCH_DELAY = 0.02
INFERENCE_DELAY = 0.01
RENDER_DELAY = 0.03
BATCH_COUNT = 5


# --- 1. The asynchronous data interface ---

class AsyncTrafficStream:
    """A real-time traffic feed of (features, Laplacian) batches.

    `__aenter__` and `__aexit__` are the resource boundary: whatever happens in
    the body, the connection is released on the way out.
    """

    def __init__(self, stream_id: str):
        self.stream_id = stream_id
        self.connected = False
        print(f"[{self.stream_id}] Stream initialized.")

    async def __aenter__(self):
        print(f"[{self.stream_id}] Attempting connection...")
        await asyncio.sleep(CONNECT_DELAY)
        self.connected = True
        print(f"[{self.stream_id}] Connected successfully.")
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[Any]):
        print(f"[{self.stream_id}] Disconnecting...")
        await asyncio.sleep(TEARDOWN_DELAY)
        self.connected = False
        if exc_type:
            print(f"[{self.stream_id}] Exception encountered: {exc_val}")
        print(f"[{self.stream_id}] Disconnected.")

    async def stream_data(self) -> AsyncGenerator[tuple, None]:
        """Yields (batch_id, Laplacian) pairs as they become available."""
        for i in range(BATCH_COUNT):
            await asyncio.sleep(BATCH_DELAY)  # simulating I/O latency
            yield (f"Batch_{i}", "Laplacian_Matrix")


# --- 2. Inference and the concurrent GIS task ---

async def perform_stgcn_inference(model, data_batch_id, X, L):
    """Stand-in for `model(X, L)`, which is CPU-bound and so is not awaited here."""
    print(f"    [Inference] Processing {data_batch_id}...")
    await asyncio.sleep(INFERENCE_DELAY)
    prediction = f"Predicted_Speed_{data_batch_id}"
    print(f"    [Inference] Prediction complete for {data_batch_id}.")
    return prediction


async def update_map_display(data_batch_id: str):
    """A GIS task that runs while the stream is idle: rendering the new layer."""
    print(f"  [Map Display] Received prediction for {data_batch_id}. Rendering...")
    await asyncio.sleep(RENDER_DELAY)
    print(f"  [Map Display] Finished rendering {data_batch_id}.")


async def run_inference(model, stream_id: str) -> int:
    """Consume the stream, predict, render. Returns the batch count."""
    processed = 0
    async with AsyncTrafficStream(stream_id) as stream:
        async for data_batch_id, laplacian in stream.stream_data():
            X = "Feature_Tensor"
            prediction = await perform_stgcn_inference(model, data_batch_id, X,
                                                       laplacian)
            await update_map_display(prediction)
            processed += 1
            print("-" * 30)
    return processed


async def continuous_health_check(cycles: int = 3):
    """Another task on the same loop: it must keep ticking during the waits."""
    for i in range(1, cycles + 1):
        await asyncio.sleep(BATCH_DELAY * 2)
        print(f"[Health Check] System operational. Cycle {i}.")


async def main_deployment_simulation(stream_id: str = "Highway_101_Feed") -> int:
    print("Starting GeoAI Deployment Simulation...")
    # gather: the inference loop and the health check share the event loop, so
    # neither waits for the other to finish.
    processed, _ = await asyncio.gather(
        run_inference("Trained_STGCN_Model", stream_id),
        continuous_health_check(),
    )
    print("Deployment simulation finished.")
    return processed


# --- 3. What a failing stream does to the connection ---

class FailingTrafficStream(AsyncTrafficStream):
    """A stream whose third batch raises, to test the teardown path."""

    async def stream_data(self) -> AsyncGenerator[tuple, None]:
        for i in range(BATCH_COUNT):
            await asyncio.sleep(BATCH_DELAY)
            if i == 2:
                raise RuntimeError("sensor feed died mid-batch")
            yield (f"Batch_{i}", "Laplacian_Matrix")


async def failing_run(stream_id: str = "Highway_101_Feed") -> str:
    """Same loop, but the body raises: `__aexit__` must still run."""
    try:
        async with FailingTrafficStream(stream_id) as stream:
            async for batch_id, _ in stream.stream_data():
                print(f"  [Inference] Processing {batch_id}...")
    except RuntimeError as exc:
        print(f"Pipeline halted: {exc}")
        return "halted"
    return "completed"


def main():
    """Run the healthy stream, then the failing one, and write the artefact."""
    batches = asyncio.run(main_deployment_simulation())

    print("\n--- Now with a stream that fails on its third batch ---")
    outcome = asyncio.run(failing_run("Highway_101_Feed"))
    print(f"Outcome: {outcome}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "async_stream.txt").write_text(
        f"batches processed: {batches}\nfailing run: {outcome}\n",
        encoding="utf-8")
    return batches, outcome


if __name__ == "__main__":
    main()
