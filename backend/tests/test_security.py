from pathlib import Path

import pytest

from app.utils.security import safe_join, sanitize_filename, sanitize_metadata_text


class TestSanitizeFilename:
    def test_strips_path_separators(self):
        assert "/" not in sanitize_filename("a/b/c")
        assert "\\" not in sanitize_filename("a\\b\\c")

    def test_strips_illegal_windows_characters(self):
        result = sanitize_filename('song<>:"|?*name')
        for ch in '<>:"|?*':
            assert ch not in result

    def test_handles_path_traversal_attempt(self):
        result = sanitize_filename("../../../etc/passwd")
        assert "/" not in result and ".." not in result.replace("..", "")  # no separators survive

    def test_returns_fallback_for_empty_input(self):
        assert sanitize_filename("", fallback="track") == "track"

    def test_returns_fallback_for_only_illegal_chars(self):
        assert sanitize_filename('///???', fallback="track") == "track"

    def test_truncates_long_names(self):
        result = sanitize_filename("A" * 500)
        assert len(result) <= 150

    def test_handles_reserved_windows_names(self):
        assert sanitize_filename("CON") != "CON"

    def test_preserves_reasonable_title(self):
        assert sanitize_filename("My Song (Official Video)") == "My Song (Official Video)"


class TestSanitizeMetadataText:
    def test_strips_control_characters(self):
        result = sanitize_metadata_text("Hello\x00World\x1f")
        assert "\x00" not in result and "\x1f" not in result

    def test_truncates_to_max_length(self):
        result = sanitize_metadata_text("A" * 1000, max_length=100)
        assert len(result) == 100

    def test_handles_none(self):
        assert sanitize_metadata_text(None) == ""


class TestSafeJoin:
    def test_joins_valid_relative_path(self, tmp_path: Path):
        result = safe_join(tmp_path, "sub", "file.txt")
        assert str(result).startswith(str(tmp_path))

    def test_rejects_traversal_outside_root(self, tmp_path: Path):
        with pytest.raises(ValueError):
            safe_join(tmp_path, "..", "..", "etc", "passwd")

    def test_rejects_absolute_path_escape(self, tmp_path: Path):
        with pytest.raises(ValueError):
            safe_join(tmp_path, "../../../../../../etc/passwd")
