import pytest

from app.utils.errors import InvalidURLError
from app.utils.validators import extract_playlist_id, validate_playlist_url


class TestExtractPlaylistId:
    def test_extracts_valid_id(self):
        url = "https://www.youtube.com/playlist?list=PLabc123XYZ_-9"
        assert extract_playlist_id(url) == "PLabc123XYZ_-9"

    def test_returns_none_without_list_param(self):
        assert extract_playlist_id("https://www.youtube.com/watch?v=abc123") is None

    def test_rejects_malicious_id_characters(self):
        url = "https://www.youtube.com/playlist?list=../../etc/passwd"
        assert extract_playlist_id(url) is None


class TestValidatePlaylistUrl:
    def test_accepts_valid_playlist_url(self):
        result = validate_playlist_url("https://www.youtube.com/playlist?list=PLabc123XYZ_-9defghi")
        assert result == "https://www.youtube.com/playlist?list=PLabc123XYZ_-9defghi"

    def test_accepts_watch_url_with_list_param(self):
        result = validate_playlist_url(
            "https://www.youtube.com/watch?v=abc&list=PLabc123XYZ_-9defghi"
        )
        assert "PLabc123XYZ_-9defghi" in result

    def test_preserves_seed_video_for_radio_mix_playlists(self):
        """RD (Radio/Mix) playlists 404 from YouTube via the bare
        /playlist?list= form and only resolve via /watch?v=...&list=RD... —
        the seed video id must survive normalization for these."""
        result = validate_playlist_url(
            "https://www.youtube.com/watch?v=wrSCeh7XMI0&list=RDoIAs1l14n34&index=2"
        )
        assert result == "https://www.youtube.com/watch?v=wrSCeh7XMI0&list=RDoIAs1l14n34"

    def test_drops_invalid_video_id(self):
        """A malformed v= value shouldn't propagate into the outbound
        yt-dlp call — falls back to the bare playlist form instead."""
        result = validate_playlist_url(
            "https://www.youtube.com/watch?v=<script>&list=PLabc123XYZ_-9defghi"
        )
        assert result == "https://www.youtube.com/playlist?list=PLabc123XYZ_-9defghi"

    def test_rejects_empty_url(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("")

    def test_rejects_non_youtube_host(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("https://evil.example.com/playlist?list=PLabc123XYZ_-9defghi")

    def test_rejects_host_confusion_attack(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("https://www.youtube.com.evil.example/playlist?list=PLabc123XYZ_-9defghi")

    def test_rejects_ip_literal_host(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("https://127.0.0.1/playlist?list=PLabc123XYZ_-9defghi")

    def test_rejects_private_ip_literal(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("http://169.254.169.254/playlist?list=PLabc123XYZ_-9defghi")

    def test_rejects_non_http_scheme(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("javascript:alert(1)")

    def test_rejects_file_scheme(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("file:///etc/passwd")

    def test_rejects_missing_playlist_id(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("https://www.youtube.com/watch?v=abc123")

    def test_rejects_overly_long_url(self):
        with pytest.raises(InvalidURLError):
            validate_playlist_url("https://www.youtube.com/playlist?list=" + "A" * 3000)

    def test_strips_whitespace(self):
        result = validate_playlist_url("  https://www.youtube.com/playlist?list=PLabc123XYZ_-9defghi  ")
        assert result.startswith("https://www.youtube.com/playlist?list=")
