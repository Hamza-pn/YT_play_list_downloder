from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class DownloadedFile(Base, TimestampMixin):
    __tablename__ = "downloaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    video_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("videos.id"), nullable=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_format: Mapped[str] = mapped_column(String(10), nullable=False)
    quality_kbps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)

    job: Mapped["Job"] = relationship(back_populates="files")
    video: Mapped[Optional["Video"]] = relationship(back_populates="file")
