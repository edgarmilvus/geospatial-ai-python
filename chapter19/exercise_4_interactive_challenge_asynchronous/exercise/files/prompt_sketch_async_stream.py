# Setup for exercise 4: the stream and the skeleton the student fills in.
# In a real deployment the stream is a message queue or a socket; here it is an
# asynchronous iterator with the same three methods, so the control flow is the
# exercise and the network is not.
import asyncio
from typing import AsyncGenerator


class AsyncTrafficStream:
    """
    Simulates a real-time traffic data feed that yields
    pre-processed feature tensors (X) and Laplacian matrices (L).
    """

    def __init__(self, stream_id: str):
        self.stream_id = stream_id
        self.connected = False

    async def __aenter__(self):
        # Asynchronous resource acquisition (e.g., connecting to a socket)
        await asyncio.sleep(0.5)
        self.connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Asynchronous resource release (e.g., closing the connection)
        await asyncio.sleep(0.1)
        self.connected = False

    async def stream_data(self) -> AsyncGenerator[tuple, None]:
        """Yields (X, L) batches asynchronously."""
        # Placeholder: in reality this awaits network IO
        for i in range(10):
            await asyncio.sleep(0.2)
            # X: (T_hist, N, F), L: (N, N)
            yield (f"Batch_{i}", "Laplacian_Matrix")


# --- Required function signatures for the student to complete ---

async def update_map_display(data_batch_id: str):
    """
    Simulates a non-blocking task (e.g., updating a GIS interface)
    concurrently with model inference.
    """
    # Student implementation must include an awaitable sleep or I/O operation
    pass


async def run_inference(model, stream_id: str):
    """
    Connects to the asynchronous stream and performs inference on received batches.
    Must use async with and async for.
    """
    # Student implementation goes here
    pass


async def main_deployment_simulation():
    # Assume model loading is synchronous for simplicity
    stgcn_model = "Trained_STGCN_Model"

    # The student must orchestrate the concurrent execution of tasks here
    await run_inference(stgcn_model, "Highway_101_Feed")


if __name__ == "__main__":
    # Student must ensure the event loop is run correctly
    pass
