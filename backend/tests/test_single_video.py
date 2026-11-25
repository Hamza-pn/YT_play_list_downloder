"""Single video / Shorts support.

The pipeline treats one video as a one-item playlist, so these tests cover
the two things that are genuinely new: URL recognition (every shape a user
might paste) and the analyze -> job -> download flow for a lone video.
"""
import time

import pytest

from app.utils.errors import InvalidURLError
from app.utils.validators import SourceKind, extract_video_id, validate_source_url

VIDEO_ID = "dQw4w9WgXcQ"
SINGLE_VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


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


class TestExtractVideoId:
    def test_watch_query_param(self):
        assert extract_video_id(f"https://www.youtube.com/watch?v={VIDEO_ID}") == VIDEO_ID

    def test_shorts_path(self):
        assert extract_video_id(f"https://www.youtube.com/shorts/{VIDEO_ID}") == VIDEO_ID

    def test_live_path(self):
        assert extract_video_id(f"https://www.youtube.com/live/{VIDEO_ID}") == VIDEO_ID

    def test_embed_path(self):
        assert extract_video_id(f"https://www.youtube.com/embed/{VIDEO_ID}") == VIDEO_ID

    def test_short_link_host(self):
        assert extract_video_id(f"https://youtu.be/{VIDEO_ID}") == VIDEO_ID

    def test_short_link_with_timestamp(self):
        assert extract_video_id(f"https://youtu.be/{VIDEO_ID}?t=42") == VIDEO_ID

    def test_rejects_traversal_in_shorts_path(self):
        assert extract_video_id("https://www.youtube.com/shorts/../../etc/passwd") is None

    def test_returns_none_for_bare_playlist_url(self):
        assert extract_video_id("https://www.youtube.com/playlist?list=PLabc123XYZ_-9") is None

    def test_returns_none_for_channel_url(self):
        assert extract_video_id("https://www.youtube.com/@somechannel") is None


class TestValidateSourceUrl:
    @pytest.mark.parametrize(
        "raw",
        [
            f"https://www.youtube.com/watch?v={VIDEO_ID}",
            f"https://m.youtube.com/watch?v={VIDEO_ID}",
            f"https://music.youtube.com/watch?v={VIDEO_ID}",
            f"https://www.youtube.com/shorts/{VIDEO_ID}",
            f"https://youtube.com/shorts/{VIDEO_ID}",
            f"https://www.youtube.com/live/{VIDEO_ID}",
            f"https://youtu.be/{VIDEO_ID}",
            f"  https://youtu.be/{VIDEO_ID}  ",
        ],
    )
    def test_accepts_every_single_video_shape(self, raw):
        source = validate_source_url(raw)
        assert source.kind is SourceKind.VIDEO
        assert source.video_id == VIDEO_ID
        assert source.url == SINGLE_VIDEO_URL

    def test_strips_tracking_and_timestamp_params(self):
        source = validate_source_url(
            f"https://www.youtube.com/watch?v={VIDEO_ID}&t=30s&si=abc&feature=share"
        )
        assert source.url == SINGLE_VIDEO_URL

    def test_playlist_url_still_resolves_as_playlist(self):
        source = validate_source_url("https://www.youtube.com/playlist?list=PLabc123XYZ_-9defghi")
        assert source.kind is SourceKind.PLAYLIST
        assert source.url == "https://www.youtube.com/playlist?list=PLabc123XYZ_-9defghi"

    def test_list_param_wins_over_video_id(self):
        """A watch URL carrying both is the playlist form YouTube hands out
        when you open a video from inside a playlist — keep treating it as
        a playlist so the user still gets the whole thing."""
        source = validate_source_url(
            f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PLabc123XYZ_-9defghi"
        )
        assert source.kind is SourceKind.PLAYLIST
        assert source.url == (
            f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PLabc123XYZ_-9defghi"
        )

    def test_rejects_non_youtube_host(self):
        with pytest.raises(InvalidURLError):
            validate_source_url(f"https://evil.example.com/watch?v={VIDEO_ID}")

    def test_rejects_host_confusion_attack(self):
        with pytest.raises(InvalidURLError):
            validate_source_url(f"https://youtu.be.evil.example/{VIDEO_ID}")

    def test_rejects_ip_literal_host(self):
        with pytest.raises(InvalidURLError):
            validate_source_url(f"https://127.0.0.1/watch?v={VIDEO_ID}")

    def test_rejects_non_http_scheme(self):
        with pytest.raises(InvalidURLError):
            validate_source_url("javascript:alert(1)")

    def test_rejects_channel_url_with_no_video_or_playlist(self):
        with pytest.raises(InvalidURLError):
            validate_source_url("https://www.youtube.com/@somechannel")

    def test_rejects_empty_url(self):
        with pytest.raises(InvalidURLError):
            validate_source_url("")

    def test_rejects_overly_long_url(self):
        with pytest.raises(InvalidURLError):
            validate_source_url("https://www.youtube.com/watch?v=" + "A" * 3000)


class TestSingleVideoApi:
    def test_analyze_single_video_returns_one_item(self, client, fake_media_service):
        resp = client.post("/api/playlist/analyze", json={"url": SINGLE_VIDEO_URL})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["video_count"] == 1
        assert len(data["videos"]) == 1
        assert data["videos"][0]["external_id"] == "vidSINGLE01"

    def test_analyze_shorts_url_returns_one_item(self, client, fake_media_service):
        resp = client.post(
            "/api/playlist/analyze", json={"url": f"https://www.youtube.com/shorts/{VIDEO_ID}"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["video_count"] == 1

    def test_analyze_short_link_returns_one_item(self, client, fake_media_service):
        resp = client.post(
            "/api/playlist/analyze", json={"url": f"https://youtu.be/{VIDEO_ID}"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["video_count"] == 1

    def test_analyze_rejects_channel_url(self, client):
        resp = client.post("/api/playlist/analyze", json={"url": "https://www.youtube.com/@chan"})
        assert resp.status_code == 422
        assert resp.json()["success"] is False

    def test_single_video_downloads_end_to_end(self, client, fake_media_service):
        """The whole point of the feature: a lone video goes through the
        same analyze -> create -> convert -> file pipeline as a playlist."""
        analyze = client.post("/api/playlist/analyze", json={"url": SINGLE_VIDEO_URL})
        assert analyze.status_code == 200
        source_url = analyze.json()["data"]["source_url"]
        video_ids = [v["external_id"] for v in analyze.json()["data"]["videos"]]

        create = client.post(
            "/api/download/create",
            json={
                "playlist_url": source_url,
                "video_ids": video_ids,
                "audio_format": "mp3",
                "quality_kbps": 192,
            },
        )
        assert create.status_code == 200, create.text
        job_id = create.json()["job_id"]

        final = _wait_for_terminal_status(client, job_id)
        assert final["status"] == "completed", final
        assert final["total_videos"] == 1
        assert final["completed_videos"] == 1

        files = client.get(f"/api/download/{job_id}/files")
        assert files.status_code == 200
        assert len(files.json()["data"]["files"]) == 1
