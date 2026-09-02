from __future__ import annotations

import shutil

from fastapi import APIRouter

from app.config.settings import get_settings
from app.services.audio_service import FFMPEG_BIN, FFPROBE_BIN

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    return {
        "success": True,
        "status": "ok",
        "ffmpeg_available": shutil.which(FFMPEG_BIN) is not None,
        "ffprobe_available": shutil.which(FFPROBE_BIN) is not None,
        "environment": settings.environment,
    }
