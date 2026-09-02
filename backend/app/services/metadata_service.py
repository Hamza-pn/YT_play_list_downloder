"""Embeds sanitized metadata (title/artist/album/year/track/cover art) into
converted audio files using mutagen. Best-effort: a metadata failure is
logged and swallowed rather than failing an otherwise-successful conversion.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mutagen.id3 import APIC, TALB, TCON, TDRC, TIT2, TPE1, TRCK, ID3, ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.wave import WAVE

from app.services.audio_service import convert_image_to_jpeg
from app.utils.logging import get_logger
from app.utils.security import sanitize_metadata_text

logger = get_logger(__name__)

_JPEG_EXTS = {".jpg", ".jpeg"}


@dataclass
class TrackMetadata:
    title: str
    artist: str
    album: str
    track_number: int
    year: int | None = None
    thumbnail_path: Path | None = None


def _prepare_artwork(thumbnail_path: Path | None) -> tuple[bytes, str] | None:
    if not thumbnail_path or not thumbnail_path.exists():
        return None

    path_to_read = thumbnail_path
    if thumbnail_path.suffix.lower() not in _JPEG_EXTS:
        jpeg_path = thumbnail_path.with_suffix(".embed.jpg")
        if convert_image_to_jpeg(thumbnail_path, jpeg_path):
            path_to_read = jpeg_path
        else:
            return None

    try:
        data = path_to_read.read_bytes()
    except OSError:
        return None
    finally:
        if path_to_read != thumbnail_path:
            path_to_read.unlink(missing_ok=True)

    if len(data) > 10 * 1024 * 1024:  # sanity cap, never trust remote size claims
        return None
    return data, "image/jpeg"


def _write_id3(path: Path, meta: TrackMetadata, artwork: tuple[bytes, str] | None) -> None:
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TRCK")
    tags.delall("TDRC")
    tags.delall("TCON")
    tags.delall("APIC")

    tags.add(TIT2(encoding=3, text=meta.title))
    tags.add(TPE1(encoding=3, text=meta.artist))
    tags.add(TALB(encoding=3, text=meta.album))
    tags.add(TRCK(encoding=3, text=str(meta.track_number)))
    tags.add(TCON(encoding=3, text="Downloaded Audio"))
    if meta.year:
        tags.add(TDRC(encoding=3, text=str(meta.year)))
    if artwork:
        data, mime = artwork
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))

    tags.save(path)


def _write_mp4(path: Path, meta: TrackMetadata, artwork: tuple[bytes, str] | None) -> None:
    mp4 = MP4(path)
    mp4["\xa9nam"] = [meta.title]
    mp4["\xa9ART"] = [meta.artist]
    mp4["\xa9alb"] = [meta.album]
    mp4["trkn"] = [(meta.track_number, 0)]
    if meta.year:
        mp4["\xa9day"] = [str(meta.year)]
    if artwork:
        data, _mime = artwork
        mp4["covr"] = [MP4Cover(data, imageformat=MP4Cover.FORMAT_JPEG)]
    mp4.save()


def _write_wav(path: Path, meta: TrackMetadata, artwork: tuple[bytes, str] | None) -> None:
    wav = WAVE(path)
    if wav.tags is None:
        wav.add_tags()
    tags = wav.tags
    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TRCK")
    tags.delall("TDRC")
    tags.delall("APIC")

    tags.add(TIT2(encoding=3, text=meta.title))
    tags.add(TPE1(encoding=3, text=meta.artist))
    tags.add(TALB(encoding=3, text=meta.album))
    tags.add(TRCK(encoding=3, text=str(meta.track_number)))
    if meta.year:
        tags.add(TDRC(encoding=3, text=str(meta.year)))
    if artwork:
        data, mime = artwork
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
    wav.save()


def embed_metadata(path: Path, audio_format: str, meta: TrackMetadata) -> None:
    sanitized = TrackMetadata(
        title=sanitize_metadata_text(meta.title, max_length=200) or "Untitled",
        artist=sanitize_metadata_text(meta.artist, max_length=200) or "Unknown Artist",
        album=sanitize_metadata_text(meta.album, max_length=200) or "Unknown Playlist",
        track_number=meta.track_number,
        year=meta.year,
        thumbnail_path=meta.thumbnail_path,
    )
    artwork = _prepare_artwork(sanitized.thumbnail_path)

    try:
        fmt = audio_format.lower()
        if fmt == "mp3":
            _write_id3(path, sanitized, artwork)
        elif fmt == "m4a":
            _write_mp4(path, sanitized, artwork)
        elif fmt == "wav":
            _write_wav(path, sanitized, artwork)
    except Exception:  # noqa: BLE001 — metadata is best-effort, never fail the job over it
        logger.warning("Failed to embed metadata for %s", path.name, exc_info=True)
