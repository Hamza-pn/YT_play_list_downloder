VALID_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLtestplaylist000001"


def test_analyze_valid_playlist_returns_metadata(client, fake_media_service):
    resp = client.post("/api/playlist/analyze", json={"url": VALID_PLAYLIST_URL})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Test Playlist"
    assert body["data"]["video_count"] == 2
    assert len(body["data"]["videos"]) == 2
    assert body["data"]["videos"][0]["external_id"] == "vidAAAAAAAA"


def test_analyze_sets_session_cookie(client, fake_media_service):
    resp = client.post("/api/playlist/analyze", json={"url": VALID_PLAYLIST_URL})
    assert "ytad_session" in resp.cookies


def test_analyze_rejects_invalid_url(client):
    resp = client.post("/api/playlist/analyze", json={"url": "not-a-url"})
    assert resp.status_code == 422
    assert resp.json()["success"] is False


def test_analyze_rejects_non_youtube_url(client):
    resp = client.post("/api/playlist/analyze", json={"url": "https://vimeo.com/playlist?list=x"})
    assert resp.status_code == 422


def test_analyze_rejects_missing_url_field(client):
    resp = client.post("/api/playlist/analyze", json={})
    assert resp.status_code == 422


def test_analyze_rejects_empty_body(client):
    resp = client.post("/api/playlist/analyze", json={"url": ""})
    assert resp.status_code == 422
