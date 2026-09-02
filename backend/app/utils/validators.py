"""YouTube playlist URL validation and SSRF protection.

The only outbound network calls this service ever makes are through yt-dlp
against YouTube's own hosts. This module is the single choke point that
decides whether a user-supplied URL is even allowed to reach that layer —
nothing else in the codebase should call yt-dlp with an unvalidated URL.
"""
from __future__ import annotations

import ipaddress
import re
import socket
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
}

_PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,64}$")
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,12}$")


def _reject_if_ip_literal(host: str) -> None:
    """Block raw IP hosts outright (nobody has a legitimate playlist URL
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


def validate_playlist_url(raw_url: str) -> str:
    """Validate a user-supplied playlist URL. Returns the normalized URL.

    Raises InvalidURLError with a human-readable message on any failure.
    """
    if not raw_url or not raw_url.strip():
        raise InvalidURLError("Playlist URL is required.")

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
        raise InvalidURLError("Only youtube.com playlist URLs are supported.")

    playlist_id = extract_playlist_id(raw_url)
    if not playlist_id:
        raise InvalidURLError("URL does not contain a valid playlist ID.")

    if not _resolves_to_public_address(host):
        raise InvalidURLError("URL host could not be verified as a public YouTube address.")

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
    parsed = urlparse(raw_url)
    query = parse_qs(parsed.query)
    video_values = query.get("v")
    if not video_values:
        return None
    candidate = video_values[0]
    if not _VIDEO_ID_RE.match(candidate):
        return None
    return candidate
