from datetime import datetime, timedelta, timezone

from app.config.settings import get_settings
from app.models.job import Job, JobStatus
from app.models.user import User
from app.services.cleanup_service import (
    cleanup_abandoned_pending_jobs,
    cleanup_expired_jobs,
    cleanup_orphaned_storage,
    cleanup_stale_processing_jobs,
    reset_orphaned_active_jobs_on_startup,
)
from app.services.storage.local_storage import LocalStorage


def _make_user(db, suffix: str = "") -> User:
    import secrets

    user = User(session_id=f"test-session-{suffix}-{secrets.token_hex(4)}")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_cleanup_expired_jobs_deletes_job_and_files(db_session):
    user = _make_user(db_session, "expired")
    storage = LocalStorage()
    now = datetime.now(timezone.utc)

    job = Job(user_id=user.id, status=JobStatus.COMPLETED, total_videos=1, expires_at=now - timedelta(hours=1))
    db_session.add(job)
    db_session.commit()

    job_dir = storage.job_dir(job.id)
    (job_dir / "track.mp3").write_bytes(b"fake audio data")

    removed = cleanup_expired_jobs(db_session, storage)

    assert removed == 1
    assert db_session.query(Job).filter(Job.id == job.id).one_or_none() is None
    assert not job_dir.exists()


def test_cleanup_expired_jobs_leaves_unexpired_jobs(db_session):
    user = _make_user(db_session, "notexpired")
    storage = LocalStorage()
    now = datetime.now(timezone.utc)

    job = Job(user_id=user.id, status=JobStatus.COMPLETED, total_videos=1, expires_at=now + timedelta(hours=5))
    db_session.add(job)
    db_session.commit()

    removed = cleanup_expired_jobs(db_session, storage)

    assert removed == 0
    assert db_session.query(Job).filter(Job.id == job.id).one_or_none() is not None


def test_cleanup_stale_processing_jobs_marks_failed(db_session):
    user = _make_user(db_session, "stale")
    settings = get_settings()
    now = datetime.now(timezone.utc)

    job = Job(
        user_id=user.id, status=JobStatus.PROCESSING, total_videos=1,
        started_at=now - timedelta(seconds=settings.job_timeout_seconds + 60),
    )
    db_session.add(job)
    db_session.commit()

    count = cleanup_stale_processing_jobs(db_session, settings)
    db_session.refresh(job)

    assert count == 1
    assert job.status == JobStatus.FAILED


def test_cleanup_orphaned_storage_removes_untracked_dirs(db_session):
    storage = LocalStorage()
    orphan_dir = storage.job_dir("orphan-job-id-not-in-db")
    (orphan_dir / "leftover.mp3").write_bytes(b"data")

    removed = cleanup_orphaned_storage(db_session, storage)

    assert removed >= 1
    assert not orphan_dir.exists()


def test_cleanup_abandoned_pending_jobs(db_session):
    user = _make_user(db_session, "abandoned")
    storage = LocalStorage()
    now = datetime.now(timezone.utc)

    job = Job(user_id=user.id, status=JobStatus.PENDING, total_videos=1)
    db_session.add(job)
    db_session.commit()
    job.created_at = now - timedelta(hours=3)
    db_session.commit()

    count = cleanup_abandoned_pending_jobs(db_session, storage, max_age_hours=2)
    db_session.refresh(job)

    assert count == 1


def test_reset_orphaned_active_jobs_on_startup(db_session):
    """Regression test for a real incident: a job stuck in PROCESSING after
    a backend restart (Phase 1's job queue is purely in-process, so nothing
    survives a restart) permanently blocked its session's concurrent-job
    limit — the user saw "you already have a conversion in progress" for a
    job that would never move again. Startup must reset any job left in an
    active status back to a terminal one."""
    user = _make_user(db_session, "orphaned")
    settings = get_settings()
    now = datetime.now(timezone.utc)

    processing_job = Job(
        user_id=user.id, status=JobStatus.PROCESSING, total_videos=55,
        completed_videos=21, started_at=now - timedelta(minutes=5),
    )
    pending_job = Job(user_id=user.id, status=JobStatus.PENDING, total_videos=3)
    completed_job = Job(user_id=user.id, status=JobStatus.COMPLETED, total_videos=1, completed_videos=1)
    db_session.add_all([processing_job, pending_job, completed_job])
    db_session.commit()

    count = reset_orphaned_active_jobs_on_startup(db_session, settings)

    db_session.refresh(processing_job)
    db_session.refresh(pending_job)
    db_session.refresh(completed_job)

    assert count == 2
    assert processing_job.status == JobStatus.FAILED
    assert processing_job.completed_videos == 21  # partial progress preserved
    assert "interrupted" in processing_job.error_message.lower()
    assert processing_job.expires_at is not None
    assert pending_job.status == JobStatus.FAILED
    assert completed_job.status == JobStatus.COMPLETED  # untouched — already terminal
