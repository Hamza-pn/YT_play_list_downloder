"""The actual job pipeline: download audio -> ffmpeg convert -> embed
metadata -> zip -> mark complete. One video failing does not abort the job;
it's recorded as a per-video failure and processing continues.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import get_settings
from app.db.session import SessionLocal
from app.models.job import Job, JobStatus
from app.models.video import Video, VideoStatus
from app.models.downloaded_file import DownloadedFile
from app.services import job_service, progress_bus
from app.services.audio_service import convert_audio
from app.services.media_retrieval import get_media_retrieval_service
from app.services.metadata_service import TrackMetadata, embed_metadata
from app.services.storage import get_storage_backend
from app.utils.errors import AppError
from app.utils.logging import get_logger, log_event
from app.utils.security import sanitize_filename

logger = get_logger(__name__)


def _publish(job: Job) -> None:
    progress_bus.publish(job.id, job_service.job_to_progress_event(job))


async def _process_one_video(db, job: Job, video: Video, job_dir, settings) -> None:
    media = get_media_retrieval_service()
    storage = get_storage_backend()

    video.status = VideoStatus.DOWNLOADING
    job.current_video_title = video.title
    _publish(job)

    raw = await asyncio.to_thread(
        media.download_audio,
        video.external_id,
        job_dir,
        max_file_size_bytes=settings.max_file_size_mb * 1024 * 1024,
        timeout_seconds=min(settings.job_timeout_seconds, 900),
    )

    video.status = VideoStatus.CONVERTING
    _publish(job)

    safe_stem = sanitize_filename(
        f"{video.position + 1:02d} - {video.title}", fallback=f"track_{video.position + 1}"
    )
    dest_filename = f"{safe_stem}.{job.audio_format.value}"
    dest_path = storage.resolve_file(job.id, dest_filename)

    await asyncio.to_thread(
        convert_audio,
        raw.file_path,
        dest_path,
        audio_format=job.audio_format.value,
        quality_kbps=job.quality_kbps,
        source_codec=raw.source_codec,
        timeout_seconds=min(settings.job_timeout_seconds, 600),
    )

    playlist_title = job.playlist.title if job.playlist else "Downloaded Playlist"
    meta = TrackMetadata(
        title=video.title,
        artist=video.channel_name or (job.playlist.channel_name if job.playlist else None) or "Unknown Artist",
        album=playlist_title,
        track_number=video.position + 1,
        year=raw.upload_year,
        thumbnail_path=raw.thumbnail_path,
    )
    await asyncio.to_thread(embed_metadata, dest_path, job.audio_format.value, meta)

    raw.file_path.unlink(missing_ok=True)
    if raw.thumbnail_path:
        raw.thumbnail_path.unlink(missing_ok=True)

    db.add(
        DownloadedFile(
            job_id=job.id,
            video_id=video.id,
            filename=dest_path.name,
            audio_format=job.audio_format.value,
            quality_kbps=job.quality_kbps,
            size_bytes=dest_path.stat().st_size,
            relative_path=dest_path.name,
        )
    )
    video.status = VideoStatus.COMPLETED
    video.progress_percent = 100
    job.completed_videos += 1


async def process_job(job_id: str) -> None:
    settings = get_settings()
    storage = get_storage_backend()
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).one_or_none()
        if job is None:
            logger.warning("process_job called for missing job %s", job_id)
            return

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        log_event(logger, 20, "job_started", job_id=job.id, total_videos=job.total_videos)
        _publish(job)

        job_dir = storage.job_dir(job.id)
        videos = sorted(job.videos, key=lambda v: v.position)

        job_was_removed = False
        for video in videos:
            try:
                await _process_one_video(db, job, video, job_dir, settings)
            except AppError as exc:
                video.status = VideoStatus.FAILED
                video.error_message = exc.message
                job.failed_videos += 1
                log_event(logger, 30, "video_failed", job_id=job.id, video_id=video.id, reason=exc.error_code)
            except Exception:
                video.status = VideoStatus.FAILED
                video.error_message = "An unexpected error occurred while processing this video."
                job.failed_videos += 1
                logger.exception("Unexpected error processing video %s (job %s)", video.id, job.id)

            try:
                db.commit()
            except SQLAlchemyError:
                # The job (or its rows) were deleted out from under us —
                # e.g. by a DELETE request racing an in-flight worker.
                # Nothing left to update; stop touching these rows.
                db.rollback()
                logger.warning("Job %s rows disappeared mid-processing; abandoning.", job.id)
                job_was_removed = True
                break
            _publish(job)

        if job_was_removed:
            return

        job.current_video_title = None
        files = storage.list_files(job.id)
        if files:
            zip_name = sanitize_filename(
                job.playlist.title if job.playlist else "playlist", fallback="playlist"
            )
            zip_path = await asyncio.to_thread(storage.create_zip, job.id, files, zip_name)
            job.zip_filename = zip_path.name
            job.total_size_bytes = storage.total_size(job.id)
            job.status = JobStatus.COMPLETED
        else:
            job.status = JobStatus.FAILED
            job.error_message = "All videos in this job failed to convert."

        job.completed_at = datetime.now(timezone.utc)
        job.expires_at = job.completed_at + timedelta(hours=settings.file_retention_hours)
        db.commit()
        log_event(
            logger, 20, "job_completed", job_id=job.id, status=job.status.value,
            completed=job.completed_videos, failed=job.failed_videos,
        )
        _publish(job)
    finally:
        db.close()


async def process_job_with_timeout(job_id: str) -> None:
    settings = get_settings()
    try:
        await asyncio.wait_for(process_job(job_id), timeout=settings.job_timeout_seconds)
    except asyncio.TimeoutError:
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).one_or_none()
            if job and job.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.status = JobStatus.FAILED
                job.error_message = "Job exceeded the maximum processing time and was stopped."
                job.completed_at = datetime.now(timezone.utc)
                job.expires_at = job.completed_at + timedelta(hours=settings.file_retention_hours)
                db.commit()
                log_event(logger, 40, "job_timeout", job_id=job_id)
                _publish(job)
        finally:
            db.close()
