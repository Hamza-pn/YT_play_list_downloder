from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.schemas.common import APIResponse
from app.schemas.playlist import PlaylistAnalyzeRequest, PlaylistOut
from app.services import job_service
from app.utils.rate_limit import action_rate_limit, limiter

router = APIRouter(prefix="/api/playlist", tags=["playlist"])


@router.post("/analyze", response_model=APIResponse[PlaylistOut])
@limiter.limit(action_rate_limit)
async def analyze_playlist(
    request: Request,
    payload: PlaylistAnalyzeRequest,
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
) -> APIResponse[PlaylistOut]:
    info = await run_in_threadpool(
        job_service.analyze_source, payload.url, max_videos=settings.max_playlist_videos
    )
    return APIResponse(data=job_service.playlist_info_to_schema(info))
