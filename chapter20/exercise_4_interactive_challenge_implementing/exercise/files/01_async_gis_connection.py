"""Chapter 20, exercise 4 — a remote GIS connection that always closes.

A PostGIS handle, a map server session, a processing queue: the pattern is the same
for all of them. Acquiring the resource is asynchronous, releasing it is
asynchronous, and the release has to happen even when the query in between fails.
That is exactly what `__aenter__` and `__aexit__` give you, and the second half of
this listing is the failure case that proves the release is not decorative.

The delays are simulated with `asyncio.sleep`, so the event loop stays free while
the connection is being established — which is the property a synchronous `with`
cannot offer.
"""

import asyncio
import logging
from typing import Any, Optional, Type

# A format without the timestamp: the log is meant to be compared between runs, and
# a clock makes two identical runs look different.
logging.basicConfig(level=logging.INFO, format="%(message)s")

CONNECT_DELAY = 0.05
RELEASE_DELAY = 0.02
QUERY_DELAY = 0.05


class AsyncGISConnectionManager:
    """An asynchronous context manager around a (simulated) remote GIS session."""

    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection: Optional[str] = None
        self.events: list = []

    async def __aenter__(self) -> str:
        logging.info("Connecting asynchronously to %s...", self.connection_url)
        await asyncio.sleep(CONNECT_DELAY)  # network latency, not a busy wait
        self.connection = f"ACTIVE_GIS_HANDLE_FOR_{self.connection_url}"
        self.events.append("connected")
        logging.info("Connection established successfully.")
        return self.connection

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[Any]) -> bool:
        # exc_type is None on the happy path; anything else means the body failed,
        # and the resource still has to go back.
        if exc_type:
            logging.error("Task failed inside the context, cleanup proceeds: %s: %s",
                          exc_type.__name__, exc_val)
        logging.info("Disconnecting from %s...", self.connection_url)
        await asyncio.sleep(RELEASE_DELAY)
        self.connection = None
        self.events.append("released")
        logging.info("Connection closed and resources released.")
        return False  # do not swallow the exception


async def run_disaster_assessment_task(url: str, fail: bool = False) -> AsyncGISConnectionManager:
    """Connect, do the work, and let the manager release whatever happened."""
    logging.info("Starting assessment task.")
    manager = AsyncGISConnectionManager(url)
    try:
        async with manager as remote_db:
            logging.info("Successfully acquired connection handle: %s", remote_db)
            logging.info("Processing large geospatial query asynchronously...")
            await asyncio.sleep(QUERY_DELAY)
            if fail:
                raise RuntimeError("query timed out on the remote server")
        logging.info("Assessment task finished (inside context).")
    except Exception as exc:  # noqa: BLE001 - the caller decides what a failure means
        logging.warning("Task encountered an error: %s", exc)
    logging.info("Assessment task finished (outside context).")
    return manager


def main():
    print("--- Starting async connection test ---")
    healthy = asyncio.run(run_disaster_assessment_task(
        "postgresql://gis_db/disaster_log"))
    print(f"Handle after the block: {healthy.connection}")
    print(f"Events: {healthy.events}")

    print("\n--- Same task, query fails ---")
    failing = asyncio.run(run_disaster_assessment_task(
        "postgresql://gis_db/disaster_log", fail=True))
    print(f"Handle after the block: {failing.connection}")
    print(f"Events: {failing.events}")
    print("--- Async connection test finished ---")
    return healthy, failing


if __name__ == "__main__":
    main()
