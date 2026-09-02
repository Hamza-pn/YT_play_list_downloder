"""In-process background job queue (Phase 1).

A fixed pool of asyncio worker tasks consume job ids from an asyncio.Queue,
capping concurrent conversions at MAX_CONCURRENT_JOBS. This is the
JobQueue interface the rest of the app depends on; Phase 2 replaces the
internals with Celery + Redis (producer: app.api routes call
`queue.enqueue(job_id)` either way; the API surface doesn't change).
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.utils.logging import get_logger

logger = get_logger(__name__)

JobHandler = Callable[[str], Awaitable[None]]


class InProcessJobQueue:
    def __init__(self, max_workers: int) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._max_workers = max_workers
        self._tasks: list[asyncio.Task] = []

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)

    def start(self, handler: JobHandler) -> None:
        if self._tasks:
            return
        for i in range(self._max_workers):
            self._tasks.append(asyncio.create_task(self._worker_loop(i, handler)))
        logger.info("Started %d job queue workers", self._max_workers)

    async def stop(self, timeout: float = 10.0) -> None:
        """Cancel and await every worker task, bounded by `timeout` so a
        worker stuck in non-cancellable blocking work (e.g. a subprocess
        running in a thread pool executor, which asyncio cancellation
        cannot interrupt) can never hang application shutdown forever."""
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await asyncio.wait_for(task, timeout=timeout)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                logger.warning("Worker task did not stop within %.0fs; abandoning it", timeout)
        self._tasks.clear()

    async def _worker_loop(self, worker_index: int, handler: JobHandler) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                await handler(job_id)
            except Exception:
                logger.exception("Unhandled error processing job %s on worker %d", job_id, worker_index)
            finally:
                self._queue.task_done()


job_queue: InProcessJobQueue | None = None


def get_job_queue() -> InProcessJobQueue:
    global job_queue
    if job_queue is None:
        from app.config.settings import get_settings

        job_queue = InProcessJobQueue(max_workers=get_settings().max_concurrent_jobs)
    return job_queue
