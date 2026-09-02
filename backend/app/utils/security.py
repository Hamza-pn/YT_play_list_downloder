"""Filename sanitization and path-traversal protection helpers.

Every path derived from user- or remote-supplied strings (video titles,
channel names, playlist names) MUST go through sanitize_filename before
touching the filesystem, and every resolved path MUST be verified with
safe_join before being opened/written.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
MAX_FILENAME_LENGTH = 150


def sanitize_filename(name: str, *, fallback: str = "untitled") -> str:
    """Strip control/path characters and normalize a string for safe use as
    a filename component (not a full path)."""
    if not name:
        return fallback

    normalized = unicodedata.normalize("NFKC", name)
    cleaned = _ILLEGAL_CHARS.sub("", normalized)
    cleaned = cleaned.strip(" .")
    cleaned = re.sub(r"\s+", " ", cleaned)

    if not cleaned:
        return fallback

    if cleaned.upper().split(".")[0] in _RESERVED_WINDOWS_NAMES:
        cleaned = f"_{cleaned}"

    if len(cleaned) > MAX_FILENAME_LENGTH:
        cleaned = cleaned[:MAX_FILENAME_LENGTH].rstrip()

    return cleaned or fallback


def sanitize_metadata_text(value: str | None, *, max_length: int = 512) -> str:
    """Sanitize a string destined for embedded audio metadata (not a path).

    Removes control characters and caps length; unlike sanitize_filename this
    permits slashes/colons since it is never used as a path component.
    """
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", value)
    cleaned = "".join(ch for ch in normalized if ch.isprintable())
    cleaned = cleaned.strip()
    return cleaned[:max_length]


def safe_join(root: Path, *parts: str) -> Path:
    """Join path components under `root`, raising ValueError if the resolved
    path would escape `root` (path traversal protection)."""
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"Path traversal detected: {parts!r} escapes {root_resolved}")
    return candidate
