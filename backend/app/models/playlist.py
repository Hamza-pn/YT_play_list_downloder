from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Playlist(Base, TimestampMixin):
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    channel_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    video_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    jobs: Mapped[list["Job"]] = relationship(back_populates="playlist")
