import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.models.downloaded_file import DownloadedFile
from app.models.job import JobStatus
from app.schemas.common import APIResponse
from app.schemas.download import (
    DownloadCreateRequest,
    FileOut,
    JobFilesOut,
    JobProgressEvent,
    JobStatusOut,
)
from app.services import job_service, progress_bus, session_service
from app.services.storage import get_storage_backend
from app.utils.errors import JobNotFoundError, JobStillProcessingError
from app.utils.rate_limit import action_rate_limit, limiter
from app.workers.conversion_worker import process_job_with_timeout
from app.workers.queue import get_job_queue

router = APIRouter(prefix="/api/download", tags=["download"])

_TERMINAL = {"completed", "failed", "cancelled", "expired"}
_MEDIA_TYPES = {"mp3": "audio/mpeg", "m4a": "audio/mp4", "wav": "audio/wav"}


def _sse(event: JobProgressEvent) -> str:
    return f"data: {event.model_dump_json()}\n\n"


@router.post("/create")
@limiter.limit(action_rate_limit)
async def create_download(
    request: Request,
    payload: DownloadCreateRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> dict:
    session_service.enforce_daily_limit(db, user)
    session_service.enforce_concurrent_job_limit(db, user)

    info = await run_in_threadpool(
        job_service.analyze_playlist, payload.playlist_url, max_videos=settings.max_playlist_videos
    )
    job = job_service.create_download_job(db, user, info, payload, settings)
    session_service.increment_daily_count(db, user)

    queue = get_job_queue()
    queue.start(process_job_with_timeout)
    await queue.enqueue(job.id)

    return {"success": True, "job_id": job.id, "status": job.status.value}


@router.get("/{job_id}", response_model=APIResponse[JobStatusOut])
async def get_job(job_id: str, db: DbSession, user: CurrentUser) -> APIResponse[JobStatusOut]:
    job = job_service.get_job_for_user(db, job_id, user)
    return APIResponse(data=job_service.job_to_status(job))


@router.get("/{job_id}/progress")
async def stream_progress(job_id: str, request: Request, db: DbSession, user: CurrentUser) -> StreamingResponse:
    job = job_service.get_job_for_user(db, job_id, user)
    initial_event = job_service.job_to_progress_event(job)

    async def event_generator():
        yield _sse(initial_event)
        if initial_event.status in _TERMINAL:
            return

        queue = progress_bus.subscribe(job_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event: JobProgressEvent = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _sse(event)
                if event.status in _TERMINAL:
                    break
        finally:
            progress_bus.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/{job_id}/files", response_model=APIResponse[JobFilesOut])
async def list_files(job_id: str, db: DbSession, user: CurrentUser) -> APIResponse[JobFilesOut]:
    job = job_service.get_job_for_user(db, job_id, user)
    files = db.query(DownloadedFile).filter(DownloadedFile.job_id == job.id).all()
    data = JobFilesOut(
        job_id=job.id,
        status=job.status.value,
        files=[
            FileOut(
                id=f.id,
                filename=f.filename,
                audio_format=f.audio_format,
                quality_kbps=f.quality_kbps,
                size_bytes=f.size_bytes,
            )
            for f in files
        ],
        total_size_bytes=job.total_size_bytes,
        expires_at=job.expires_at,
    )
    return APIResponse(data=data)


@router.get("/{job_id}/file/{file_id}")
async def download_file(job_id: str, file_id: str, db: DbSession, user: CurrentUser) -> FileResponse:
    job = job_service.get_job_for_user(db, job_id, user)
    file_row = (
        db.query(DownloadedFile)
        .filter(DownloadedFile.id == file_id, DownloadedFile.job_id == job.id)
        .one_or_none()
    )
    if file_row is None:
        raise JobNotFoundError("File not found.")

    storage = get_storage_backend()
    path = storage.resolve_file(job.id, file_row.filename)
    if not path.exists():
        raise JobNotFoundError("This file has expired or was already removed.")

    return FileResponse(
        path,
        media_type=_MEDIA_TYPES.get(file_row.audio_format, "application/octet-stream"),
        filename=file_row.filename,
    )


@router.get("/{job_id}/zip")
async def download_zip(job_id: str, db: DbSession, user: CurrentUser) -> FileResponse:
    job = job_service.get_job_for_user(db, job_id, user)
    if job.status != JobStatus.COMPLETED or not job.zip_filename:
        raise JobNotFoundError("No ZIP archive is available for this job.")

    storage = get_storage_backend()
    path = storage.resolve_file(job.id, job.zip_filename)
    if not path.exists():
        raise JobNotFoundError("This ZIP archive has expired or was already removed.")

    return FileResponse(path, media_type="application/zip", filename=job.zip_filename)


@router.delete("/{job_id}")
async def delete_job(job_id: str, db: DbSession, user: CurrentUser) -> dict:
    job = job_service.get_job_for_user(db, job_id, user)
    if job.status in (JobStatus.PENDING, JobStatus.ANALYZING, JobStatus.PROCESSING):
        raise JobStillProcessingError(
            "This job is still processing and can't be deleted yet. It will be safe to "
            "delete once it completes or fails."
        )
    storage = get_storage_backend()
    storage.delete_job(job.id)
    db.delete(job)
    db.commit()
    return {"success": True, "message": "Job and associated files deleted."}
