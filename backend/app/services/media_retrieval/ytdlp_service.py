"""yt-dlp backed implementation of MediaRetrievalService.

Only accesses data yt-dlp can reach as an unauthenticated, anonymous client
against YouTube's public endpoints — no cookies, no login, no age/region
gate bypassing, no DRM circumvention. Private, members-only, and
age-restricted videos are surfaced as unavailable/permission-denied rather
than worked around.
"""
from __future__ import annotations

from pathlib import Path

import yt_dlp

from app.services.media_retrieval.base import (
    MediaRetrievalService,
    PlaylistInfo,
    ProgressCallback,
    RetrievedAudio,
    VideoInfo,
)
from app.utils.errors import (
    ContentUnavailableError,
    FileTooLargeError,
    PermissionDeniedError,
    PlaylistEmptyError,
    PlaylistNotFoundError,
    PlaylistTooLargeError,
    TimeoutErrorApp,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

_UNAVAILABLE_TITLES = {"[Private video]", "[Deleted video]", "[Unavailable]"}
_UNAVAILABLE_STATUSES = {"private", "needs_auth", "subscriber_only", "premium_only"}
_THUMB_EXTS = (".jpg", ".jpeg", ".webp", ".png")


def _pick_thumbnail(entry: dict) -> str | None:
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        return thumbs[-1].get("url")
    return entry.get("thumbnail")


def _is_available(entry: dict) -> bool:
    title = entry.get("title") or ""
    if title in _UNAVAILABLE_TITLES:
        return False
    availability = entry.get("availability")
    if availability in _UNAVAILABLE_STATUSES:
        return False
    return True


def _map_download_error(exc: Exception) -> Exception:
    msg = str(exc).lower()
    if "private video" in msg or "members-only" in msg or "sign in" in msg:
        return PermissionDeniedError(
            "This video is private, members-only, or otherwise restricted. "
            "You must have permission to access it."
        )
    if "does not exist" in msg or "not found" in msg:
        return PlaylistNotFoundError("The requested playlist or video could not be found.")
    if "max-filesize" in msg or "file is larger than max-filesize" in msg:
        return FileTooLargeError("This video's audio exceeds the maximum allowed file size.")
    if "timed out" in msg or "timeout" in msg:
        return TimeoutErrorApp("Timed out while retrieving media from YouTube.")
    return ContentUnavailableError("This video is unavailable or could not be retrieved.")


class YtDlpService(MediaRetrievalService):
    def get_playlist_info(self, playlist_url: str, *, max_videos: int) -> PlaylistInfo:
        ydl_opts = {
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ignoreerrors": True,
            "playlistend": max_videos + 1,
            "socket_timeout": 15,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            raise _map_download_error(exc) from exc

        if info is None:
            raise PlaylistNotFoundError("The requested playlist could not be found.")

        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise PlaylistEmptyError("This playlist has no available videos.")
        if len(entries) > max_videos:
            raise PlaylistTooLargeError(
                f"This playlist has more than {max_videos} videos. "
                f"Only playlists with up to {max_videos} videos are supported."
            )

        videos = [
            VideoInfo(
                external_id=entry.get("id", ""),
                title=entry.get("title") or "Untitled",
                channel_name=entry.get("channel") or entry.get("uploader"),
                thumbnail_url=_pick_thumbnail(entry),
                duration_seconds=int(entry.get("duration") or 0),
                position=idx,
                available=_is_available(entry),
            )
            for idx, entry in enumerate(entries)
        ]

        return PlaylistInfo(
            external_id=info.get("id", ""),
            title=info.get("title") or "Untitled Playlist",
            channel_name=info.get("channel") or info.get("uploader"),
            thumbnail_url=_pick_thumbnail(info),
            source_url=playlist_url,
            videos=videos,
        )

    def download_audio(
        self,
        video_id: str,
        dest_dir: Path,
        *,
        max_file_size_bytes: int,
        timeout_seconds: int,
        progress_callback: ProgressCallback | None = None,
    ) -> RetrievedAudio:
        url = f"https://www.youtube.com/watch?v={video_id}"
        outtmpl = str(dest_dir / f"{video_id}.%(ext)s")

        def hook(d: dict) -> None:
            if progress_callback and d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    progress_callback(min(99.0, downloaded / total * 100))

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "postprocessors": [],
            "max_filesize": max_file_size_bytes,
            "socket_timeout": 20,
            "retries": 3,
            "progress_hooks": [hook],
            "writethumbnail": True,
            "noprogress": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = Path(ydl.prepare_filename(info))
        except yt_dlp.utils.DownloadError as exc:
            raise _map_download_error(exc) from exc

        if not filepath.exists():
            raise ContentUnavailableError("Audio download did not produce a file.")

        thumbnail_path = None
        for ext in _THUMB_EXTS:
            candidate = filepath.with_suffix(ext)
            if candidate.exists():
                thumbnail_path = candidate
                break

        acodec = (info.get("acodec") or "").lower()
        if acodec.startswith("mp4a"):
            acodec = "aac"

        upload_date = info.get("upload_date")
        upload_year = int(upload_date[:4]) if upload_date and len(upload_date) >= 4 else None

        if progress_callback:
            progress_callback(100.0)

        return RetrievedAudio(
            file_path=filepath,
            source_codec=acodec or "unknown",
            source_ext=(info.get("ext") or filepath.suffix.lstrip(".")).lower(),
            bitrate_kbps=int(info["abr"]) if info.get("abr") else None,
            title=info.get("title") or "Untitled",
            channel_name=info.get("channel") or info.get("uploader"),
            thumbnail_path=thumbnail_path,
            duration_seconds=int(info.get("duration") or 0),
            upload_year=upload_year,
        )
