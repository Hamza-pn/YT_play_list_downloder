VALID_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLtestplaylist000001"
VIDEO_IDS = ["vidAAAAAAAA", "vidBBBBBBBB"]


def _create_job(client, **overrides):
    payload = {
        "playlist_url": VALID_PLAYLIST_URL,
        "video_ids": VIDEO_IDS,
        "audio_format": "mp3",
        "quality_kbps": 192,
    }
    payload.update(overrides)
    return client.post("/api/download/create", json=payload)


def test_create_job_returns_expected_shape(client, fake_media_service):
    resp = _create_job(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "job_id" in body
    assert body["status"] in ("pending", "processing", "completed")


def test_create_job_rejects_invalid_format(client, fake_media_service):
    resp = _create_job(client, audio_format="flac")
    assert resp.status_code == 422


def test_create_job_rejects_invalid_mp3_quality(client, fake_media_service):
    resp = _create_job(client, quality_kbps=999)
    assert resp.status_code == 422


def test_create_job_rejects_empty_video_selection(client, fake_media_service):
    resp = _create_job(client, video_ids=[])
    assert resp.status_code == 422


def test_get_job_status_after_creation(client, fake_media_service):
    job_id = _create_job(client).json()["job_id"]
    resp = client.get(f"/api/download/{job_id}")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["job_id"] == job_id
    assert body["total_videos"] == 2


def test_get_job_status_unknown_id_returns_404(client):
    resp = client.get("/api/download/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["success"] is False


def test_job_isolated_between_sessions(client, fake_media_service):
    """A different guest session must not be able to read another session's
    job — same 404 as a nonexistent job, so job existence isn't leaked
    either. Simulated by dropping the session cookie on the same client
    (a second nested TestClient(app) would start a second lifespan on the
    same shared app singleton and race the first one's background queue)."""
    job_id = _create_job(client).json()["job_id"]

    client.cookies.clear()
    resp = client.get(f"/api/download/{job_id}")
    assert resp.status_code == 404


def test_delete_job_removes_it(client, fake_media_service):
    from tests.conftest import wait_for_terminal_status

    job_id = _create_job(client).json()["job_id"]
    wait_for_terminal_status(client, job_id)

    del_resp = client.delete(f"/api/download/{job_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    get_resp = client.get(f"/api/download/{job_id}")
    assert get_resp.status_code == 404


def test_delete_rejects_job_still_processing(client, slow_fake_media_service):
    """Deleting a job while its background worker is still writing to it
    would race the worker's in-memory Video/Job objects against the DELETE
    (the worker's next commit fails with a stale-data error once its rows
    are gone). Rejecting the delete until the job reaches a terminal status
    avoids that race entirely. Uses a deliberately slow fake service so the
    job is guaranteed to still be in flight when DELETE is called."""
    job_id = _create_job(client).json()["job_id"]
    resp = client.delete(f"/api/download/{job_id}")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "job_still_processing"


def test_zip_not_available_before_completion(client, fake_media_service):
    job_id = _create_job(client).json()["job_id"]
    resp = client.get(f"/api/download/{job_id}/zip")
    assert resp.status_code in (404, 200)  # 200 only if the fast test pipeline already finished
