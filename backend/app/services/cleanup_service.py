"""Temporary file / job retention cleanup.

Run periodically by the scheduled task in app.main (Phase 1: asyncio loop;
Phase 2: a dedicated Celery beat worker calling the same functions).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.models.base import ensure_aware
from app.models.job import Job, JobStatus
from app.services.storage.base import StorageBackend
from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)

_TERMINAL_STATUSES = (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED)
_ACTIVE_STATUSES = (JobStatus.PENDING, JobStatus.ANALYZING, JobStatus.PROCESSING)


def cleanup_expired_jobs(db: Session, storage: StorageBackend) -> int:
    """Delete files + DB rows for jobs whose retention window has passed."""
    now = datetime.now(timezone.utc)
    candidates = db.query(Job).filter(Job.status.in_(_TERMINAL_STATUSES), Job.expires_at.is_not(None)).all()
    expired = [j for j in candidates if ensure_aware(j.expires_at) < now]
    for job in expired:
        storage.delete_job(job.id)
        log_event(logger, 20, "job_cleanup", job_id=job.id, status=job.status.value)
        db.delete(job)
    if expired:
        db.commit()
    return len(expired)


def cleanup_stale_processing_jobs(db: Session, settings: Settings) -> int:
    """Fail jobs that have been PROCESSING far longer than JOB_TIMEOUT_SECONDS
    (e.g. the worker crashed mid-job) so they don't hang forever."""
    now = datetime.now(timezone.utc)
    stale = db.query(Job).filter(Job.status == JobStatus.PROCESSING, Job.started_at.is_not(None)).all()
    count = 0
    for job in stale:
        elapsed = (now - ensure_aware(job.started_at)).total_seconds()
        if elapsed > settings.job_timeout_seconds:
            job.status = JobStatus.FAILED
            job.error_message = "Job timed out during processing."
            job.completed_at = now
            job.expires_at = now
            count += 1
            log_event(logger, 30, "job_timeout", job_id=job.id, elapsed_seconds=int(elapsed))
    if count:
        db.commit()
    return count


def reset_orphaned_active_jobs_on_startup(db: Session, settings: Settings) -> int:
    """Phase 1 uses a purely in-process job queue — any job still in
    PENDING/ANALYZING/PROCESSING when the process starts is guaranteed to
    be orphaned (its worker task no longer exists; nothing survives a
    restart in this architecture). Left alone, such a job blocks its
    owning session's concurrent-job limit indefinitely and confuses users
    who see "you already have a conversion in progress" for a job that
    will never move again.

    Any partial output (tracks that finished converting before the
    restart) is left on disk and stays downloadable via the normal
    retention window — only the job's status is corrected here.
    """
    now = datetime.now(timezone.utc)
    orphaned = db.query(Job).filter(Job.status.in_(_ACTIVE_STATUSES)).all()
    for job in orphaned:
        previous_status = job.status.value
        job.status = JobStatus.FAILED
        job.error_message = (
            "This conversion was interrupted by a server restart before it could finish. "
            "Any tracks that completed beforehand are still available below — "
            "start a new conversion for the rest."
        )
        job.completed_at = now
        job.expires_at = now + timedelta(hours=settings.file_retention_hours)
        log_event(logger, 30, "job_orphaned_on_startup", job_id=job.id, previous_status=previous_status)
    if orphaned:
        db.commit()
    return len(orphaned)


def cleanup_orphaned_storage(db: Session, storage: StorageBackend) -> int:
    """Remove on-disk job directories that have no corresponding DB row
    (e.g. left behind by a crash between file creation and commit)."""
    known_ids = {job_id for (job_id,) in db.query(Job.id).all()}
    removed = 0
    for job_id in storage.list_all_job_ids():
        if job_id not in known_ids:
            storage.delete_job(job_id)
            removed += 1
            log_event(logger, 20, "orphan_storage_cleanup", job_id=job_id)
    return removed


def cleanup_abandoned_pending_jobs(db: Session, storage: StorageBackend, max_age_hours: int = 2) -> int:
    """Cancel jobs stuck in PENDING (never picked up by a worker) past a
    sanity window, e.g. after a backend restart dropped the in-memory queue."""
    now = datetime.now(timezone.utc)
    pending = db.query(Job).filter(Job.status == JobStatus.PENDING).all()
    count = 0
    for job in pending:
        age_hours = (now - ensure_aware(job.created_at)).total_seconds() / 3600
        if age_hours > max_age_hours:
            job.status = JobStatus.CANCELLED
            job.error_message = "Job was abandoned and automatically cancelled."
            job.completed_at = now
            job.expires_at = now
            storage.delete_job(job.id)
            count += 1
    if count:
        db.commit()
    return count
