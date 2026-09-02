from app.services.media_retrieval.base import (
    MediaRetrievalService,
    PlaylistInfo,
    RetrievedAudio,
    VideoInfo,
)
from app.services.media_retrieval.ytdlp_service import YtDlpService

__all__ = [
    "MediaRetrievalService",
    "PlaylistInfo",
    "VideoInfo",
    "RetrievedAudio",
    "YtDlpService",
]


def get_media_retrieval_service() -> MediaRetrievalService:
    """Factory — the single place that decides which implementation backs
    the MediaRetrievalService interface. Swap here to change providers."""
    return YtDlpService()
