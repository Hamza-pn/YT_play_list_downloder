from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PlaylistAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.strip()


class VideoOut(BaseModel):
    external_id: str
    title: str
    channel_name: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int
    position: int
    available: bool = True


class PlaylistOut(BaseModel):
    external_id: str
    title: str
    channel_name: str | None = None
    thumbnail_url: str | None = None
    video_count: int
    videos: list[VideoOut]
    source_url: str
