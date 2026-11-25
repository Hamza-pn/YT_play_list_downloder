"""YouTube source URL validation and SSRF protection.

A "source" is either a playlist or a single video (including Shorts, live
replays and youtu.be short links). Both kinds flow through the same
download pipeline — a single video is simply a one-item collection.

The only outbound network calls this service ever makes are through yt-dlp
against YouTube's own hosts. This module is the single choke point that
decides whether a user-supplied URL is even allowed to reach that layer —
nothing else in the codebase should call yt-dlp with an unvalidated URL.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs, urlparse

from app.utils.errors import InvalidURLError

# Only these exact hosts are permitted. Deliberately no wildcard subdomain
# matching beyond this explicit list, to prevent host-confusion tricks like
# "youtube.com.evil.example".
ALLOWED_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    # youtu.be is YouTube's own short-link domain: youtu.be/<video id>.
    "youtu.be",
    "www.youtu.be",
}

_PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,64}$")
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,12}$")

# Path prefixes that carry a bare video id as the next path segment:
#   /shorts/<id>  /live/<id>  /embed/<id>  /v/<id>
# On youtu.be the id is the first segment with no prefix at all.
_VIDEO_PATH_PREFIXES = {"shorts", "live", "embed", "v"}
_SHORT_LINK_HOSTS = {"youtu.be", "www.youtu.be"}


class SourceKind(str, Enum):
    """Which of the two supported source shapes a URL refers to."""

    PLAYLIST = "playlist"
    VIDEO = "video"


@dataclass(frozen=True)
class ValidatedSource:
    """The outcome of validating a user-supplied URL.

    `url` is the normalized, safe-to-dispatch form — the only URL any
    caller should hand to the media retrieval layer.
    """

    kind: SourceKind
    url: str
    playlist_id: str | None = None
    video_id: str | None = None


def _reject_if_ip_literal(host: str) -> None:
    """Block raw IP hosts outright (nobody has a legitimate YouTube URL
    pointing at an IP), which also blocks the common SSRF trick of encoding
    an internal address as the hostname."""
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return
    raise InvalidURLError("URL host must be a YouTube domain, not an IP address.")


def _resolves_to_public_address(host: str) -> bool:
    """Defense in depth: resolve the hostname and reject anything that
    points at a private/loopback/link-local/reserved network, even if the
    hostname itself passed the allow-list (guards against DNS rebinding)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr.split("%")[0])
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def _parse_and_check_host(raw_url: str, *, what: str) -> tuple[str, str]:
    """Shared gate for every accepted URL shape: scheme, host allow-list
    and IP-literal rejection. Returns (trimmed URL, host).

    The DNS resolution check is deliberately NOT done here — it is the one
    step that touches the network, so callers run it via
    _require_public_host only after the cheap syntactic checks (including
    id extraction) have passed.

    `what` only shapes the error message ("playlist" vs "video or
    playlist") so the user is told what the endpoint actually accepts.
    """
    if not raw_url or not raw_url.strip():
        raise InvalidURLError(f"A YouTube {what} URL is required.")

    raw_url = raw_url.strip()
    if len(raw_url) > 2048:
        raise InvalidURLError("URL is too long.")

    try:
        parsed = urlparse(raw_url)
    except ValueError as exc:
        raise InvalidURLError("URL could not be parsed.") from exc

    if parsed.scheme not in ("http", "https"):
        raise InvalidURLError("URL must use http or https.")

    host = (parsed.hostname or "").lower()
    if not host:
        raise InvalidURLError("URL is missing a host.")

    _reject_if_ip_literal(host)

    if host not in ALLOWED_HOSTS:
        raise InvalidURLError(f"Only YouTube {what} URLs are supported.")

    return raw_url, host


def _require_public_host(host: str) -> None:
    if not _resolves_to_public_address(host):
        raise InvalidURLError("URL host could not be verified as a public YouTube address.")


