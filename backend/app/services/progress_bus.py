"""In-process pub/sub used to push job progress to SSE subscribers.

Phase 1 only (single backend process). Phase 2 replaces this with Redis
pub/sub so progress fans out correctly across multiple API/worker
processes — call sites (publish/subscribe) won't need to change.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict

from app.schemas.download import JobProgressEvent

_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


def subscribe(job_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _subscribers[job_id].append(queue)
    return queue


def unsubscribe(job_id: str, queue: asyncio.Queue) -> None:
    subs = _subscribers.get(job_id)
    if subs and queue in subs:
        subs.remove(queue)
    if subs is not None and not subs:
        _subscribers.pop(job_id, None)


def publish(job_id: str, event: JobProgressEvent) -> None:
    for queue in list(_subscribers.get(job_id, [])):
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass
