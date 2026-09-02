from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

ALLOWED_FORMATS = {"mp3", "m4a", "wav"}
ALLOWED_MP3_QUALITIES = {128, 192, 256, 320}


class DownloadCreateRequest(BaseModel):
    playlist_url: str = Field(..., min_length=1, max_length=2048)
    # This is a generous absolute safety ceiling only (prevents an absurd
    # payload), not the real business limit — that's MAX_PLAYLIST_VIDEOS,
    # enforced dynamically against Settings in job_service.create_download_job
    # so it stays in sync with the configured value instead of a second
    # hardcoded number drifting out of sync with it.
    video_ids: list[str] = Field(..., min_length=1, max_length=1000)
    audio_format: str = Field(default="mp3")
    quality_kbps: int | None = Field(default=192)

    @field_validator("audio_format")
    @classmethod
    def check_format(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ALLOWED_FORMATS:
            raise ValueError(f"audio_format must be one of {sorted(ALLOWED_FORMATS)}")
        return v

    @field_validator("quality_kbps")
    @classmethod
    def check_quality(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v not in ALLOWED_MP3_QUALITIES:
            raise ValueError(f"quality_kbps must be one of {sorted(ALLOWED_MP3_QUALITIES)}")
        return v

    @field_validator("video_ids")
    @classmethod
    def dedupe_ids(cls, v: list[str]) -> list[str]:
        seen = list(dict.fromkeys(v))
        for vid in seen:
            if not vid or len(vid) > 64:
                raise ValueError("Invalid video id in selection.")
        return seen


class VideoProgressOut(BaseModel):
    id: str
    external_id: str
    title: str
    status: str
    progress_percent: int
    error_message: str | None = None


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    audio_format: str
    quality_kbps: int | None
    total_videos: int
    completed_videos: int
    failed_videos: int
    current_video_title: str | None
    error_message: str | None
    total_size_bytes: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime | None


class JobProgressEvent(BaseModel):
    job_id: str
    status: str
    total_videos: int
    completed_videos: int
    failed_videos: int
    overall_percent: int
    current_video_title: str | None = None
    videos: list[VideoProgressOut] = []
    estimated_seconds_remaining: int | None = None


class FileOut(BaseModel):
    id: str
    filename: str
    audio_format: str
    quality_kbps: int | None
    size_bytes: int


class JobFilesOut(BaseModel):
    job_id: str
    status: str
    files: list[FileOut]
    total_size_bytes: int
    expires_at: datetime | None
