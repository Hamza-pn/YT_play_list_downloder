"""End-to-end test of the full pipeline: analyze -> create job -> background
worker (download stub -> real ffmpeg convert -> real mutagen metadata) ->
files -> zip -> delete. No network access — the media retrieval layer is
faked, but audio conversion and tagging are real.
"""
import time

VALID_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLtestplaylist000001"
VIDEO_IDS = ["vidAAAAAAAA", "vidBBBBBBBB"]


def _wait_for_terminal_status(client, job_id, timeout=30):
    deadline = time.time() + timeout
    terminal = {"completed", "failed", "cancelled", "expired"}
    last = None
    while time.time() < deadline:
        resp = client.get(f"/api/download/{job_id}")
        last = resp.json()["data"]
        if last["status"] in terminal:
            return last
        time.sleep(0.25)
    raise AssertionError(f"Job did not reach a terminal status in time: {last}")


def test_full_playlist_to_zip_workflow(client, fake_media_service):
    analyze_resp = client.post("/api/playlist/analyze", json={"url": VALID_PLAYLIST_URL})
    assert analyze_resp.status_code == 200
    playlist = analyze_resp.json()["data"]
    assert playlist["video_count"] == 2

    create_resp = client.post(
        "/api/download/create",
        json={
            "playlist_url": VALID_PLAYLIST_URL,
            "video_ids": [v["external_id"] for v in playlist["videos"]],
            "audio_format": "mp3",
            "quality_kbps": 128,
        },
    )
    assert create_resp.status_code == 200
    job_id = create_resp.json()["job_id"]

    final_status = _wait_for_terminal_status(client, job_id)
    assert final_status["status"] == "completed"
    assert final_status["completed_videos"] == 2
    assert final_status["failed_videos"] == 0
    assert final_status["total_size_bytes"] > 0

    files_resp = client.get(f"/api/download/{job_id}/files")
    assert files_resp.status_code == 200
    files = files_resp.json()["data"]["files"]
    assert len(files) == 2
    for f in files:
        assert f["audio_format"] == "mp3"
        assert f["size_bytes"] > 0

    file_resp = client.get(f"/api/download/{job_id}/file/{files[0]['id']}")
    assert file_resp.status_code == 200
    assert file_resp.headers["content-type"] == "audio/mpeg"
    assert len(file_resp.content) > 0

    zip_resp = client.get(f"/api/download/{job_id}/zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"
    assert len(zip_resp.content) > 0

    delete_resp = client.delete(f"/api/download/{job_id}")
    assert delete_resp.status_code == 200
    assert client.get(f"/api/download/{job_id}").status_code == 404


def test_m4a_transcodes_from_opus_source(client, fake_media_service):
    """The fake source is opus; requesting m4a must transcode (not stream
    copy) — exercises the real ffmpeg re-encode branch end to end."""
    create_resp = client.post(
        "/api/download/create",
        json={"playlist_url": VALID_PLAYLIST_URL, "video_ids": VIDEO_IDS[:1], "audio_format": "m4a"},
    )
    job_id = create_resp.json()["job_id"]
    final_status = _wait_for_terminal_status(client, job_id)
    assert final_status["status"] == "completed"
    assert final_status["completed_videos"] == 1


def test_wav_output(client, fake_media_service):
    create_resp = client.post(
        "/api/download/create",
        json={"playlist_url": VALID_PLAYLIST_URL, "video_ids": VIDEO_IDS[:1], "audio_format": "wav"},
    )
    job_id = create_resp.json()["job_id"]
    final_status = _wait_for_terminal_status(client, job_id)
    assert final_status["status"] == "completed"
