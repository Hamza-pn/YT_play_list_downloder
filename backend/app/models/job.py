from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AudioFormat(str, enum.Enum):
    MP3 = "mp3"
    M4A = "m4a"
    WAV = "wav"


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    playlist_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("playlists.id"), nullable=True)

    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    audio_format: Mapped[AudioFormat] = mapped_column(Enum(AudioFormat), default=AudioFormat.MP3, nullable=False)
    quality_kbps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    total_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    current_video_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    zip_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="jobs")
    playlist: Mapped[Optional["Playlist"]] = relationship(back_populates="jobs")
    videos: Mapped[list["Video"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    files: Mapped[list["DownloadedFile"]] = relationship(back_populates="job", cascade="all, delete-orphan")