def validate_source_url(raw_url: str) -> ValidatedSource:
    """Validate any supported YouTube URL — playlist, single video, Short,
    live replay or youtu.be short link — and return its normalized form.

    A `list=` parameter wins over a video id: a watch URL that carries both
    is the playlist form the user pasted from, so it is treated as a
    playlist (the existing behaviour). Only when no playlist id is present
    does the URL resolve to a single video.

    Raises InvalidURLError with a human-readable message on any failure.
    """
    raw_url, host = _parse_and_check_host(raw_url, what="video or playlist")

    playlist_id = extract_playlist_id(raw_url)
    if playlist_id:
        _require_public_host(host)
        return ValidatedSource(
            kind=SourceKind.PLAYLIST,
            url=_normalize_playlist_url(raw_url, playlist_id),
            playlist_id=playlist_id,
            video_id=extract_video_id(raw_url),
        )

    video_id = extract_video_id(raw_url)
    if video_id:
        _require_public_host(host)
        # noplaylist is set on the outbound call, but normalizing to the
        # bare watch form means no stray list=/index=/start_radio= params
        # can pull extra videos in regardless.
        return ValidatedSource(
            kind=SourceKind.VIDEO,
            url=f"https://www.youtube.com/watch?v={video_id}",
            video_id=video_id,
        )

    raise InvalidURLError(
        "URL does not contain a valid YouTube video or playlist ID. Paste a video, "
        "Shorts or playlist link."
    )


def validate_playlist_url(raw_url: str) -> str:
    """Validate a user-supplied playlist URL. Returns the normalized URL.

    Playlist-only entry point, kept for callers that must reject single
    videos. Use validate_source_url for the general case.
    """
    raw_url, host = _parse_and_check_host(raw_url, what="playlist")

    playlist_id = extract_playlist_id(raw_url)
    if not playlist_id:
        raise InvalidURLError("URL does not contain a valid playlist ID.")

    _require_public_host(host)

    return _normalize_playlist_url(raw_url, playlist_id)


def _normalize_playlist_url(raw_url: str, playlist_id: str) -> str:
    # "Radio"/Mix playlists (list starts with "RD") are generated from a
    # seed video and YouTube rejects the bare /playlist?list= form for them
    # ("This playlist type is unviewable") — they only resolve via the
    # watch page with both v= and list= present. Regular playlists (PL/UU/
    # FL/OLAK5uy_/etc.) work fine either way, so preserving v= when present
    # is safe for all playlist types, not just mixes.
    video_id = extract_video_id(raw_url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}&list={playlist_id}"
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def extract_playlist_id(raw_url: str) -> str | None:
    parsed = urlparse(raw_url)
    query = parse_qs(parsed.query)
    list_values = query.get("list")
    if not list_values:
        return None
    candidate = list_values[0]
    if not _PLAYLIST_ID_RE.match(candidate):
        return None
    return candidate


def extract_video_id(raw_url: str) -> str | None:
    """Pull the video id out of any supported URL shape.

    Covers the `v=` query parameter (watch/music URLs), the path forms
    /shorts/<id>, /live/<id>, /embed/<id> and /v/<id>, and youtu.be/<id>
    short links. Returns None if no syntactically valid id is present.
    """
    parsed = urlparse(raw_url)

    video_values = parse_qs(parsed.query).get("v")
    if video_values and _VIDEO_ID_RE.match(video_values[0]):
        return video_values[0]

    segments = [s for s in (parsed.path or "").split("/") if s]
    host = (parsed.hostname or "").lower()

    if host in _SHORT_LINK_HOSTS:
        # youtu.be/<id> — the id is the whole path, no prefix.
        if segments and _VIDEO_ID_RE.match(segments[0]):
            return segments[0]
        return None

    if len(segments) >= 2 and segments[0].lower() in _VIDEO_PATH_PREFIXES:
        if _VIDEO_ID_RE.match(segments[1]):
            return segments[1]

    return None
