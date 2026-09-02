"""FFmpeg-backed audio conversion.

Security: every ffmpeg/ffprobe invocation uses an explicit argument list via
subprocess — never shell=True, never string-formatted commands. Paths are
expected to already be validated/sanitized by the caller (job_service /
storage layer) before reaching this module.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config.settings import get_settings
from app.utils.errors import ConversionFailedError, TimeoutErrorApp
from app.utils.logging import get_logger

logger = get_logger(__name__)

_settings = get_settings()
FFMPEG_BIN = _settings.ffmpeg_path or "ffmpeg"
FFPROBE_BIN = _settings.ffprobe_path or "ffprobe"

_ENCODERS = {
    "mp3": "libmp3lame",
    "m4a": "aac",
    "wav": "pcm_s16le",
}
DEFAULT_M4A_BITRATE_KBPS = 192


@dataclass
class AudioProbe:
    codec: str
    bitrate_kbps: int | None
    sample_rate: int | None
    channels: int | None


def probe_audio(path: Path) -> AudioProbe:
    cmd = [
        FFPROBE_BIN, "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,bit_rate,sample_rate,channels",
        "-of", "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    except FileNotFoundError as exc:
        raise ConversionFailedError("Audio processing is temporarily unavailable.") from exc
    except subprocess.TimeoutExpired as exc:
        raise TimeoutErrorApp("Timed out inspecting audio file.") from exc

    if result.returncode != 0:
        logger.warning("ffprobe failed: %s", result.stderr[-2000:])
        return AudioProbe(codec="unknown", bitrate_kbps=None, sample_rate=None, channels=None)

    try:
        data = json.loads(result.stdout)
        stream = (data.get("streams") or [{}])[0]
    except (json.JSONDecodeError, IndexError):
        return AudioProbe(codec="unknown", bitrate_kbps=None, sample_rate=None, channels=None)

    bit_rate = stream.get("bit_rate")
    return AudioProbe(
        codec=(stream.get("codec_name") or "unknown").lower(),
        bitrate_kbps=int(int(bit_rate) / 1000) if bit_rate else None,
        sample_rate=int(stream["sample_rate"]) if stream.get("sample_rate") else None,
        channels=stream.get("channels"),
    )


def _can_stream_copy(source_codec: str, target_format: str) -> bool:
    if target_format == "m4a" and source_codec == "aac":
        return True
    if target_format == "mp3" and source_codec == "mp3":
        return True
    return False


def convert_audio(
    src: Path,
    dest: Path,
    *,
    audio_format: str,
    quality_kbps: int | None,
    source_codec: str,
    timeout_seconds: int = 300,
) -> bool:
    """Convert src -> dest in audio_format. Returns True if a lossless
    stream copy was used (no re-encoding), False if ffmpeg transcoded."""
    audio_format = audio_format.lower()
    if audio_format not in _ENCODERS:
        raise ValueError(f"Unsupported audio_format: {audio_format}")

    argv = [FFMPEG_BIN, "-y", "-i", str(src), "-vn", "-map_metadata", "-1"]
    used_copy = _can_stream_copy(source_codec, audio_format)

    if used_copy:
        argv += ["-c:a", "copy"]
    elif audio_format == "mp3":
        bitrate = quality_kbps or 192
        argv += ["-c:a", _ENCODERS["mp3"], "-b:a", f"{bitrate}k", "-ar", "44100"]
    elif audio_format == "m4a":
        argv += ["-c:a", _ENCODERS["m4a"], "-b:a", f"{DEFAULT_M4A_BITRATE_KBPS}k"]
    else:  # wav
        argv += ["-c:a", _ENCODERS["wav"]]

    argv.append(str(dest))

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        logger.error("ffmpeg binary not found at %s", FFMPEG_BIN)
        raise ConversionFailedError("Audio processing is temporarily unavailable.") from exc
    except subprocess.TimeoutExpired as exc:
        raise TimeoutErrorApp("Audio conversion took too long and was stopped.") from exc

    if result.returncode != 0 or not dest.exists():
        stderr_tail = result.stderr.decode(errors="replace")[-2000:] if result.stderr else ""
        logger.error("ffmpeg conversion failed (code %s): %s", result.returncode, stderr_tail)
        raise ConversionFailedError(
            "This video's audio could not be converted. It may use an unsupported codec."
        )

    return used_copy


def convert_image_to_jpeg(src: Path, dest: Path, timeout_seconds: int = 30) -> bool:
    """Best-effort thumbnail normalization (e.g. webp -> jpeg) for embedding
    as cover art. Returns False (non-fatal) on any failure."""
    argv = [FFMPEG_BIN, "-y", "-i", str(src), "-frames:v", "1", str(dest)]
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout_seconds, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and dest.exists()
