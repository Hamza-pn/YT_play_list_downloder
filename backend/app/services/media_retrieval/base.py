"""Interface for retrieving public playlist/video data and audio streams.

This is the ONLY seam through which the rest of the application talks to
YouTube. Keeping it as an abstract interface means the concrete
implementation (currently yt-dlp) can be replaced without touching the API
layer, job orchestration, or worker code.

Implementations MUST:
  - only ever access publicly available data (no auth-cookie injection, no
    bypassing age/region/subscriber gates, no DRM circumvention)
  - raise the appropriate app.utils.errors.AppError subclass on failure
    instead of leaking a provider-specific exception upward
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoInfo:
    external_id: str
    title: str
    channel_name: str | None
    thumbnail_url: str | None
    duration_seconds: int
    position: int
    available: bool = True


@dataclass
class PlaylistInfo:
    external_id: str
    title: str
    channel_name: str | None
    thumbnail_url: str | None
    source_url: str
    videos: list[VideoInfo] = field(default_factory=list)


@dataclass
class RetrievedAudio:
    file_path: Path
    source_codec: str
    source_ext: str
    bitrate_kbps: int | None
    title: str
    channel_name: str | None
    thumbnail_path: Path | None
    duration_seconds: int
    upload_year: int | None = None


ProgressCallback = Callable[[float], None]


class MediaRetrievalService(ABC):
    @abstractmethod
    def get_playlist_info(self, playlist_url: str, *, max_videos: int) -> PlaylistInfo:
        """Fetch playlist + video metadata only (no media download)."""
        raise NotImplementedError

    @abstractmethod
    def download_audio(
        self,
        video_id: str,
        dest_dir: Path,
        *,
        max_file_size_bytes: int,
        timeout_seconds: int,
        progress_callback: ProgressCallback | None = None,
    ) -> RetrievedAudio:
        """Download the best available audio stream for one video into
        dest_dir, returning its path and basic probe info."""
        raise NotImplementedError
