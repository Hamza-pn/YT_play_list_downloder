from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

# Set at conftest import time (pytest imports conftest.py before collecting
# any test module), so Settings' lru_cache never gets primed with real
# development values by an accidental top-level `from app.main import app`
# in a test file.
_tmp_dir = Path(tempfile.mkdtemp(prefix="ytad_test_"))
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_tmp_dir / 'test.db'}"
os.environ["STORAGE_LOCAL_PATH"] = str(_tmp_dir / "storage")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["MAX_REQUESTS_PER_MINUTE"] = "1000"
os.environ["MAX_CONCURRENT_JOBS_PER_SESSION"] = "5"


@pytest.fixture(autouse=True)
def _reset_job_queue_singleton():
    """The in-process job queue binds its asyncio.Queue lazily to whichever
    event loop is running. TestClient spins up a fresh loop per test, so the
    singleton must be rebuilt each time or queue operations raise
    'Future attached to a different loop'."""
    import app.workers.queue as queue_module

    queue_module.job_queue = None
    yield
    queue_module.job_queue = None


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.db.session import init_db
    from app.main import app

    init_db()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal, init_db

    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def sample_audio_source(tmp_path_factory) -> Path:
    """A tiny real (silent) audio file generated once via ffmpeg, standing
    in for a real yt-dlp download so tests never touch the network."""
    from app.services.audio_service import FFMPEG_BIN

    ffmpeg = FFMPEG_BIN if (Path(FFMPEG_BIN).is_absolute() and Path(FFMPEG_BIN).exists()) else shutil.which(FFMPEG_BIN)
    if ffmpeg is None:
        pytest.skip("ffmpeg is not installed; skipping tests that require real audio conversion.")

    directory = tmp_path_factory.mktemp("sample_audio")
    source = directory / "sample.opus"
    subprocess.run(
        [
            ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "1", "-c:a", "libopus", str(source),
        ],
        check=True, capture_output=True, timeout=30,
    )
    return source


def wait_for_terminal_status(client, job_id, timeout=30):
    """Poll GET /api/download/{job_id} until the job reaches a terminal
    status, returning the final status payload."""
    import time

    deadline = time.time() + timeout
    terminal = {"completed", "failed", "cancelled", "expired"}
    last = None
    while time.time() < deadline:
        resp = client.get(f"/api/download/{job_id}")
        last = resp.json()["data"]
        if last["status"] in terminal:
            return last
        time.sleep(0.1)
    raise AssertionError(f"Job did not reach a terminal status in time: {last}")


@pytest.fixture
def fake_media_service(monkeypatch, sample_audio_source):
    """Replaces the real yt-dlp-backed service everywhere it's referenced
    (job_service for analyze/create, conversion_worker for the background
    pipeline) with a fake that returns fixed metadata and a local sample
    audio file, so tests exercise the real ffmpeg/mutagen pipeline without
    any network access."""
    from app.services.media_retrieval.base import (
        MediaRetrievalService,
        PlaylistInfo,
        RetrievedAudio,
        VideoInfo,
    )

    class FakeMediaService(MediaRetrievalService):
        def get_playlist_info(self, url: str, *, max_videos: int) -> PlaylistInfo:
            return PlaylistInfo(
                external_id="PLtestplaylist000001",
                title="Test Playlist",
                channel_name="Test Channel",
                thumbnail_url=None,
                source_url=url,
                videos=[
                    VideoInfo(
                        external_id="vidAAAAAAAA", title="Song One", channel_name="Test Channel",
                        thumbnail_url=None, duration_seconds=180, position=0, available=True,
                    ),
                    VideoInfo(
                        external_id="vidBBBBBBBB", title="Song Two", channel_name="Test Channel",
                        thumbnail_url=None, duration_seconds=200, position=1, available=True,
                    ),
                ],
            )

        def get_video_info(self, video_url: str) -> PlaylistInfo:
            return PlaylistInfo(
                external_id="vidSINGLE01",
                title="Single Song",
                channel_name="Test Channel",
                thumbnail_url=None,
                source_url=video_url,
                videos=[
                    VideoInfo(
                        external_id="vidSINGLE01", title="Single Song", channel_name="Test Channel",
                        thumbnail_url=None, duration_seconds=150, position=0, available=True,
                    ),
                ],
            )

        def download_audio(self, video_id, dest_dir, *, max_file_size_bytes, timeout_seconds, progress_callback=None):
            dest = Path(dest_dir) / f"{video_id}.opus"
            shutil.copyfile(sample_audio_source, dest)
            return RetrievedAudio(
                file_path=dest,
                source_codec="opus",
                source_ext="opus",
                bitrate_kbps=64,
                title=f"Fake Title {video_id}",
                channel_name="Test Channel",
                thumbnail_path=None,
                duration_seconds=1,
                upload_year=2024,
            )

    instance = FakeMediaService()
    monkeypatch.setattr("app.services.job_service.get_media_retrieval_service", lambda: instance)
    monkeypatch.setattr("app.workers.conversion_worker.get_media_retrieval_service", lambda: instance)
    return instance


@pytest.fixture
def slow_fake_media_service(fake_media_service):
    """Same as fake_media_service, but download_audio blocks briefly so a
    job is reliably still PROCESSING right after creation — for tests that
    need to observe an in-flight job deterministically rather than racing
    the (normally near-instant) fake pipeline."""
    import time

    original_download_audio = fake_media_service.download_audio

    def slow_download_audio(*args, **kwargs):
        time.sleep(1.5)
        return original_download_audio(*args, **kwargs)

    fake_media_service.download_audio = slow_download_audio
    return fake_media_service
