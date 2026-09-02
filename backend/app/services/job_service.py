"""Orchestrates playlist analysis and job/video record creation.

Keeps API routes thin: routes only handle HTTP concerns (auth cookie,
status codes) and delegate all business logic here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.models.base import ensure_aware
from app.models.job import AudioFormat, Job, JobStatus
from app.models.playlist import Playlist
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.schemas.download import DownloadCreateRequest, JobProgressEvent, JobStatusOut, VideoProgressOut
from app.schemas.playlist import PlaylistOut, VideoOut
from app.services.media_retrieval import get_media_retrieval_service
from app.services.media_retrieval.base import PlaylistInfo
from app.services.session_service import clamp_quality_for_user
from app.utils.errors import JobNotFoundError, PlaylistTooLargeError
from app.utils.validators import validate_playlist_url


def analyze_playlist(raw_url: str, *, max_videos: int) -> PlaylistInfo:
    validated_url = validate_playlist_url(raw_url)
    service = get_media_retrieval_service()
    return service.get_playlist_info(validated_url, max_videos=max_videos)


def playlist_info_to_schema(info: PlaylistInfo) -> PlaylistOut:
    return PlaylistOut(
        external_id=info.external_id,
        title=info.title,
        channel_name=info.channel_name,
        thumbnail_url=info.thumbnail_url,
        video_count=len(info.videos),
        source_url=info.source_url,
        videos=[
            VideoOut(
                external_id=v.external_id,
                title=v.title,
                channel_name=v.channel_name,
                thumbnail_url=v.thumbnail_url,
                duration_seconds=v.duration_seconds,
                position=v.position,
                available=v.available,
            )
            for v in info.videos
        ],
    )


def _get_or_create_playlist(db: Session, info: PlaylistInfo) -> Playlist:
    playlist = db.query(Playlist).filter(Playlist.external_id == info.external_id).one_or_none()
    if playlist is None:
        playlist = Playlist(
            source_url=info.source_url,
            external_id=info.external_id,
            title=info.title,
            channel_name=info.channel_name,
            thumbnail_url=info.thumbnail_url,
            video_count=len(info.videos),
        )
        db.add(playlist)
        db.flush()
    return playlist


def create_download_job(
    db: Session,
    user: User,
    playlist_info: PlaylistInfo,
    req: DownloadCreateRequest,
    settings: Settings,
) -> Job:
    if len(req.video_ids) > settings.max_playlist_videos:
        raise PlaylistTooLargeError(
            f"You can select at most {settings.max_playlist_videos} videos per job."
        )

    available_by_id = {v.external_id: v for v in playlist_info.videos if v.available}
    selected = [available_by_id[vid] for vid in req.video_ids if vid in available_by_id]
    if not selected:
        raise PlaylistTooLargeError("None of the selected videos are available to download.")

    playlist = _get_or_create_playlist(db, playlist_info)
    quality = clamp_quality_for_user(user, req.quality_kbps) if req.audio_format == "mp3" else None

    job = Job(
        user_id=user.id,
        playlist_id=playlist.id,
        status=JobStatus.PENDING,
        audio_format=AudioFormat(req.audio_format),
        quality_kbps=quality,
        total_videos=len(selected),
    )
    db.add(job)
    db.flush()

    for v in selected:
        db.add(
            Video(
                job_id=job.id,
                external_id=v.external_id,
                title=v.title,
                channel_name=v.channel_name,
                thumbnail_url=v.thumbnail_url,
                duration_seconds=v.duration_seconds,
                position=v.position,
                status=VideoStatus.WAITING,
            )
        )

    db.commit()
    db.refresh(job)
    return job


def get_job_for_user(db: Session, job_id: str, user: User) -> Job:
    job = db.query(Job).filter(Job.id == job_id).one_or_none()
    if job is None or job.user_id != user.id:
        raise JobNotFoundError("Job not found.")
    return job


def job_to_status(job: Job) -> JobStatusOut:
    return JobStatusOut(
        job_id=job.id,
        status=job.status.value,
        audio_format=job.audio_format.value,
        quality_kbps=job.quality_kbps,
        total_videos=job.total_videos,
        completed_videos=job.completed_videos,
        failed_videos=job.failed_videos,
        current_video_title=job.current_video_title,
        error_message=job.error_message,
        total_size_bytes=job.total_size_bytes,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        expires_at=job.expires_at,
    )


def job_to_progress_event(job: Job) -> JobProgressEvent:
    processed = job.completed_videos + job.failed_videos
    overall_percent = int((processed / job.total_videos) * 100) if job.total_videos else 0

    eta = None
    if job.started_at and processed > 0 and processed < job.total_videos:
        elapsed = (datetime.now(timezone.utc) - ensure_aware(job.started_at)).total_seconds()
        per_video = elapsed / processed
        eta = int(per_video * (job.total_videos - processed))

    return JobProgressEvent(
        job_id=job.id,
        status=job.status.value,
        total_videos=job.total_videos,
        completed_videos=job.completed_videos,
        failed_videos=job.failed_videos,
        overall_percent=overall_percent,
        current_video_title=job.current_video_title,
        estimated_seconds_remaining=eta,
        videos=[
            VideoProgressOut(
                id=v.id,
                external_id=v.external_id,
                title=v.title,
                status=v.status.value,
                progress_percent=v.progress_percent,
                error_message=v.error_message,
            )
            for v in sorted(job.videos, key=lambda x: x.position)
        ],
    )
